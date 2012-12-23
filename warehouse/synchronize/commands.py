from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import eventlet

from progress.bar import ShadyBar

from warehouse import create_app, db, redis, script
from warehouse.exceptions import FailedSynchronization
from warehouse.packages import diff, store
from warehouse.synchronize.fetchers import PyPIFetcher


REDIS_SINCE_KEY = "warehouse:since"
REDIS_SYNC_LOCK_KEY = "warehouse:sync:lock:{project}"


eventlet.monkey_patch()


class DummyBar(object):
    def iter(self, iterable):
        for item in iterable:
            yield item


def synchronize_project(app, project, fetcher, force=False):
    with app.test_request_context():
        key = REDIS_SYNC_LOCK_KEY.format(project=project)

        with redis.lock(key, timeout=60 * 10):
            project = store.project(project)

            versions = fetcher.versions(project.name)

            for ver in versions:
                version = store.version(
                            project,
                            fetcher.release(project.name, ver),
                        )

                dists = fetcher.distributions(project.name, version.version)
                dists = list(dists)

                for dist in dists:
                    distribution = store.distribution(version, dist)

                    if distribution.hashes is None:
                        current_hash = None
                    else:
                        current_hash = distribution.hashes.get("md5")

                    # Check if the stored hash matches what the fetcher says
                    if (force or
                            distribution.hashes is None or
                            dist["md5_digest"] != current_hash):
                        # The fetcher has a different file
                        store.distribution_file(
                                distribution,
                                fetcher.file(dist["url"]),
                            )

                # Yank distributions that no longer exist in PyPI
                diff.distributions(version, [x["filename"] for x in dists])

            # Yank versions that no longer exist in PyPI
            diff.versions(project, versions)

            # Commit our changes
            db.session.commit()


def syncer(projects=None, since=None, fetcher=None, pool=None, progress=True,
        force=False, raise_exc=False):
    if pool is None:
        pool = eventlet.GreenPool(10)

    if fetcher is None:
        fetcher = PyPIFetcher()

    current = fetcher.current()

    # Sync the Classifiers
    for classifier in fetcher.classifiers():
        store.classifier(classifier)

    # Commit the classifiers
    db.session.commit()

    # Sync the Projects/Versions/Files
    if not projects:
        projects = fetcher.projects(since=since)

    if progress:
        bar = ShadyBar("Synchronizing", max=len(projects))
    else:
        bar = DummyBar()

    app = create_app()

    results = []

    with app.app_context():
        for project in bar.iter(projects):
            results.append(
                pool.spawn(synchronize_project, app, project, fetcher, force),
            )

    failed = False

    for result in results:
        # Wait for the result so that it will raise an exception if one
        #   occured
        try:
            result.wait()
        # Catch a general Exception here because we do not know what will
        #   be raised by the green thread.
        except Exception:  # pylint: disable=W0703
            failed = True

            # If we are re-raising exceptions then raise this one
            if raise_exc:
                raise

    if failed:
        # Raise a general Synchronization has failed exception. In general
        #   hiding the exception like this isn't very nice but it's difficult
        #   to "do the right thing" with green threads.
        raise FailedSynchronization

    # See if there have been any deletions
    if fetcher.deletions(since=since):
        # Grab all projects to do a diff against
        projects = fetcher.projects()

        # Yank no longer existing projects (and versions and files)
        diff.projects(projects)

        # Commit the deletion
        db.session.commit()

    return current


@script.option("--raise", action="store_true", dest="raise_exc", default=False)
@script.option("--no-store",
            action="store_false", dest="store_since", default=True)
@script.option("--full", action="store_true", dest="full", default=False)
@script.option("--since", type=int, default=None)
@script.option("--force-download", action="store_true", dest="force")
@script.option("--concurrency", dest="concurrency", type=int, default=10)
@script.option("--no-progress", action="store_false", dest="progress")
@script.option("projects", nargs="*", metavar="project")
def synchronize(projects=None, concurrency=10, progress=True, force=False,
        since=None, full=False, store_since=True, raise_exc=False):
    # This is a hack to normalize the incoming projects to unicode
    projects = [x.decode("utf-8") for x in projects]

    # Create the Pool that Synchronization will use
    pool = eventlet.GreenPool(concurrency)

    # Get our last run out of Redis if there was a last run
    if since is None and not full:
        since = int(redis.get(REDIS_SINCE_KEY))

    if full and not since is None:
        since = None

    # Run the actual Synchronization
    synced = syncer(projects,
                since=since,
                pool=pool,
                progress=progress,
                force=force,
                raise_exc=raise_exc,
            )

    # Save our synchronization time in redis
    if store_since:
        redis.set(REDIS_SINCE_KEY, synced)

    # Output the time we started the sync
    print "Synchronization completed at", synced

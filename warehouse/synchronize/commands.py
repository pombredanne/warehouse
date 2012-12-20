from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import eventlet

from progress.bar import ShadyBar

from warehouse import create_app, db, script
from warehouse.packages import diff, store
from warehouse.synchronize.fetchers import PyPIFetcher


eventlet.monkey_patch()


class DummyBar(object):
    def iter(self, iterable):
        for item in iterable:
            yield item


def synchronize_project(app, project, fetcher, force=False):
    with app.test_request_context():
        project = store.project(project)

        versions = fetcher.versions(project.name)

        for ver in versions:
            version = store.version(
                        project,
                        fetcher.release(project.name, ver),
                    )
            dists = list(fetcher.distributions(project.name, version.version))

            for dist in dists:
                distribution = store.distribution(version, dist)

                # Check if the stored hash matches what the fetcher says
                if (force or
                        distribution.hashes is None or
                        dist["md5_digest"] != distribution.hashes.get("md5")):
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
        force=False):
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

    with app.app_context():
        for project in bar.iter(projects):
            pool.spawn_n(synchronize_project, app, project, fetcher, force)

    # See if there have been any deletions
    if fetcher.deletions(since=since):
        # Grab all projects to do a diff against
        projects = fetcher.projects()

        # Yank no longer existing projects (and versions and files)
        diff.projects(projects)

        # Commit the deletion
        db.session.commit()

    return current


@script.option("--since", type=int, default=None)
@script.option("--force-download", action="store_true", dest="force")
@script.option("--concurrency", dest="concurrency", type=int, default=10)
@script.option("--no-progress", action="store_false", dest="progress")
@script.option("projects", nargs="*", metavar="project")
def synchronize(projects=None, concurrency=10, progress=True, force=False,
        since=None):
    # This is a hack to normalize the incoming projects to unicode
    projects = [x.decode("utf-8") for x in projects]

    # Create the Pool that Synchronization will use
    pool = eventlet.GreenPool(concurrency)

    # Run the actual Synchronization
    synced = syncer(projects,
                since=since,
                pool=pool,
                progress=progress,
                force=force
            )

    # Output the time we started the sync
    print "Synchronization completed at", synced

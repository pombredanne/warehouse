from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import eventlet

from progress.bar import ShadyBar

from warehouse import create_app, db, script
from warehouse.packages import store
from warehouse.packages.models import Project, Version, File
from warehouse.synchronize.fetchers import PyPIFetcher


eventlet.monkey_patch()


class DummyBar(object):
    def iter(self, iterable):
        for x in iterable:
            yield x


def synchronize_project(app, project, fetcher, force=False):
    with app.test_request_context():
        project = store.project(project)

        versions = fetcher.versions(project.name)

        for v in versions:
            version = store.version(project, fetcher.release(project.name, v))
            distributions = fetcher.distributions(project.name, version.version)

            for dist in distributions:
                distribution = store.distribution(project, version, dist)

                # Check if the stored hash matches what the fetcher says
                if (force or
                        distribution.hashes is None or
                        dist["md5_digest"] != distribution.hashes.get("md5")):
                    # The fetcher has a different file
                    store.distribution_file(project, version, distribution,
                                            fetcher.file(dist["url"]))

            # Get a list of filesnames
            filenames = [x["filename"] for x in distributions]

            # Find what files no longer exist in PyPI to yank them
            if filenames:
                # If there any files we use IN
                files_to_yank = File.query.filter(
                                    File.version == version,
                                    ~File.filename.in_(filenames),
                                )
            else:
                # If there are no filenames we can do a simpler query
                files_to_yank = File.query.filter(File.version == version)

            # Actually preform the yanking
            files_to_yank.update({"yanked": False}, synchronize_session=False)

        # Find what versions no longer exist in PyPI to yank them
        if versions:
            # If there are any versions we use IN
            versions_to_yank = Version.query.filter(
                                    Version.project == project,
                                    ~Version.version.in_(versions),
                                )
        else:
            # If there are no versions we can do a simpler query
            versions_to_yank = Version.query.filter(Version.project == project)

        # Actually preform the yanking
        versions_to_yank.update({"yanked": True}, synchronize_session=False)

        # Commit our changes
        db.session.commit()


def syncer(projects=None, fetcher=None, pool=None, progress=True, force=False):
    if pool is None:
        pool = eventlet.GreenPool(10)

    if fetcher is None:
        fetcher = PyPIFetcher()

    # Sync the Classifiers
    for classifier in fetcher.classifiers():
        store.classifier(classifier)

    # Commit the classifiers
    db.session.commit()

    # Sync the Projects/Versions/Files
    if not projects:
        # TODO(dstufft): Determine how to make this do the "since last sync"
        projects = fetcher.projects()

    if progress:
        bar = ShadyBar("Synchronizing", max=len(projects))
    else:
        bar = DummyBar()

    app = create_app()

    with app.app_context():
        for project in bar.iter(projects):
            pool.spawn_n(synchronize_project, app, project, fetcher, force)

    # Yank no longer existing projects (and versions and files)
    Project.query.filter(
                ~Project.name.in_(projects)
            ).update({"yanked": True}, synchronize_session=False)

    # Commit the deletion
    db.session.commit()


@script.option("--force-download", action="store_true", dest="force")
@script.option("--concurrency", dest="concurrency", type=int, default=10)
@script.option("--no-progress", action="store_false", dest="progress")
@script.option("projects", nargs="*", metavar="project")
def synchronize(projects=None, concurrency=10, progress=True, force=False):
    # This is a hack to normalize the incoming projects to unicode
    projects = [x.decode("utf-8") for x in projects]

    # Create the Pool that Synchronization will use
    pool = eventlet.GreenPool(concurrency)

    # Run the actual Synchronization
    syncer(projects, pool=pool, progress=progress, force=force)

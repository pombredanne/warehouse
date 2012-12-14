from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import eventlet

from progress.bar import ShadyBar

from warehouse import create_app, db, script
from warehouse.packages import store
from warehouse.synchronize.fetchers import PyPIFetcher


eventlet.monkey_patch()


class DummyBar(object):
    def iter(self, iterable):
        for x in iterable:
            yield x


def synchronize_project(app, project, fetcher):
    with app.test_request_context():
        project = store.project(project)

        for v in fetcher.versions(project.name):
            version = store.version(project, fetcher.release(project.name, v))

            for dist in fetcher.distributions(project.name, version.version):
                distribution = store.distribution(project, version, dist)

                # Check if the stored hash matches what the fetcher says
                if (distribution.hashes is None or
                        dist["md5_digest"] != distribution.hashes.get("md5")):
                    # The fetcher has a different file
                    # TODO(dstufft): Verify that this url is HTTPS
                    store.distribution_file(project, version, distribution,
                                            fetcher.file(dist["url"]))

        # Commit our changes
        db.session.commit()


def syncer(projects=None, fetcher=None, app=None, pool=None, progress=True):
    if pool is None:
        pool = eventlet.GreenPool(10)

    if app is None:
        app = create_app()

    if fetcher is None:
        fetcher = PyPIFetcher()

    if not projects:
        # TODO(dstufft): Determine how to make this do the "since last sync"
        projects = fetcher.projects()

    if progress:
        bar = ShadyBar("Synchronizing", max=len(projects))
    else:
        bar = DummyBar()

    with app.app_context():
        for project in bar.iter(projects):
            pool.spawn_n(synchronize_project, app, project, fetcher)


@script.option("--concurrency", dest="concurrency", type=int, default=10)
@script.option("--no-progress", action="store_false", dest="progress")
@script.option("projects", nargs="*", metavar="project")
def synchronize(projects=None, concurrency=10, progress=True):
    # This is a hack to normalize the incoming projects to unicode
    projects = [x.decode("utf-8") for x in projects]

    # Create the Pool that Synchronization will use
    pool = eventlet.GreenPool(concurrency)

    # Run the actual Synchronization
    syncer(projects, pool=pool, progress=progress)

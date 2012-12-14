from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import eventlet

from progress.bar import ShadyBar

from warehouse import create_app, db, script
from warehouse.packages import store
from warehouse.synchronize.fetchers import PyPIFetcher


eventlet.monkey_patch()


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


def syncer(projects=None, fetcher=None, app=None, pool=None):
    if pool is None:
        pool = eventlet.GreenPool(10)

    if app is None:
        app = create_app()

    if fetcher is None:
        fetcher = PyPIFetcher()

    if projects is None:
        # TODO(dstufft): Determine how to make this do the "since last sync"
        projects = fetcher.projects()

    with app.app_context():
        for project in ShadyBar("Syncing", max=len(projects)).iter(projects):
            pool.spawn_n(synchronize_project, app, project, fetcher)


@script.command
def synchronize():
    syncer()

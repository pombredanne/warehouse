from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

import eventlet

from flask.ext.script import (  # pylint: disable=E0611,F0401
                            Command, Group, Option)
from progress.bar import ShadyBar

from warehouse import create_app, db, redis, script
from warehouse import utils
from warehouse.exceptions import FailedSynchronization, SynchronizationTimeout
from warehouse.packages import diff, store
from warehouse.packages.models import FileType
from warehouse.synchronize.fetchers import PyPIFetcher


REDIS_SINCE_KEY = "warehouse:since"
REDIS_SYNC_LOCK_KEY = "warehouse:sync:lock:{project}"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

eventlet.monkey_patch()


class DummyBar(object):
    def iter(self, iterable):
        for item in iterable:
            yield item


def synchronize_project(app, project, fetcher, download=None):
    with app.test_request_context():
        key = REDIS_SYNC_LOCK_KEY.format(project=project)

        with redis.lock(key, timeout=60 * 10):
            logger.info("Synchronizing '%s' from pypi.python.org", project)

            project = store.project(project)
            versions = fetcher.versions(project.name)

            for ver in versions:
                logger.debug(
                    "Synchronizing version '%s' of '%s' from pypi.python.org",
                    ver,
                    project.name,
                )

                release = fetcher.release(project.name, ver)
                version = store.version(project, release)

                dists = fetcher.distributions(project.name, version.version)
                dists = list(dists)

                for dist in dists:
                    logger.debug(
                        "Synchronizing '%s' from version '%s' of '%s' "
                            "from pypi.python.org",
                        dist["filename"],
                        version.version,
                        project.name,
                    )

                    distribution = store.distribution(version, dist)

                    if distribution.hashes is None:
                        current_hashes = {}
                    else:
                        current_hashes = distribution.hashes

                    # Handle the True/False/None logic of download, and if
                    #   download is None check if our stored hash matches
                    #   the hash from PyPI
                    if download or (
                                download is None and
                                dist["md5_digest"] != current_hashes.get("md5")
                            ):
                        file_data = fetcher.file(dist["url"])
                        store.distribution_file(distribution, file_data)

                        if distribution.type == FileType.source:
                            store.setuptools_requires(
                                version,
                                distribution.filename,
                                file_data,
                            )

                # Yank distributions that no longer exist in PyPI
                logger.debug("Diffing distributions of '%s' version '%s'",
                        project.name,
                        version.version,
                    )
                diff.distributions(version, [x["filename"] for x in dists])

            # Yank versions that no longer exist in PyPI
            logger.debug("Diffing versions of '%s'", project.name)
            diff.versions(project, versions)

            # Commit our changes
            db.session.commit()


def syncer(projects=None, since=None, fetcher=None, pool=None, progress=True,
        download=None, raise_exc=False, timeout=None):
    if pool is None:
        pool = eventlet.GreenPool(10)
        logger.debug("Using concurrency of %s for GreenPool", pool.size)

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

    # Check if we have anything to sync before bothering to attempt to sync
    if projects:
        if progress:
            bar = ShadyBar("Synchronizing", max=len(projects))
        else:
            bar = DummyBar()

        app = create_app()

        results = []

        with app.app_context():
            if timeout is None:
                timeout = app.config["SYNCHRONIZATION_TIMEOUT"]

            with eventlet.Timeout(timeout, SynchronizationTimeout):
                for project in bar.iter(projects):
                    results.append(
                        pool.spawn(synchronize_project,
                                app,
                                project,
                                fetcher,
                                download,
                        ),
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
                logger.exception("An error has occured during synchronization")
                failed = True
                # If we are re-raising exceptions then raise this one
                if raise_exc:
                    raise

        if failed:
            # Raise a general Synchronization has failed exception. In general
            #   hiding the exception like this isn't very nice but it's
            #    difficult to "do the right thing" with green threads.
            raise FailedSynchronization

    # See if there have been any deletions
    if fetcher.deletions(since=since):
        logger.debug("Diffing all projects from pypi.python.org")

        # Grab all projects to do a diff against
        projects = fetcher.projects()

        # Yank no longer existing projects (and versions and files)
        diff.projects(projects)

        # Commit the deletion
        db.session.commit()

    return current


class Synchronize(Command):
    """
    Synchronizes Warehouse with PyPI.
    """

    # pylint: disable=W0232

    option_list = [
        Option("projects", nargs="*", help="list of projects to synchronize"),
        Option("--repeat-every",
            type=int,
            dest="repeat",
            default=False,
            help="repeat the synchronization with the selected options every "
                "REPEAT seconds",
        ),
        Option("--no-progress",
            action="store_false",
            dest="progress",
            help="do not display a progress bar",
        ),
        Option("--timeout",
            type=int,
            dest="timeout",
            default=None,
            help="timeout each individual project synchronization in TIMEOUT "
                "seconds",
        ),
        Option("--no-store",
            action="store_false",
            dest="store_since",
            default=True,
            help="do not store the synchronization time",
        ),
        Option("--raise",
            action="store_true",
            dest="raise_exc",
            default=False,
            help="raise an exception in project synchronization as it happens "
                "instead of a generic one at the end",
        ),
        Option("--concurrency",
            dest="concurrency",
            type=int,
            default=10,
            help="use CONCURRENCY eventlet threads at once",
        ),
        Group(
            Option("--full",
                action="store_true",
                dest="full",
                default=False,
                help="force a full synchronization instead of differential",
            ),
            Option("--since",
                type=int,
                default=None,
                help="synchronize since SINCE",
            ),
            exclusive=True,
        ),
        Group(
            Option("--force-download",
                action="store_true",
                dest="download",
                help="force downloading packages even if the hashes match",
                default=None,
            ),
            Option("--no-download",
                action="store_false",
                dest="download",
                help="disable downloading of files even if hashes mismatch",
            ),
            exclusive=True,
        ),
    ]

    def run(self, projects=None, concurrency=10, progress=True, download=None,
            since=None, full=False, store_since=True, raise_exc=False,
            repeat=False, timeout=None):
        # This is a hack to normalize the incoming projects to unicode
        projects = [x.decode("utf-8") for x in projects]

        if projects:
            logger.info("Will synchronize %s from pypi.python.org", projects)
        else:
            logger.info("will synchronize all projects from pypi.python.org")

        # Create the Pool that Synchronization will use
        pool = eventlet.GreenPool(concurrency)
        logger.debug("Using concurrency of %s for GreenPool", pool.size)

        # record if we should be grabbing since from redis
        fetch_since = not since and not full

        for _ in utils.repeat_every(
                    seconds=repeat if repeat else 0,
                    times=None if repeat else 1,
                ):
            # Determine what our since should be
            if fetch_since:
                fetched = redis.get(REDIS_SINCE_KEY)
                since = int(fetched) if not fetched is None else None
            elif full:
                since = None

            # Run the actual Synchronization
            synced = syncer(projects,
                        since=since,
                        pool=pool,
                        progress=progress,
                        download=download,
                        raise_exc=raise_exc,
                        timeout=timeout,
                    )

            # Save our synchronization time in redis
            if store_since:
                redis.set(REDIS_SINCE_KEY, synced)

            # Output the time we started the sync
            logger.info(
                "Synchronization from pypi.python.org completed at %s",
                synced,
            )

script.add_command("sync", Synchronize())

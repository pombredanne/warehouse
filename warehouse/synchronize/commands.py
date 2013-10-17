from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import logging

from flask.ext.script import (  # pylint: disable=E0611,F0401
                            Command, Group, Option)
from progress.bar import ShadyBar

from warehouse import db, redis, script
from warehouse import utils
from warehouse.history.models import Journal
from warehouse.packages import diff, store
from warehouse.packages.models import Project, FileType
from warehouse.synchronize.fetchers import PyPIFetcher


REDIS_JOURNALS_KEY = "warehouse:journals"
REDIS_SINCE_KEY = "warehouse:since"
REDIS_SYNC_LOCK_KEY = "warehouse:sync:lock:{project}"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class DummyBar(object):
    def iter(self, iterable):
        for item in iterable:
            yield item


def synchronize_project(project, fetcher, download=None):
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


def synchronize_classifiers(fetcher):
    # Sync the Classifiers
    for classifier in fetcher.classifiers():
        store.classifier(classifier)

    # Commit the classifiers
    db.session.commit()


def synchronize_by_journals(since=None, fetcher=None, progress=True,
        download=None):
    if fetcher is None:
        fetcher = PyPIFetcher()

    # Grab the current datetime
    current = fetcher.current()

    # Synchronize all the classifiers with PyPI
    synchronize_classifiers(fetcher)

    # Grab the journals since `since`
    journals = fetcher.journals(since=since)

    # Storage for projects that have been updated or deleted
    updated = set()
    deleted = set()

    # Check if we have anything to process before attempting to
    if journals:
        if progress:
            bar = ShadyBar("Processing Journals", max=len(journals))
        else:
            bar = DummyBar()

        # Handle Renames, these need to occur first because PyPI retroactively
        #   changes journal names to the new project, which if we experience
        #   any of these prior to handling a rename it'll trigger a sync which
        #   will act like it's a new project and not a renamed project.
        if since is not None:
            for journal in journals:
                if journal.action.lower().startswith("rename from "):
                    _, _, previous = journal.action.split(" ", 2)

                    proj = Project.get(previous)
                    proj.rename(journal.name)

        # Commit the renames
        db.session.commit()

        for journal in bar.iter(journals):
            if redis.sismember(REDIS_JOURNALS_KEY, journal.id):
                # We've already processed this entry, so skip to the next one
                continue

            created = datetime.datetime.utcfromtimestamp(journal.timestamp)
            Journal.create(
                        name=journal.name,
                        version=journal.version,
                        created=created,
                        action=journal.action,
                        pypi_id=journal.id,
                    )

            if (journal.action.lower() == "remove" and
                    journal.version is None):
                # Delete the entire project
                if journal.name not in deleted:
                    updated.discard(journal.name)
                    deleted.add(journal.name)

                    # Actually yank the project
                    Project.yank(journal.name, synchronize=False)
            elif journal.action.lower().startswith("rename from "):
                _, _, previous = journal.action.split(" ", 2)

                # Do nothing for right now, eventually we'll use this spot for
                #   creating a history event
            else:
                # Process the update
                if journal.name not in updated:
                    deleted.discard(journal.name)
                    updated.add(journal.name)

                    # Actually synchronize the project
                    synchronize_project(journal.name,
                        fetcher,
                        download=download,
                    )

            try:
                # Add this ID to our list of IDs we've processed in Redis
                redis.sadd(REDIS_JOURNALS_KEY, journal.id)

                # Commit any changes made from this journal entry
                db.session.commit()
            except:
                # If any exception occured during committing remove the id
                #   from redis
                redis.srem(REDIS_JOURNALS_KEY, journal.id)
                raise

    logger.info(
        "Finished processing journals at %s; updated %s and deleted %s",
        current, len(updated), len(deleted),
    )

    return current


def synchronize_by_projects(projects=None, fetcher=None, progress=True,
        download=None):
    if fetcher is None:
        fetcher = PyPIFetcher()

    # Grab the current datetime
    current = fetcher.current()

    # Synchronize all the classifiers with PyPI
    synchronize_classifiers(fetcher)

    if not projects:
        # Grab a list of projects from PyPI
        projects = fetcher.projects()

        # We are not synchronizing a subset of projects, so we can check for
        #   any deletions (if required) and yank them.
        diff.projects(projects)

        # Commit our yanked projects
        db.session.commit()

    if progress:
        bar = ShadyBar("Processing Projects", max=len(projects))
    else:
        bar = DummyBar()

    for project in bar.iter(projects):
        synchronize_project(project, fetcher, download=download)

    logger.info("Finished processing projects at %s", current)

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
        Option("--no-store",
            action="store_false",
            dest="store_since",
            default=True,
            help="do not store the synchronization time",
        ),
        Option("--full",
            action="store_true",
            dest="full",
            default=False,
            help="force a full synchronization instead of differential",
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

    def run(self, projects=None, progress=True, download=None, full=False,
                store_since=True, repeat=False):
        # This is a hack to normalize the incoming projects to unicode
        projects = [x.decode("utf-8") for x in projects]

        if projects:
            logger.info("Will synchronize %s from pypi.python.org", projects)
        else:
            logger.info("will synchronize all projects from pypi.python.org")

        for _ in utils.repeat_every(
                    seconds=repeat if repeat else 0,
                    times=None if repeat else 1,
                ):
            if full or projects:
                # We are preforming a full synchronization, or by a list of
                #   projects
                synced = synchronize_by_projects(projects,
                            progress=progress,
                            download=download,
                        )
            else:
                # Grab the since key from redis
                fetched = redis.get(REDIS_SINCE_KEY)
                since = int(fetched) if not fetched is None else None

                # We are preforming a standard journal based synchronization
                synced = synchronize_by_journals(since,
                        progress=progress,
                        download=download,
                    )

            # Save our synchronization time in redis
            if store_since:
                redis.set(REDIS_SINCE_KEY, synced)

script.add_command("sync", Synchronize())

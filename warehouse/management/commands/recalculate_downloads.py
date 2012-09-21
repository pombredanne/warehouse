import collections
import logging
import uuid

import progress.bar
import redis

from django.core.management.base import NoArgsCommand
from django.db import connection, transaction

from warehouse.conf import settings
from warehouse.models import Download


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = "Recalculates the download counts for all objects"

    def handle_noargs(self, **options):
        logger.info("Recalculating downloads")

        # Get the database cursors
        cursor = connection.cursor()
        downloads = connection.connection.cursor(name="cur" + str(uuid.uuid4()))

        totals = collections.Counter()

        with transaction.commit_manually():
            try:
                # Set all the download counts to 0
                cursor.execute("UPDATE warehouse_project SET downloads = 0")
                cursor.execute("UPDATE warehouse_version SET downloads = 0")
                cursor.execute("UPDATE warehouse_versionfile SET downloads = 0")

                # Get the number of downloads
                cursor.execute("SELECT reltuples FROM pg_class WHERE relname=%s", ["warehouse_download"])
                count = int(cursor.fetchall()[0][0])

                logger.info("Found %s download records", count)

                # Replay all the download counts
                downloads.execute("SELECT project, filename, downloads FROM warehouse_download")

                for record in progress.bar.ShadyBar("Recalculating", max=count).iter(downloads):
                    # Process Record
                    totals[(record[0], record[1])] += record[2]

                for (project, filename), changed in progress.bar.ShadyBar("Updating Counts", max=len(totals)).iter(totals.iteritems()):
                    Download.update_counts(project, filename, changed)
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()

        datastore = redis.StrictRedis(**dict([(k.lower(), v) for k, v in settings.REDIS.items()]))
        datastore.set("warehouse:stats:downloads", sum(totals.values()))

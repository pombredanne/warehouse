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
        downloads = connection.connection.cursor(name=str(uuid.uuid4()))

        total = 0

        with transaction.commit_manually():
            try:
                # Set all the download counts to 0
                cursor.execute("UPDATE warehouse_project SET downloads = 0")
                cursor.execute("UPDATE warehouse_version SET downloads = 0")
                cursor.execute("UPDATE warehouse_versionfile SET downloads = 0")

                # Get the number of downloads
                cursor.execute("SELECT COUNT(id) FROM warehouse_download")
                count = cursor.fetchall()[0][0]

                logger.info("Found %s download records", count)

                # Replay all the download counts
                downloads.execute("SELECT project, version, filename, downloads FROM warehouse_download")

                for record in progress.bar.ShadyBar("Recalculating", max=count).iter(downloads):
                    # Update download counts
                    Download.update_counts(record[0], record[1], record[2], record[3])

                    # Update running total
                    total += record[3]
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()

        datastore = redis.StrictRedis(**dict([(k.lower(), v) for k, v in settings.REDIS.get("default", {}).items()]))
        datastore.set("warehouse:stats:downloads", total)

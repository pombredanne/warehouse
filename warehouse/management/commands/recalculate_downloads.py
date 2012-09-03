import logging
import uuid

import redis

from django.core.management.base import NoArgsCommand
from django.db import connection, transaction

from warehouse.conf import settings
from warehouse.models import Download


# Number of rows to include in a transaction
ROWS_PER_TRANSACTION = 50


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = "Recalculates the download counts for all objects"

    def handle_noargs(self, **options):
        logger.info("Recalculating downloads")

        # Get the database cursors
        cursor = connection.cursor()
        downloads = connection.cursor(str(uuid.uuid4()))

        seen = set()

        total = 0

        try:
            with transaction.commit_manually():
                downloads.execute("SELECT project, version, filename, downloads FROM warehouse_download")

                for i, record in enumerate(downloads):
                    # Check if Project has not been seen and set downloads to 0 then
                    pids, vids = None, None

                    if not record[0] in seen:
                        cursor.execute("UPDATE warehouse_project SET downloads = 0 WHERE name = %s RETURNING id", [record[0]])
                        pids = cursor.fetchall()

                        if pids:
                            cursor.execute("UPDATE warehouse_version SET downloads = 0 WHERE project_id IN %s RETURNING id", [tuple([r[0] for r in pids])])
                            vids = cursor.fetchall()

                        if vids:
                            cursor.execute("UPDATE warehouse_versionfile SET downloads = 0 WHERE version_id IN %s", [tuple([r[0] for r in vids])])

                    # Update download counts
                    Download.update_counts(record[0], record[1], record[2], record[3])

                    # Update running total
                    total += record[3]

                    # Commit transactions
                    if not i % ROWS_PER_TRANSACTION:
                        transaction.commit()
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        datastore = redis.StrictRedis(**dict([(k.lower(), v) for k, v in settings.REDIS.get("default", {}).items()]))
        datastore.set("warehouse:stats:downloads", total)

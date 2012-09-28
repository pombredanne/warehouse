import bz2
import collections
import csv
import io
import logging
import os
import urlparse

import lxml.html
import requests

from django.db import connection, transaction

from warehouse.conf import settings
from warehouse.models import Download
from warehouse.redis import datastore
from warehouse.utils import locks


# How many rows to process between transactions
ROWS_PER_TRANSACTION = 25


logger = logging.getLogger(__name__)


def downloads(label):
    stats_url = getattr(settings, "PYPI_STATS_URL", "https://pypi.python.org/stats/days/")

    session = requests.session(verify=getattr(settings, "PYPI_SSL_CERT", os.path.join(os.path.dirname(__file__), "pypi.crt")))

    # Get the database cursor
    cursor = connection.cursor()

    # Get a listing of all the Files
    resp = session.get(stats_url)
    resp.raise_for_status()

    html = lxml.html.fromstring(resp.content)
    urls = [(urlparse.urljoin(stats_url, x), x) for x in html.xpath("//a/@href")]

    total = len(urls)

    for i, (url, statfile) in enumerate(urls):
        if not url.endswith(".bz2"):
            continue

        date = statfile[:-4]

        last_modified_key = "pypi:download:last_modified:%s" % url
        last_modified = datastore.get(last_modified_key)

        headers = {"If-Modified-Since": last_modified} if last_modified else None

        resp = session.get(url, headers=headers, prefetch=True)

        if resp.status_code == 304:
            logger.debug("Skipping %s, it has not been modified since %s", statfile, last_modified)
            continue

        resp.raise_for_status()

        try:
            with locks.Lock("pypi:locks:%s" % statfile, expires=settings.WAREHOUSE_DOWNLOAD_COUNT_TIMEOUT + 10 * 60):
                with transaction.commit_manually():
                    logger.info("Computing download counts from %s (%s/%s)", statfile, i + 1, total)

                    data = bz2.decompress(resp.content)
                    csv_r = csv.DictReader(io.BytesIO(data), ["project", "filename", "user_agent", "downloads"])

                    try:
                        cursor.execute("SELECT agent, id FROM warehouse_useragent")
                        user_agents = dict(cursor.fetchall())

                        totals = collections.Counter()

                        for i, row in enumerate(csv_r):
                            row["date"] = date
                            row["downloads"] = int(row["downloads"])

                            ua = user_agents.get(row["user_agent"], None)

                            if ua is None:
                                cursor.execute("SELECT id FROM warehouse_useragent WHERE agent = %s LIMIT 1", [row["user_agent"]])
                                uas = cursor.fetchall()

                                if not uas:
                                    cursor.execute("INSERT INTO warehouse_useragent (agent) VALUES (%s) RETURNING id", [row["user_agent"]])
                                    uas = cursor.fetchall()

                                ua = uas[0][0]
                                user_agents[row["user_agent"]] = ua

                            changed = 0

                            args = [row["project"], row["filename"], ua, date, label]
                            cursor.execute("""
                                    SELECT id, downloads
                                    FROM warehouse_download
                                    WHERE project = %s
                                        AND filename = %s
                                        AND user_agent_id = %s
                                        AND date = %s
                                        and label = %s
                                """, args)

                            downloads = cursor.fetchall()

                            if not downloads:
                                changed = row["downloads"]

                                if changed:
                                    cursor.execute("""
                                        INSERT INTO warehouse_download (label, date, user_agent_id, project, filename, downloads)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """, [label, date, ua, row["project"], row["filename"], row["downloads"]])
                            else:
                                # There should only ever be 1 here
                                assert len(downloads) == 1
                                d = downloads[0]

                                # The total new value minus the existing value == amount changed
                                changed = row["downloads"] - d[1]

                                if changed:
                                    cursor.execute("UPDATE warehouse_download SET downloads = downloads + %s WHERE id = %s", [changed, d[0]])

                            totals[(row["project"], row["filename"])] += changed

                            if settings.WAREHOUSE_UPDATE_DOWNLOAD_COUNTS:
                                Download.update_counts(row["project"], row["filename"], changed)

                            if not i % ROWS_PER_TRANSACTION:
                                if settings.WAREHOUSE_UPDATE_DOWNLOAD_COUNTS:
                                    datastore.incr("warehouse:stats:downloads", sum(totals.values()))

                                totals = collections.Counter()
                                transaction.commit()

                        if settings.WAREHOUSE_UPDATE_DOWNLOAD_COUNTS:
                            datastore.incr("warehouse:stats:downloads", sum(totals.values()))
                    except:
                        transaction.rollback()
                        raise
                    else:
                        transaction.commit()

                if "Last-Modified" in resp.headers:
                    datastore.set(last_modified_key, resp.headers["Last-Modified"])
                else:
                    datastore.delete(last_modified_key)
        except locks.LockTimeout:
            continue

        break

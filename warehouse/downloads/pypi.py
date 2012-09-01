import bz2
import csv
import io
import logging
import os
import urlparse
import uuid

import lxml.html
import redis
import requests

from django.db import connection, transaction, IntegrityError

from warehouse.conf import settings
from warehouse.utils import locks


# Number of rows to include in a transaction
ROWS_PER_TRANSACTION = 50


logger = logging.getLogger(__name__)


def downloads(label):
    stats_url = getattr(settings, "PYPI_STATS_URL", "https://pypi.python.org/stats/days/")

    session = requests.session(verify=getattr(settings, "PYPI_SSL_CERT", os.path.join(os.path.dirname(__file__), "pypi.crt")))

    redis_db = "pypi" if "pypi" in settings.REDIS else "default"

    config = settings.REDIS[redis_db]
    kwargs = dict([(k.lower(), v) for k, v in config.items()])
    r = redis.StrictRedis(**kwargs)

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
        year, month, day = date.split("-")

        last_modified_key = "pypi:download:last_modified:%s" % url
        last_modified = r.get(last_modified_key)

        headers = {"If-Modified-Since": last_modified} if last_modified else None

        resp = session.get(url, headers=headers, prefetch=True)

        if resp.status_code == 304:
            logger.debug("Skipping %s, it has not been modified since %s", statfile, last_modified)
            continue

        resp.raise_for_status()

        try:
            with locks.Lock("pypi:locks:%s" % statfile, expires=45 * 60, using="pypi"):
                logger.info("Computing download counts from %s (%s/%s)", statfile, i + 1, total)

                data = bz2.decompress(resp.content)
                csv_r = csv.DictReader(io.BytesIO(data), ["project", "filename", "user_agent", "downloads"])

                user_agents = {}

                cursor.execute("SELECT id, agent FROM warehouse_useragent")

                for i, agent in cursor.fetchall():
                    user_agents[agent] = i

                with transaction.commit_manually():
                    try:
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

                            cursor.execute("""
                                SELECT warehouse_version.version
                                FROM warehouse_version
                                INNER JOIN warehouse_versionfile ON (
                                    warehouse_version.id = warehouse_versionfile.version_id
                                )
                                WHERE warehouse_versionfile.filename = %s
                                LIMIT 1
                            """, [row["filename"]])
                            vfiles = cursor.fetchall()

                            if vfiles:
                                row["version"] = vfiles[0][0]

                            sid = transaction.savepoint()

                            try:
                                cursor.execute("""
                                    INSERT INTO warehouse_download (id, label, date, user_agent_id, project, version, filename, downloads)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """, [str(uuid.uuid4()), label, date, ua, row["project"], row.get("version", ""), row["filename"], row["downloads"]])
                            except IntegrityError:
                                transaction.savepoint_rollback(sid)

                                cursor.execute("""
                                    UPDATE warehouse_download
                                    SET downloads = %s
                                    WHERE label = %s
                                        AND date = %s
                                        AND user_agent_id = %s
                                        AND project = %s
                                        AND version = %s
                                        AND filename = %s
                                """, [row["downloads"], label, date, ua, row["project"], row.get("version", ""), row["filename"]])

                                transaction.savepoint_commit(sid)
                            else:
                                transaction.savepoint_commit(sid)

                            if not i % ROWS_PER_TRANSACTION:
                                transaction.commit()
                    except:
                        transaction.rollback()
                        raise
                    else:
                        transaction.commit()

                if "Last-Modified" in resp.headers:
                    r.set(last_modified_key, resp.headers["Last-Modified"])
                else:
                    r.delete(last_modified_key)
        except locks.LockTimeout:
            continue

        break

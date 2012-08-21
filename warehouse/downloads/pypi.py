import bz2
import csv
import io
import logging
import os
import urlparse

import lxml.html
import redis
import requests

from warehouse.conf import settings
from warehouse.models import Download, UserAgent, VersionFile


logger = logging.getLogger(__name__)


def downloads(label):
    stats_url = getattr(settings, "PYPI_STATS_URL", "https://pypi.python.org/stats/days/")

    session = requests.session(verify=getattr(settings, "PYPI_SSL_CERT", os.path.join(os.path.dirname(__file__), "pypi.crt")))
    r = redis.StrictRedis(host=getattr(settings, "REDIS_HOST", "localhost"), port=getattr(settings, "REDIS_PORT", 6379), password=getattr(settings, "REDIS_PASSWORD", None), db=getattr(settings, "PYPI_REDIS_DATABASE", 0))

    # Get a listing of all the Files
    resp = session.get(stats_url)
    resp.raise_for_status()

    html = lxml.html.fromstring(resp.content)
    urls = [(urlparse.urljoin(stats_url, x), x) for x in html.xpath("//a/@href")]

    for url, statfile in urls:
        if not url.endswith(".bz2"):
            continue

        date = statfile[:-4]
        year, month, day = date.split("-")

        last_modified_key = "pypi:download:last_modified:%s" % url
        last_modified = r.get(last_modified_key)

        headers = {"If-Modified-Since": last_modified} if last_modified else None

        resp = session.get(url, headers=headers, prefetch=True)

        if resp.status_code == 304:
            logger.info("Skipping %s, it has not been modified since %s", statfile, last_modified)
            continue

        resp.raise_for_status()

        logger.info("Computing download counts from %s", statfile)

        data = bz2.decompress(resp.content)
        csv_r = csv.DictReader(io.BytesIO(data), ["project", "filename", "user_agent", "downloads"])

        for row in csv_r:
            row["date"] = date
            row["downloads"] = int(row["downloads"])

            ua, _ = UserAgent.objects.get_or_create(agent=row["user_agent"])

            try:
                f = VersionFile.objects.filter(filename=row["filename"]).select_related("version")[:1].get()
            except VersionFile.DoesNotExist:
                pass
            else:
                row["version"] = f.version.version

            kwargs = row.copy()
            kwargs.update({"label": label, "user_agent": ua, "defaults": {"downloads": row["downloads"]}})
            del kwargs["downloads"]

            dload, created = Download.objects.get_or_create(**kwargs)

            if not created:
                dload.downloads = row["downloads"]
                dload.save()

        if "Last-Modified" in resp.headers:
            r.set(last_modified_key, resp.headers["Last-Modified"])
        else:
            r.delete(last_modified_key)

from optparse import make_option

import redis
import rq

from django.core.management.base import LabelCommand, CommandError
from django.utils import importlib

from warehouse.conf import settings


class Command(LabelCommand):
    args = "<label label ...>"
    help = "Spawns download counting jobs"

    option_list = LabelCommand.option_list + (
        make_option("--host", "-H",
            action="store",
            dest="host",
            help="The Redis hostname (default: localhost)"
        ),
        make_option("--port", "-p",
            action="store",
            dest="port",
            help="The Redis port number (default: 6379)"
        ),
        make_option("--db", "-d",
            action="store",
            dest="db",
            help="The Redis database (default: 0)"
        ),
        make_option("--password", "-P",
            action="store",
            dest="password",
            help="The password for Redis"
        ),
        make_option("--queue", "-q",
            action="store",
            dest="queue",
            default="low",
            help="RQ queue to send the job to"
        ),
        make_option("--url",
            action="store",
            dest="url",
            help="specify an url to a Redis instance"
        )
    )

    def handle_label(self, label, **options):
        if options.get("url", None):
            db = options.get("db", None) or getattr(settings, "RQ_REDIS_DB", 0)
            conn = redis.from_url(options["url"], db=db)
        else:
            host = options.get("host", None) or getattr(settings, "RQ_REDIS_HOST", "localhost")
            port = options.get("port", None) or getattr(settings, "RQ_REDIS_PORT", 6379)
            password = options.get("password", None) or getattr(settings, "RQ_REDIS_PASSWORD", None)
            db = options.get("db", None) or getattr(settings, "RQ_REDIS_DB", 0)

            conn = redis.Redis(host=host, port=port, db=db, password=password)

        if not label in settings.WAREHOUSE_DOWNLOAD_SOURCES:
            raise CommandError("No download source identified by the %s label" % label)

        module_name = settings.WAREHOUSE_DOWNLOAD_SOURCES[label]
        mod = importlib.import_module(module_name)
        func = getattr(mod, "downloads")

        q = rq.Queue(options["queue"], connection=conn)
        q.enqueue_call(func=func, args=(label,), timeout=3600)

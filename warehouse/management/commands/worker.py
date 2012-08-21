from optparse import make_option

import redis
import rq

from django.core.management.base import BaseCommand

from warehouse.conf import settings


class Command(BaseCommand):
    args = "<queue queue ...>"
    help = "Starts an RQ worker"

    option_list = BaseCommand.option_list + (
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
        make_option("--burst", "-b",
            action="store_true",
            dest="burst",
            default=False,
            help="Run in burst mode (quit after all work is done)"
        ),
        make_option("--name", "-n",
            action="store",
            dest="name",
            help="Specify a different name",
        ),
        make_option("--url",
            action="store",
            dest="url",
            help="specify an url to a Redis instance"
        )
    )

    def handle(self, *args, **options):
        if not args:
            args = ["default"]

        if options.get("url", None):
            db = options.get("db", None) or getattr(settings, "RQ_REDIS_DB", 0)
            conn = redis.from_url(options["url"], db=db)
        else:
            host = options.get("host", None) or getattr(settings, "RQ_REDIS_HOST", "localhost")
            port = options.get("port", None) or getattr(settings, "RQ_REDIS_PORT", 6379)
            password = options.get("password", None) or getattr(settings, "RQ_REDIS_PASSWORD", None)

            db = options.get("db", None) or getattr(settings, "RQ_REDIS_DB", 0)

            conn = redis.Redis(host=host, port=port, db=db, password=password)

        with rq.Connection(conn):
            worker = rq.Worker([rq.Queue(q) for q in args], name=options.get("name", getattr(settings, "RQ_NAME", None)))
            worker.work(burst=options.get("burst"))

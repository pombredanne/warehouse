from optparse import make_option

import redis
import rq

from django.core.management.base import BaseCommand

from warehouse.conf import settings


class Command(BaseCommand):
    args = "<queue queue ...>"
    help = "Starts an RQ worker"

    option_list = BaseCommand.option_list + (
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
    )

    def handle(self, *args, **options):
        if not args:
            args = ["default"]

        conn = redis.Redis(**dict([(k.lower(), v) for k, v in settings.REDIS.items()]))

        with rq.Connection(conn):
            worker = rq.Worker([rq.Queue(q) for q in args], name=options.get("name", getattr(settings, "RQ_NAME", None)))
            worker.work(burst=options.get("burst"))

from optparse import make_option

import redis
import rq

from django.core.management.base import LabelCommand, CommandError

from warehouse.conf import settings


class Command(LabelCommand):
    args = "<label label ...>"
    help = "Spawns download counting jobs"

    option_list = LabelCommand.option_list + (
        make_option("--redis", "-r",
            action="store",
            dest="redis",
            default="default",
            help="Which REDIS key to use (default: default)"
        ),
        make_option("--queue", "-q",
            action="store",
            dest="queue",
            default="low",
            help="RQ queue to send the job to"
        ),
    )

    def handle_label(self, label, **options):
        if not label in settings.WAREHOUSE_DOWNLOAD_SOURCES:
            raise CommandError("No download source identified by the %s label" % label)

        config = settings.REDIS[options["redis"]]
        kwargs = dict([(k.lower(), v) for k, v in config.items()])
        conn = redis.Redis(**kwargs)

        function = settings.WAREHOUSE_DOWNLOAD_SOURCES[label]

        q = rq.Queue(options["queue"], connection=conn)
        q.enqueue_call(func=function, args=(label,), timeout=15 * 60)

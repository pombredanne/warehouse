import logging

import redis

from django.core.management.base import NoArgsCommand
from django.db.models import Sum

from warehouse.conf import settings
from warehouse.models import Download


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = "Recalculates the download counts for all objects"

    def handle_noargs(self, **options):
        logger.info("Recalculating download totals")

        total_downloads = Download.objects.all().aggregate(Sum("downloads")).get("downloads__sum", None)

        if total_downloads is None:
            total_downloads = 0

        datastore = redis.StrictRedis(**dict([(k.lower(), v) for k, v in settings.REDIS.get("default", {}).items()]))
        datastore.set("warehouse:stats:downloads", total_downloads)

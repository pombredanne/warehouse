import logging

from django.core.management.base import NoArgsCommand
from django.db.models import Sum

from warehouse.models import Project, Version, VersionFile, Download
from warehouse.utils.query import RangeQuerySetWrapper


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = "Recalculates the download counts for all objects"

    def handle_noargs(self, **options):
        logger.info("Recalculating downloads for Projects")

        for p in RangeQuerySetWrapper(Project.objects.all().only("pk", "name")):
            downloads = Download.objects.filter(project=p.name).aggregate(Sum("downloads")).get("downloads__sum", None)

            if downloads is None:
                downloads = 0

            logger.debug("Recalculating downloads for Project %s (now: %s)", p.name, downloads)

            Project.objects.filter(pk=p.pk).update(downloads=downloads)

        logger.info("Recalculating downloads for Versions")

        for v in RangeQuerySetWrapper(Version.objects.all().select_related("project").only("pk", "project__name", "version")):
            downloads = Download.objects.filter(project=v.project.name, version=v.version).aggregate(Sum("downloads")).get("downloads__sum", None)

            if downloads is None:
                downloads = 0

            logger.debug("Recalculating downloads for Version %s %s (now: %s)", v.version, v.project.name, downloads)

            Version.objects.filter(pk=v.pk).update(downloads=downloads)

        logger.info("Recalculating downloads for VersionFiles")

        for vf in RangeQuerySetWrapper(VersionFile.objects.all().select_related("version", "version__project").only("pk", "version__project__name", "version__version", "filename")):
            downloads = Download.objects.filter(project=vf.version.project.name, version=vf.version.version, filename=vf.filename).aggregate(Sum("downloads")).get("downloads__sum", None)

            if downloads is None:
                downloads = 0

            logger.debug("Recalculating downloads for VersionFile %s (now: %s)", vf.filename, downloads)

            VersionFile.objects.filter(pk=vf.pk).update(downloads=downloads)

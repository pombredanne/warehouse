from django.core.management.base import NoArgsCommand
from django.db.models import Sum

from warehouse.models import Project, Version, VersionFile, Download
from warehouse.utils.query import RangeQuerySetWrapper


class Command(NoArgsCommand):
    help = "Recalculates the download counts for all objects"

    def handle_noargs(self, **options):
        for p in RangeQuerySetWrapper(Project.objects.all().only("pk", "name")):
            downloads = Download.objects.filter(project=p.name).aggregate(Sum("downloads")).get("dowloads__sum", None)

            if downloads is None:
                downloads = 0

            Project.objects.filter(pk=p.pk).update(downloads=downloads)

        for v in RangeQuerySetWrapper(Version.objects.all().select_related("project").only("pk", "project__name", "version")):
            downloads = Download.objects.filter(project=v.project.name, version=v.version).aggregate(Sum("downloads")).get("dowloads__sum", None)

            if downloads is None:
                downloads = 0

            Version.objects.filter(pk=v.pk).update(downloads=downloads)

        for vf in RangeQuerySetWrapper(VersionFile.objects.all().select_related("version", "version__project").only("pk", "version__project__name", "version__version", "filename")):
            downloads = Download.objects.filter(project=vf.version.project.name, version=vf.version.version, filename=vf.filename).aggregate(Sum("downloads")).get("dowloads__sum", None)

            if downloads is None:
                downloads = 0

            VersionFile.objects.filter(pk=vf.pk).update(downloads=downloads)

from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver


from warehouse.models.packaging import Project, Version, VersionFile
from warehouse.utils.track_data import track_data
from warehouse.utils.transactions import xact


__all__ = ["UserAgent", "Download"]


class UserAgent(models.Model):
    agent = models.TextField(unique=True)

    class Meta:
        app_label = "warehouse"


@track_data("downloads")
class Download(models.Model):
    label = models.CharField(max_length=25)

    date = models.DateField()
    user_agent = models.ForeignKey(UserAgent)

    project = models.CharField(max_length=512)
    filename = models.CharField(max_length=512)

    downloads = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "warehouse"
        unique_together = ("label", "date", "project", "filename", "user_agent")

    @staticmethod
    def update_counts(project, filename, changed):
        if not changed:
            return  # Shortcut if there are no changes

        with xact():
            VersionFile.objects.filter(version__project__name=project, filename=filename).update(downloads=F("downloads") + changed)
            Version.objects.filter(project__name=project, files__filename=filename).update(downloads=F("downloads") + changed)
            Project.objects.filter(name=project, versions__files__filename=filename).update(downloads=F("downloads") + changed)


@receiver(post_save, sender=Download)
def update_downloads(sender, created, instance, **kwargs):
    if created:
        amount = instance.downloads
    else:
        amount = instance.downloads - instance.old_value("downloads")

    if amount:
        with xact():
            VersionFile.objects.filter(version__project__name=instance.project, filename=instance.filename).update(downloads=F("downloads") + amount)
            Version.objects.filter(project__name=instance.project, files__filename=instance.filename).update(downloads=F("downloads") + amount)
            Project.objects.filter(name=instance.project, versions__files__filename=instance.filename).update(downloads=F("downloads") + amount)

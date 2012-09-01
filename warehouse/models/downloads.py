import redis

from django.db import connection, models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from uuidfield import UUIDField

from warehouse.conf import settings
from warehouse.models.packaging import Project, Version, VersionFile
from warehouse.utils.track_data import track_data


__all__ = ["UserAgent", "Download"]


class UserAgent(models.Model):
    agent = models.TextField(unique=True)

    class Meta:
        app_label = "warehouse"


@track_data("downloads")
class Download(models.Model):
    id = UUIDField(auto=True, primary_key=True)

    label = models.CharField(max_length=25)

    date = models.DateField()
    user_agent = models.ForeignKey(UserAgent)

    project = models.CharField(max_length=150)
    version = models.CharField(max_length=512)
    filename = models.CharField(max_length=200)

    downloads = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "warehouse"
        unique_together = ("label", "date", "project", "version", "filename", "user_agent")


@receiver(post_save, sender=Download)
def update_downloads(sender, created, instance, **kwargs):
    if created:
        amount = instance.downloads
    else:
        amount = instance.downloads - instance.old_value("downloads")

    Project.objects.filter(
                        name=instance.project
                    ).update(downloads=F("downloads") + amount)

    Version.objects.filter(
                        project__name=instance.project,
                        version=instance.version
                    ).update(downloads=F("downloads") + amount)

    VersionFile.objects.filter(
                            version__project__name=instance.project,
                            version__version=instance.version,
                            filename=instance.filename
                        ).update(downloads=F("downloads") + amount)

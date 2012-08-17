from django.db import models

from warehouse.fields.uuid import UUIDField


__all__ = ["UserAgent", "Download"]


class UserAgent(models.Model):
    agent = models.TextField(unique=True)

    class Meta:
        app_label = "warehouse"


class Download(models.Model):
    id = UUIDField(primary_key=True)

    datetime = models.DateTimeField()
    user_agent = models.ForeignKey(UserAgent)

    project = models.CharField(max_length=150)
    version = models.CharField(max_length=512)
    filename = models.CharField(max_length=200)

    downloads = models.PositiveInteger(default=0)

    class Meta:
        app_label = "warehouse"

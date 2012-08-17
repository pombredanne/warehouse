from django.db import models

from uuidfield import UUIDField


__all__ = ["UserAgent", "Download"]


class UserAgent(models.Model):
    agent = models.TextField(unique=True)

    class Meta:
        app_label = "warehouse"


class Download(models.Model):
    id = UUIDField(auto=True, primary_key=True)

    date = models.DateField()
    user_agent = models.ForeignKey(UserAgent)

    project = models.CharField(max_length=150)
    version = models.CharField(max_length=512)
    filename = models.CharField(max_length=200)

    downloads = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "warehouse"

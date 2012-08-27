from django.db import models

from django.contrib.auth.models import User

from json_field import JSONField
from model_utils import Choices
from model_utils.models import TimeStampedModel

from warehouse.conf import settings


__all__ = ["Event"]


class EventManager(models.Manager):

    def log(self, **kwargs):
        if settings.WAREHOUSE_API_HISTORY:
            return self.create(**kwargs)


class Event(TimeStampedModel):

    ACTIONS = Choices(
        ("history_started", "History Started"),
        ("project_created", "Project Created"),
        ("project_updated", "Project Updated"),
        ("project_deleted", "Project Deleted"),
        ("version_created", "Version Created"),
        ("version_updated", "Version Updated"),
        ("version_deleted", "Version Deleted"),
        ("file_created", "File Created"),
        ("file_updated", "File Updated"),
        ("file_deleted", "File Deleted"),
    )

    user = models.ForeignKey(User)

    project = models.CharField(max_length=150)
    version = models.CharField(max_length=512)
    filename = models.CharField(max_length=200)

    action = models.CharField(max_length=50, choices=ACTIONS)

    data = JSONField()

    # Manager
    objects = EventManager()

    class Meta:
        app_label = "warehouse"

from django.db import models

from django.contrib.auth.models import User

from django_hstore import hstore
from model_utils import Choices
from model_utils.models import TimeStampedModel


__all__ = ["Event"]


class Event(TimeStampedModel):

    ACTIONS = Choices(
        ("project_created", "Project Created"),
    )

    user = models.ForeignKey(User)

    project = models.CharField(max_length=150)
    version = models.CharField(max_length=512)
    filename = models.CharField(max_length=200)

    action = models.CharField(max_length=50, choices=ACTIONS)

    data = hstore.DictionaryField(blank=True, default=dict)

    # Manager
    objects = hstore.HStoreManager()

    class Meta:
        app_label = "warehouse"

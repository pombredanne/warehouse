from django.db import models

from django.contrib.auth.models import User

from django_hstore import hstore
from model_utils.models import TimeStampedModel


__all__ = ["Event"]


class Event(TimeStampedModel):
    user = models.ForeignKey(User)

    project = models.CharField(max_length=150)
    version = models.CharField(max_length=512)
    filename = models.CharField(max_length=200)

    data = hstore.DictionaryField(blank=True, default=dict)

    # Manager
    objects = hstore.HStoreManager()

    class Meta:
        app_label = "warehouse"

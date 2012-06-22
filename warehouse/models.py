import re

from django.db import models

from model_utils.models import TimeStampedModel

_normalize_regex = re.compile(r"[^A-Za-z0-9.]+")


class Project(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)

    # De-normalization
    normalized = models.CharField(max_length=150, unique=True)
    downloads = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.normalized = _normalize_regex.sub("-", self.name).lower()
        return super(Project, self).save(*args, **kwargs)

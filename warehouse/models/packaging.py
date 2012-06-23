import re

from django.db import models

from django_hstore import hstore
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from model_utils.models import TimeStampedModel

from warehouse.fields import dbarray


__all__ = ["Project", "Version"]


METADATA_VERSIONS = [
    ("1.0", "1.0"),
    ("1.1", "1.1"),
    ("1.2", "1.2"),
]

_normalize_regex = re.compile(r"[^A-Za-z0-9.]+")


class Project(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)

    # De-normalization
    normalized = models.CharField(max_length=150, unique=True)
    downloads = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "warehouse"

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.normalized = _normalize_regex.sub("-", self.name).lower()
        return super(Project, self).save(*args, **kwargs)


class Version(models.Model):
    project = models.ForeignKey(Project, related_name="releases")
    version = models.CharField(max_length=512)

    created = AutoCreatedField("created", db_index=True)
    modified = AutoLastModifiedField("modified")

    order = models.IntegerField(default=0, db_index=True)
    yanked = models.BooleanField(default=False)

    # Meta data
    metadata_version = models.CharField(max_length=5, choices=METADATA_VERSIONS)

    summary = models.TextField(blank=True)
    description = models.TextField(blank=True)

    author = models.TextField(blank=True)
    author_email = models.TextField(blank=True)

    maintainer = models.TextField(blank=True)
    maintainer_email = models.TextField(blank=True)

    license = models.TextField(blank=True)

    platforms = dbarray.TextArrayField(blank=True)
    supported_platforms = dbarray.TextArrayField(blank=True)

    # @@@ Can we convert this to a tagging system instead of a free form text field?
    keywords = models.TextField(blank=True)

    uris = hstore.DictionaryField()

    # Requirements
    requires_python = models.CharField(max_length=25, blank=True)
    requires_external = dbarray.TextArrayField(blank=True)

    # Trove Classifiers
    classifiers = models.ManyToManyField("warehouse.Classifier", related_name="releases", blank=True)

    # Manager
    objects = hstore.HStoreManager()

    class Meta:
        app_label = "warehouse"
        unique_together = ("project", "version")

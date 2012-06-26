import re

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_hstore import hstore
from model_utils import Choices
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from model_utils.models import TimeStampedModel

from warehouse.conf import settings
from warehouse.fields import dbarray
from warehouse.utils.packages import version_file_upload_path, package_storage


__all__ = [
    "Project", "Version", "VersionFile",
    "Require", "Provide", "Obsolete",
    "OldRequire", "OldProvide", "OldObsolete",
]


METADATA_VERSIONS = [
    ("1.0", "1.0"),
    ("1.1", "1.1"),
    ("1.2", "1.2"),
]

_normalize_regex = re.compile(r"[^A-Za-z0-9.]+")


class Project(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)

    # This mostly exists for sake of the Simple and Simple-Restricted API
    uris = dbarray.TextArrayField(blank=True)

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


class VersionFile(models.Model):

    TYPES = Choices(
        ("sdist", _("Source")),
        ("bdist_egg", "Egg"),
        ("bdist_msi", "MSI"),
        ("bdist_dmg", "DMG"),
        ("bdist_rpm", "RPM"),
        ("bdist_dumb", _("Dumb Binary Distribution")),
        ("bdist_wininst", _("Windows Installer Binary Distribution")),
    )

    version = models.ForeignKey(Version, related_name="files")

    created = AutoCreatedField("created", db_index=True)
    modified = AutoLastModifiedField("modified")

    yanked = models.BooleanField(default=False)

    type = models.CharField(max_length=25, choices=TYPES)

    file = models.FileField(upload_to=version_file_upload_path, storage=package_storage, max_length=512)
    python_version = models.CharField(max_length=25)
    digests = hstore.DictionaryField()

    comment = models.TextField(blank=True)

    # De normalization
    filename = models.CharField(max_length=200)
    filesize = models.PositiveIntegerField(default=0)

    # Manager
    objects = hstore.HStoreManager()

    class Meta:
        app_label = "warehouse"

    def __unicode__(self):
        return self.filename


class BaseRequirement(models.Model):

    name = models.CharField(max_length=150)
    version = models.CharField(max_length=50, blank=True)
    environment = models.TextField(blank=True)

    class Meta:
        app_label = "warehouse"
        abstract = True

    def __unicode__(self):
        rtr = self.name

        if self.version:
            rtr = "{rtr} ({version})".format(rtr=rtr, version=self.version)

        if self.environment:
            rtr = "{rtr}; {environment}".format(rtr=rtr, environment=self.environment)

        return rtr


# These are the *-Dist version of Requires/Provides/Obsoletes, and are the way forward
class Require(BaseRequirement):
    project_version = models.ForeignKey(Version, related_name="requires")


class Provide(BaseRequirement):
    project_version = models.ForeignKey(Version, related_name="provides")


class Obsolete(BaseRequirement):
    project_version = models.ForeignKey(Version, related_name="obsoletes")


# These are the original version of Requires/Provides/Obsoletes and are mostly useless
class OldRequire(BaseRequirement):
    project_version = models.ForeignKey(Version, related_name="old_requires")


class OldProvide(BaseRequirement):
    project_version = models.ForeignKey(Version, related_name="old_provides")


class OldObsolete(BaseRequirement):
    project_version = models.ForeignKey(Version, related_name="old_obsoletes")

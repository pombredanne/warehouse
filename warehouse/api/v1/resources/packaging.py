from tastypie import fields
from tastypie.authentication import MultiAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.bundle import Bundle
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource as TastypieModelResource

from warehouse.api.authentication import BasicAuthentication
from warehouse.api.fields import ConditionalToMany
from warehouse.api.resources import ModelResource
from warehouse.models import Project, Version, VersionFile
from warehouse.models import Require, Provide, Obsolete


# @@@ Sort out Permissions
# @@@ Allow deletion of projects if user has permission
# @@@ Allow creating a new version of a project if user has permission
# @@@ Allow editing a version of a project if user has permission
#         - Should restrict which fields can be edited based on user
# @@@ Hydrate classifiers into Trove objects
#         - We should not allow new Trove objects to be created
# @@@ Fix BasicAuthentication Realm


__all__ = [
        "ProjectResource", "VersionResource", "FileResource",
        "RequireResource", "ObsoleteResource", "ProvideResource",
    ]


def handle_yanked_versions(bundle):
    if not bundle.request.GET.get("show_yanked", "no").lower() in ["yes", "on", "true", "t", "1"]:
        return bundle.obj.versions.filter(yanked=False)
    return bundle.obj.versions.all()


def handle_yanked_files(bundle):
    if not bundle.request.GET.get("show_yanked", "no").lower() in ["yes", "on", "true", "t", "1"]:
        return bundle.obj.files.filter(yanked=False)
    return bundle.obj.files.all()


class ProjectResource(ModelResource):

    # Read only fields
    created = fields.DateTimeField(attribute="created")  # @@@ Make this Read only
    downloads = fields.IntegerField(attribute="downloads", readonly=True)
    normalized = fields.CharField(attribute="normalized", readonly=True)

    # related fields
    versions = ConditionalToMany("warehouse.api.v1.resources.VersionResource", handle_yanked_versions, readonly=True, null=True)

    class Meta:
        resource_name = "projects"
        detail_uri_name = "normalized"

        queryset = Project.objects.all()
        fields = ["created", "downloads", "name", "normalized"]

        filtering = {
            "name": ALL,
            "normalized": ALL,
        }

        ordering = ["name", "normalized", "downloads"]

        authentication = MultiAuthentication(BasicAuthentication())
        authorization = DjangoAuthorization()

        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get"]


class VersionResource(ModelResource):

    # Read Only Fields
    project = fields.ToOneField("warehouse.api.v1.resources.ProjectResource", "project")
    version = fields.CharField(attribute="version")
    yanked = fields.BooleanField(attribute="yanked")

    # Advanced Data Prep
    uris = fields.DictField(attribute="uris")
    platforms = fields.ListField(attribute="platforms")
    supported_platforms = fields.ListField(attribute="supported_platforms")
    requires_external = fields.ListField(attribute="requires_external")
    keywords = fields.ListField(attribute="keywords")

    author = fields.DictField()
    maintainer = fields.DictField()
    classifiers = fields.ListField()

    files = ConditionalToMany("warehouse.api.v1.resources.FileResource", handle_yanked_files, readonly=True, null=True)

    # Requirements
    requires = fields.ToManyField("warehouse.api.v1.resources.RequireResource", "requires", related_name="project_version", null=True, full=True)
    provides = fields.ToManyField("warehouse.api.v1.resources.ProvideResource", "provides", null=True, full=True)
    obsoletes = fields.ToManyField("warehouse.api.v1.resources.ObsoleteResource", "obsoletes", null=True, full=True)

    class Meta:
        resource_name = "versions"
        detail_uri_name = "version"

        parent_resource = ProjectResource
        parent_resource_uri_prefix = "project"

        queryset = Version.objects.all()
        fields = [
            "created", "project", "version", "yanked",
            "summary", "description", "license", "uris",
            "author", "maintainer", "keywords",
            "platforms", "supported_platforms",
            "requires_python", "requires_external",
            "requires", "provides", "obsoletes",
        ]

        filtering = {
            "project": ALL_WITH_RELATIONS,
        }

        authentication = MultiAuthentication(BasicAuthentication())
        authorization = DjangoAuthorization()

        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get"]

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(VersionResource, self).build_filters(filters)

        if not filters.get("show_yanked", "no").lower() in ["yes", "on", "true", "t", "1"]:
            orm_filters["yanked"] = False

        return orm_filters

    def dehydrate_author(self, bundle):
        person = {}

        if bundle.obj.author:
            person.update({"name": bundle.obj.author})

        if bundle.obj.author_email:
            person.update({"email": bundle.obj.author_email})

        return person

    def dehydrate_maintainer(self, bundle):
        person = {}

        if bundle.obj.maintainer:
            person.update({"name": bundle.obj.maintainer})

        if bundle.obj.maintainer_email:
            person.update({"email": bundle.obj.maintainer_email})

        return person

    def dehydrate_classifiers(self, bundle):
        return [c.trove for c in bundle.obj.classifiers.all()]

    def hydrate(self, bundle):
        bundle.obj.author = bundle.data.get("author", {}).get("name", "")
        bundle.obj.author_email = bundle.data.get("author", {}).get("email", "")

        bundle.obj.maintainer = bundle.data.get("maintainer", {}).get("name", "")
        bundle.obj.maintainer_email = bundle.data.get("maintainer", {}).get("email", "")

        return bundle

    def hydrate_requires(self, bundle):
        data = []

        for x in bundle.data["requires"]:
            if not isinstance(x, Bundle):
                _data = x.copy()
                _data.update({
                    "project_version": bundle.obj,
                    })
                data.append(_data)
        if data:
            bundle.data["requires"] = data

        return bundle


class RequireResource(TastypieModelResource):

    project_version = fields.ToOneField("warehouse.api.v1.resources.VersionResource", "project_version")

    class Meta:
        fields = ["name", "version", "environment"]
        include_resource_uri = False
        queryset = Require.objects.all()

    def dehydrate(self, bundle):
        if "project_version" in bundle.data:
            del bundle.data["project_version"]
        return bundle


class ProvideResource(TastypieModelResource):

    class Meta:
        fields = ["name", "version", "environment"]
        include_resource_uri = False
        queryset = Provide.objects.all()


class ObsoleteResource(TastypieModelResource):

    class Meta:
        fields = ["name", "version", "environment"]
        include_resource_uri = False
        queryset = Obsolete.objects.all()


class FileResource(ModelResource):

    digests = fields.DictField(attribute="digests")

    class Meta:
        resource_name = "files"
        detail_uri_name = "filename"

        parent_resource = VersionResource
        parent_resource_uri_prefix = "version"

        queryset = VersionFile.objects.all()
        fields = [
            "version", "created", "modified", "yanked", "type", "file",
            "python_version", "digests", "comment", "filename", "filesize",
        ]

        filtering = {
            "version": ALL_WITH_RELATIONS,
        }

        list_allowed_methods = ["get"]
        detail_allowed_methods = ["get"]

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(FileResource, self).build_filters(filters)

        if not filters.get("show_yanked", "no").lower() in ["yes", "on", "true", "t", "1"]:
            orm_filters["yanked"] = False

        return orm_filters

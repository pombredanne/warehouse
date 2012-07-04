from tastypie import fields
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from warehouse.api.resources import ModelResource
from warehouse.models import Project, Version


# @@@ Allow deletion of projects if user has permission
# @@@ Allow creating a new version of a project if user has permission
# @@@ Allow editing a version of a project if user has permission
#         - Should restrict which fields can be edited based on user
# @@@ Can we use actual data structures for version author and maintainer


class ProjectResource(ModelResource):

    created = fields.DateTimeField(attribute="created", readonly=True)
    downloads = fields.IntegerField(attribute="downloads", readonly=True)
    normalized = fields.CharField(attribute="normalized", readonly=True)

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

        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get"]


class VersionResource(ModelResource):

    # Read Only Fields
    project = fields.ToOneField(ProjectResource, "project", readonly=True)
    version = fields.CharField(attribute="version", readonly=True)
    yanked = fields.BooleanField(attribute="yanked", readonly=True)

    # Advanced Data Prep
    uris = fields.DictField(attribute="uris")
    platforms = fields.ListField(attribute="platforms")
    supported_platforms = fields.ListField(attribute="supported_platforms")
    requires_external = fields.ListField(attribute="requires_external")

    class Meta:
        resource_name = "versions"
        parent_resource = ProjectResource
        parent_resource_uri_prefix = "project"

        queryset = Version.objects.all()
        fields = [
            "created", "project", "version", "yanked",
            "summary", "description", "license", "uris",
            "author", "author_email", "maintainer", "maintainer_email",
            "platforms", "supported_platforms",
            "requires_python", "requires_external",
        ]

        filtering = {
            "project": ALL_WITH_RELATIONS,
        }

        list_allowed_methods = ["get"]
        detail_allowed_methods = ["get"]

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(VersionResource, self).build_filters(filters)

        if not filters.get("show_yanked", "no").lower() in ["yes", "on", "true", "t", "1"]:
            orm_filters["yanked"] = False

        return orm_filters

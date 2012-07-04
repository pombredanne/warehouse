from tastypie import fields
from tastypie.constants import ALL

from warehouse.api.resources import ModelResource
from warehouse.models import Project


# @@@ Allow deletion of projects if user has permission


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

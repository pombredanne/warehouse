from tastypie import fields
from tastypie.resources import ModelResource

from warehouse.models import Project


# @@@ Allow deletion of projects if user has permission


class ProjectResource(ModelResource):

    created = fields.DateTimeField(attribute="created", readonly=True)
    downloads = fields.IntegerField(attribute="downloads", readonly=True)
    normalized = fields.CharField(attribute="normalized", readonly=True)

    class Meta:
        resource_name = "projects"

        queryset = Project.objects.all()
        fields = ["created", "downloads", "name", "normalized"]

        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get"]

from tastypie import fields
from tastypie.resources import ModelResource

from warehouse.models import Project


class ProjectResource(ModelResource):

    created = fields.DateTimeField(attribute="created", readonly=True)
    downloads = fields.IntegerField(attribute="downloads", readonly=True)
    normalized = fields.CharField(attribute="normalized", readonly=True)

    class Meta:
        resource_name = "project"

        queryset = Project.objects.all()
        fields = ["created", "downloads", "name", "normalized"]

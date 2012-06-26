from tastypie import fields
from tastypie.resources import ModelResource

from warehouse.models import Project


class ProjectResource(ModelResource):

    class Meta:
        resource_name = "project"

        queryset = Project.objects.all()
        fields = ["created", "downloads", "name", "normalized"]

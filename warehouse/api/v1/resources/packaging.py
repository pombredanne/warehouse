from django.conf.urls import url

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.utils import trailing_slash

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

        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get"]

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

from django.conf.urls import patterns, url, include

from tastypie.api import Api

from warehouse.api.v1.resources import ProjectResource, VersionResource, FileResource, DownloadResource

v1_api = Api(api_name="v1")
v1_api.register(ProjectResource())
v1_api.register(VersionResource())
v1_api.register(FileResource())
v1_api.register(DownloadResource())

urlpatterns = patterns("",
    url(r"", include(v1_api.urls)),
)

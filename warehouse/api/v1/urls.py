from django.conf.urls import patterns, url, include

from warehouse.api.v1.resources import ProjectResource, VersionResource, FileResource

urlpatterns = patterns("",
    url(r"", include(ProjectResource().urls)),
    url(r"", include(VersionResource().urls)),
    url(r"", include(FileResource().urls)),
)

from django.conf.urls import patterns, url, include

from warehouse.api.v1.resources import ProjectResource

urlpatterns = patterns("",
    url(r"", include(ProjectResource().urls)),
)

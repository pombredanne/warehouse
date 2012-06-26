from django.conf.urls import patterns, include, url

from tastypie.api import Api

from warehouse.api.resources import ProjectResource

v1 = Api(api_name="v1")
v1.register(ProjectResource())

urlpatterns = patterns("",
    url(r"", include(v1.urls)),
)

from django.conf.urls import patterns, url

from warehouse.api.simple.views import ProjectIndex, ProjectDetail

urlpatterns = patterns("",
    url(r"^$", ProjectIndex.as_view(restricted=True), name="api_restricted_index"),
    url(r"^(?P<slug>[^/]+)/(?:(?P<version>[^/]+)/)?$", ProjectDetail.as_view(restricted=True), name="api_resticted_detail"),
)

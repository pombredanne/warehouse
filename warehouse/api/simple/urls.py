from django.conf.urls import patterns, url

from warehouse.api.simple.views import ProjectIndex

urlpatterns = patterns("",
    url(r"^$", ProjectIndex.as_view())
)

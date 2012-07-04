from django.conf.urls import patterns, include, url

urlpatterns = patterns("",
    url(r"^v1/", include("warehouse.api.v1.urls")),
)

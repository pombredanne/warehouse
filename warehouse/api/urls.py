from django.conf.urls import patterns, include, url

urlpatterns = patterns("",
    url(r"^v1/", include("warehouse.api.v1.urls")),
    url(r"^simple/", include("warehouse.api.simple.urls")),
    url(r"^restricted/", include("warehouse.api.simple.restricted")),
)

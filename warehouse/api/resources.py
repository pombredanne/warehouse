from django.conf.urls import url

from tastypie.resources import ModelResource as TastypieModelResource
from tastypie.utils import trailing_slash


__all__ = ["ModelResource"]


class ModelResource(TastypieModelResource):

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

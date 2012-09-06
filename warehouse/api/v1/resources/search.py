from django.core.urlresolvers import NoReverseMatch

from haystack.inputs import AutoQuery, Exact
from haystack.models import SearchResult
from haystack.query import SearchQuerySet, SQ
from tastypie import fields
from tastypie.authentication import MultiAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.bundle import Bundle
from tastypie.exceptions import BadRequest

from warehouse.api.authentication import BasicAuthentication
from warehouse.api.resources import Resource
from warehouse.api.serializers import Serializer


__all__ = ["SearchResource"]


class SearchResource(Resource):

    name = fields.CharField("name", readonly=True)
    summary = fields.CharField("summary", readonly=True)
    description = fields.CharField("description", readonly=True)

    class Meta:
        resource_name = "search"
        object_class = SearchResult

        authentication = MultiAuthentication(BasicAuthentication())
        authorization = DjangoAuthorization()

        list_allowed_methods = ["get"]
        detail_allowed_methods = []

        #cache_control = {"public": True, "max_age": 60, "s_maxage": 60}

        serializer = Serializer(formats=["json", "jsonp"])

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is not None:
            url_name = 'api_dispatch_detail'

            kwargs = {
                "resource_name": "projects",
            }

            if self._meta.api_name is not None:
                kwargs["api_name"] = self._meta.api_name

            if bundle_or_obj is not None:
                if isinstance(bundle_or_obj, Bundle):
                    kwargs["normalized"] = getattr(bundle_or_obj.obj, "normalized")
                else:
                    kwargs["normalized"] = getattr(bundle_or_obj, "normalized")

            return self._build_reverse_url(url_name, kwargs=kwargs)

        try:
            return self._build_reverse_url(url_name, kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

    def apply_filters(self, request, applicable_filters):
        if "q" in applicable_filters:
            query = applicable_filters["q"]
            return self.get_object_list(request).filter(SQ(name=Exact(query)) | SQ(content=AutoQuery(query)))

        return self.get_object_list(request)

    def get_object_list(self, request):
        query = SearchQuerySet()
        return query

    def obj_get_list(self, request=None, **kwargs):
        filters = {}

        if hasattr(request, 'GET'):
            # Grab a mutable copy.
            filters = request.GET.copy()

        # Update with the provided kwargs.
        filters.update(kwargs)
        applicable_filters = self.build_filters(filters=filters)

        try:
            base_object_list = self.apply_filters(request, applicable_filters)
            return self.apply_authorization_limits(request, base_object_list)
        except ValueError:
            raise BadRequest("Invalid resource lookup data provided (mismatched type).")

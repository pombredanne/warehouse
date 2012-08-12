import urllib

from django.conf.urls import include, patterns, url
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource as TastypieModelResource
from tastypie.utils import trailing_slash


__all__ = ["ModelResource"]


def _get_model_attr(obj, prefix, attr):
    for level in prefix:
        obj = getattr(obj, level)

    return getattr(obj, attr)


class ModelResource(TastypieModelResource):

    def base_urls(self):
        urls = [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<%s>[^/]+)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

        parent = getattr(self._meta, "parent_resource", None)
        child = self

        prefix = []

        while parent is not None:
            p = parent()
            include_pattern = patterns("", *urls)

            prefix.append(child._meta.parent_resource_uri_prefix)

            urls = [
                url(r"^%s/(?P<%s>[^/]+)/" % (p._meta.resource_name, "__".join(prefix[:] + [p._meta.detail_uri_name])), include(include_pattern)),
            ]

            child = parent
            parent = getattr(p._meta, "parent_resource", None)

        return urls

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            obj = bundle_or_obj.obj
        else:
            obj = bundle_or_obj

        uri_kwargs = super(ModelResource, self).detail_uri_kwargs(bundle_or_obj)

        parent = getattr(self._meta, "parent_resource", None)
        child = self

        prefix = []

        while parent is not None:
            p = parent()

            prefix.append(child._meta.parent_resource_uri_prefix)

            uri_kwargs.update({
                "__".join(prefix[:] + [p._meta.detail_uri_name]): _get_model_attr(obj, prefix, p._meta.detail_uri_name),
            })

            child = parent
            parent = getattr(p._meta, "parent_resource", None)

        return uri_kwargs

    def full_dehydrate(self, bundle):
        requested = bundle.request.GET.get("fields", "")

        if requested:
            requested = set(requested.split(",")) or set(self.fields.keys())

        # Dehydrate each field.
        for field_name, field_object in self.fields.items():
            if requested and not field_name in requested:
                continue

            # A touch leaky but it makes URI resolution work.
            if getattr(field_object, "dehydrated_type", None) == "related":
                field_object.api_name = self._meta.api_name
                field_object.resource_name = self._meta.resource_name

            bundle.data[field_name] = field_object.dehydrate(bundle)

            # Check for an optional method to do further dehydration.
            method = getattr(self, "dehydrate_%s" % field_name, None)

            if method:
                bundle.data[field_name] = method(bundle)

        bundle = self.dehydrate(bundle)

        return bundle

    def get_via_uri(self, uri, request=None):
        # @@@ Hackish
        uri = urllib.unquote(uri)
        return super(ModelResource, self).get_via_uri(uri, request=request)

    def obj_create(self, bundle, request=None, **kwargs):
        with transaction.commit_on_success():
            bundle = super(ModelResource, self).obj_create(bundle, request=request, **kwargs)

            try:
                self.on_obj_create(bundle.obj, request=request, **kwargs)
            except NotImplementedError:
                pass

        return bundle

    def on_obj_create(self, obj, request=None, **kwargs):
        raise NotImplementedError()

    def obj_update(self, bundle, request=None, skip_errors=False, **kwargs):
        with transaction.commit_on_success():
            # Hack to force lookup
            bundle.obj = self.obj_get(request=request, **kwargs)
            current = bundle.obj

            bundle = super(ModelResource, self).obj_update(bundle, request=request, skip_errors=skip_errors, **kwargs)

            try:
                self.on_obj_update(current, bundle.obj, request=request, **kwargs)
            except NotImplementedError:
                pass

        return bundle

    def on_obj_update(self, old_obj, new_obj, request=None, **kwargs):
        raise NotImplementedError()

    def obj_delete(self, request=None, **kwargs):
        obj = kwargs.pop("_obj", None)

        if obj is None:
            try:
                obj = self.obj_get(request, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")

        kwargs["_obj"] = obj

        with transaction.commit_on_success():
            try:
                self.on_obj_delete(obj, request=request, **kwargs)
            except NotImplementedError:
                pass

            return super(ModelResource, self).obj_delete(request=request, **kwargs)

    def on_obj_delete(self, obj, request=None, **kwargs):
        raise NotImplementedError()

import copy
import json
import urllib

from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource as TastypieModelResource
from tastypie.utils import trailing_slash


__all__ = ["ModelResource"]


class CleanErrors(object):

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            resp = super(CleanErrors, self).wrap_view(view)(request, *args, **kwargs)

            if resp.status_code == 400:
                # @@@ Errors should not assume JSON?
                resp.content = json.dumps({"message": resp.content})
                resp["Content-Type"] = "application/json"

            return resp

        return wrapper

    def is_valid(self, bundle, request=None):
        """
        Handles checking if the data provided by the user is valid.

        Mostly a hook, this uses class assigned to ``validation`` from
        ``Resource._meta``.

        If validation fails, an error is raised with the error messages
        serialized inside it.
        """
        errors = self._meta.validation.is_valid(bundle, request)

        if errors:
            bundle.errors["message"] = "Validation Error"
            bundle.errors["errors"] = [dict(resource=self._meta.resource_name, **e) for e in errors]
            return False

        return True


class ModelResource(CleanErrors, TastypieModelResource):

    def base_urls(self):
        """
        The standard URLs this ``Resource`` should respond to.
        """
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>[^/]+)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

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
            current = copy.copy(bundle.obj)

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

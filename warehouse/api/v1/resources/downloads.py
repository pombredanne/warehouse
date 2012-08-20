import re

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from tastypie import fields
from tastypie.authentication import MultiAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL
from tastypie.exceptions import BadRequest, ImmediateHttpResponse
from tastypie import http
from tastypie.resources import ModelResource, convert_post_to_patch
from tastypie.utils import dict_strip_unicode_keys

from warehouse.api.authentication import BasicAuthentication
from warehouse.api.serializers import Serializer
from warehouse.models import Download, UserAgent, VersionFile


__all__ = ["DownloadResource"]


_package_to_requirement = re.compile(r"^(.*?)-(dev|\d.*)")


class DownloadResource(ModelResource):

    user_agent = fields.CharField()

    class Meta:
        resource_name = "downloads"

        queryset = Download.objects.all()

        filtering = {
            "project": ALL,
            "version": ALL,
            "filename": ALL,
            "date": ALL,
            "user_agent": ALL,
        }

        authentication = MultiAuthentication(BasicAuthentication())
        authorization = DjangoAuthorization()

        list_allowed_methods = ["get", "post", "patch"]
        detail_allowed_methods = ["get", "put"]

        cache_control = {"public": True, "max_age": 60, "s_maxage": 60}

        serializer = Serializer(formats=["json", "jsonp"])

    def dehydrate_user_agent(self, bundle):
        return bundle.obj.user_agent.agent

    def hydrate_version(self, bundle):
        try:
            version_file = VersionFile.objects.filter(version__project__name=bundle.data["project"], filename=bundle.data["filename"]).get()
        except VersionFile.DoesNotExist:
            if "filename" in bundle.data:
                del bundle.data["filename"]

            return bundle
        else:
            bundle.data["version"] = version_file.version.version

        return bundle

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        user_agent = filters.pop("user_agent", None)

        orm_filters = super(DownloadResource, self).build_filters(filters)

        if user_agent is not None:
            orm_filters["user_agent__agent"] = user_agent[0]

        return orm_filters

    def save_related(self, bundle):
        agent = bundle.data.get("user_agent", None)

        if agent is not None:
            user_agent, _ = UserAgent.objects.get_or_create(agent=agent)
            bundle.obj.user_agent = user_agent

        return super(DownloadResource, self).save_related(bundle)

    def patch_list(self, request, **kwargs):
        request = convert_post_to_patch(request)
        deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get("CONTENT_TYPE", "application/json"))

        if "objects" not in deserialized:
            raise BadRequest("Invalid data sent.")

        if len(deserialized["objects"]) and "put" not in self._meta.detail_allowed_methods:
            raise ImmediateHttpResponse(response=http.HttpMethodNotAllowed())

        for data in deserialized["objects"]:
            # Assume the object exists until told otherwise
            try:
                lookup_kwargs = {}
                for k, v in data.items():
                    if k in ["project", "filename"]:
                        lookup_kwargs[k] = v
                    elif k in ["user_agent"]:
                        lookup_kwargs["user_agent__agent"] = v
                    elif k in ["date"]:
                        year, month, day = [int(x) for x in v.split("-")]
                        lookup_kwargs["date__year"] = year
                        lookup_kwargs["date__month"] = month
                        lookup_kwargs["date__day"] = day

                obj = self.obj_get(request=request, **lookup_kwargs)

                # The object does exist, so this is an update-in-place.
                bundle = self.build_bundle(obj=obj, request=request)
                bundle = self.full_dehydrate(bundle)
                bundle = self.alter_detail_data_to_serialize(request, bundle)
                self.update_in_place(request, bundle, data)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # The object referenced by resource_uri doesn't exist,
                # so this is a create-by-PUT equivalent.
                data = self.alter_deserialized_detail_data(request, data)
                bundle = self.build_bundle(data=dict_strip_unicode_keys(data), request=request)
                self.obj_create(bundle, request=request)

        return http.HttpAccepted()

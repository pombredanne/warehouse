import re

from tastypie.authentication import MultiAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL
from tastypie import fields
from tastypie.resources import ModelResource

from warehouse.api.authentication import BasicAuthentication
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

        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get"]

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

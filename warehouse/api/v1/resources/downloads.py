import re

from tastypie.authentication import MultiAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL
from tastypie import fields
from tastypie.resources import ModelResource

from warehouse.api.authentication import BasicAuthentication
from warehouse.models import Download, UserAgent
from warehouse.utils.paths import splitext


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
        if not bundle.data.get("version"):
            package_name, ext = splitext(bundle.data["filename"])
            matches = _package_to_requirement.search(package_name)

            if matches and matches.group(1) == bundle.data["project"]:
                bundle.data["version"] = matches.group(2)

        return bundle

    def save_related(self, bundle):
        agent = bundle.data.get("user_agent", None)

        if agent is not None:
            user_agent, _ = UserAgent.objects.get_or_create(agent=agent)
            bundle.obj.user_agent = user_agent

        return super(DownloadResource, self).save_related(bundle)

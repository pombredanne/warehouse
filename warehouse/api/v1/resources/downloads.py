from tastypie.authentication import MultiAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL
from tastypie import fields
from tastypie.resources import ModelResource

from warehouse.api.authentication import BasicAuthentication
from warehouse.models import Download


__all__ = ["DownloadResource"]


class DownloadResource(ModelResource):

    user_agent = fields.CharField()

    class Meta:
        resource_name = "downloads"

        queryset = Download.objects.all()

        filtering = {
            "project": ALL,
            "version": ALL,
            "filename": ALL,
            "datetime": ALL,
        }

        authentication = MultiAuthentication(BasicAuthentication())
        authorization = DjangoAuthorization()

        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get"]

    def dehydrate_user_agent(self, bundle):
        return bundle.obj.user_agent.agent

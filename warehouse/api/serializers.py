from django.utils.simplejson import JSONDecodeError

from tastypie.exceptions import BadRequest
from tastypie.serializers import Serializer as TastypieSerializer


__all__ = ["Serializer"]


class Serializer(TastypieSerializer):

    def from_json(self, *args, **kwargs):
        try:
            return super(Serializer, self).from_json(*args, **kwargs)
        except JSONDecodeError:
            raise BadRequest("No JSON object could be decoded")

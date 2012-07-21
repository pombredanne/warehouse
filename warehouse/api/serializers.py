from tastypie.serializers import Serializer as TastypieSerializer
from tastypie.utils import format_datetime


__all__ = ["Serializer"]


class Serializer(TastypieSerializer):

    def format_datetime(self, data):
        """
        A hook to control how datetimes are formatted.

        Can be overridden at the ``Serializer`` level (``datetime_formatting``)
        or globally (via ``settings.TASTYPIE_DATETIME_FORMATTING``).

        Default is ``iso-8601``, which looks like "2010-12-16T03:02:14+00:00".
        """
        data = data
        if self.datetime_formatting == "rfc-2822":
            return format_datetime(data)

        return data.isoformat()

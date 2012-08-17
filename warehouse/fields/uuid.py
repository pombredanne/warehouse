from __future__ import absolute_import

import psycopg2.extras
import uuid

from django.db import models

from south.modelsinspector import add_introspection_rules

# Register the adapter so we can use UUID objects.
psycopg2.extras.register_uuid()


class UUIDField(models.CharField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 36
        kwargs.setdefault("default", uuid.uuid4)
        kwargs.setdefault("editable", not kwargs.get("primary_key", False))

        super(UUIDField, self).__init__(*args, **kwargs)

    def db_type(self):
        return "uuid"

    def get_db_prep_value(self, value):
        return self.to_python(value)

    def to_python(self, value):
        if not value:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value


add_introspection_rules([], ["^warehouse\.fields\.uuid\.UUIDField"])

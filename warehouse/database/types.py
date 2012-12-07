from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from sqlalchemy import types


__all__ = ["CIText"]


class CIText(types.UserDefinedType):

    def get_col_spec(self):
        return "CITEXT"

    def bind_processor(self, dialect):
        def process(value):
            return value
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return value
        return process

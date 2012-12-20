from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from sqlalchemy import event, schema

from warehouse import db


class TableDDL(schema.SchemaItem):

    def __init__(self, ddl):
        self.ddl = ddl
        self.parent = None

    def _set_parent(self, table):
        self.parent = table
        event.listen(self.parent, "after_create", db.DDL(self.ddl))

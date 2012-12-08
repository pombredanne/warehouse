from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from sqlalchemy.schema import FetchedValue
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declared_attr

from warehouse import db
from warehouse.database.mixins import UUIDPrimaryKeyMixin, TimeStampedMixin
from warehouse.database.schema import TableDDL
from warehouse.database.types import CIText
from warehouse.database.utils import table_args


class Project(UUIDPrimaryKeyMixin, TimeStampedMixin, db.Model):

    __tablename__ = "projects"
    __table_args__ = declared_attr(table_args((
        TableDDL("""
            CREATE OR REPLACE FUNCTION normalize_name()
            RETURNS trigger AS $$
            BEGIN
                NEW.normalized = lower(regexp_replace(new.name, '[^A-Za-z0-9.]+', '-'));
                return NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER %(table)s_normalize_name
            BEFORE INSERT OR UPDATE
            ON %(table)s
            FOR EACH ROW
            EXECUTE PROCEDURE normalize_name();
        """),
    )))

    name = db.Column(CIText, unique=True, nullable=False)
    normalized = db.Column(CIText, unique=True, nullable=False,
                                    server_default=FetchedValue(),
                                    server_onupdate=FetchedValue())

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Project: {name}>".format(name=self.name)

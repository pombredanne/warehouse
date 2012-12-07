from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from sqlalchemy import event
from sqlalchemy.schema import FetchedValue
from sqlalchemy.dialects import postgresql as pg

from warehouse import db
from warehouse.databases.mixins import UUIDPrimaryKeyMixin
from warehouse.database.types import CIText


class Project(UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "projects"

    name = db.Column(CIText, unique=True, nullable=False)
    normalized = db.Column(CIText, unique=True, nullable=False,
                                    server_default=FetchedValue(),
                                    server_onupdate=FetchedValue())

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Project: {name}>".format(name=self.name)


# Create the Trigger to fill in normalized (TODO: Move this to Alembic?)
event.listen(Project.__table__, "after_create", db.DDL("""
CREATE OR REPLACE FUNCTION normalize_name() RETURNS trigger AS
$body$
BEGIN
    new.normalized = lower(regexp_replace(new.name, '[^A-Za-z0-9.]+', '-'));
    RETURN new;
end;
$body$ LANGUAGE plpgsql;

CREATE TRIGGER %(table)s_normalize_name
BEFORE INSERT OR UPDATE
ON %(table)s
FOR EACH ROW
EXECUTE PROCEDURE normalize_name();
"""))

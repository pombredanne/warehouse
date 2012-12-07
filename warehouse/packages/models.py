from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from sqlalchemy import event
from sqlalchemy.schema import FetchedValue
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.sql.expression import text

from warehouse import db
from warehouse.database.types import CIText


class Project(db.Model):
    id = db.Column(pg.UUID(as_uuid=True),
            primary_key=True, server_default=text("uuid_generate_v4()"))
    name = db.Column(CIText, unique=True, nullable=False)
    normalized = db.Column(CIText, FetchedValue(), unique=True, nullable=False)

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

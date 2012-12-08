from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.schema import FetchedValue
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import text

from warehouse import db
from warehouse.database.schema import TableDDL


class UUIDPrimaryKeyMixin(object):

    id = db.Column(pg.UUID(as_uuid=True),
                   primary_key=True, server_default=text("uuid_generate_v4()"))


class TimeStampedMixin(object):

    __table_args__ = (
        TableDDL("""
            CREATE OR REPLACE FUNCTION update_modified_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.modified = now();
                RETURN NEW;
            END;
            $$ LANGUAGE 'plpgsql';

            CREATE TRIGGER update_%(table)s_modtime
            BEFORE UPDATE
            ON %(table)s
            FOR EACH ROW
            EXECUTE PROCEDURE update_modified_column();
        """),
    )

    created = db.Column(db.DateTime, nullable=False, server_default=func.now())
    modified = db.Column(db.DateTime, nullable=False,
                         server_default=func.now(),
                         server_onupdate=FetchedValue())

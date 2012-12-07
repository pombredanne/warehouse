from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.sql.expression import text

from warehouse import db


class UUIDPrimaryKeyMixin(object):

    id = db.Column(pg.UUID(as_uuid=True),
            primary_key=True, server_default=text("uuid_generate_v4()"))

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from sqlalchemy.schema import FetchedValue
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from warehouse import db
from warehouse.database.mixins import UUIDPrimaryKeyMixin, TimeStampedMixin
from warehouse.database.schema import TableDDL
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

    name = db.Column(db.UnicodeText, unique=True, nullable=False)
    normalized = db.Column(db.UnicodeText, unique=True, nullable=False,
                           server_default=FetchedValue(),
                           server_onupdate=FetchedValue())

    versions = relationship("Version", backref="project")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Project: {name}>".format(name=self.name)


class Version(UUIDPrimaryKeyMixin, TimeStampedMixin, db.Model):

    __tablename__ = "versions"
    __table_args__ = declared_attr(table_args((
        db.Index("idx_project_version", "project_id", "version", unique=True),
    )))

    project_id = db.Column(pg.UUID(as_uuid=True),
                           db.ForeignKey("projects.id", ondelete="RESTRICT"),
                           nullable=False)
    version = db.Column(db.UnicodeText, nullable=False)

    summary = db.Column(db.UnicodeText, nullable=False, server_default="")
    description = db.Column(db.UnicodeText, nullable=False, server_default="")

    keywords = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                         nullable=False, server_default="{}")

    author = db.Column(db.UnicodeText, nullable=False, server_default="")
    author_email = db.Column(db.UnicodeText, nullable=False, server_default="")

    maintainer = db.Column(db.UnicodeText, nullable=False, server_default="")
    maintainer_email = db.Column(db.UnicodeText, nullable=False,
                                 server_default="")

    license = db.Column(db.UnicodeText, nullable=False, server_default="")

    # URIs
    uris = db.Column(pg.HSTORE, nullable=False,
                     server_default=text("''::hstore"))

    # Requirements
    requires_python = db.Column(db.UnicodeText, nullable=False,
                                server_default="")
    requires_external = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                                  nullable=False, server_default="{}")

    def __repr__(self):
        ctx = {"name": self.project.name, "version": self.version}
        return "<Version: {name} {version}>".format(**ctx)

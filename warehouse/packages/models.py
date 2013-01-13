from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import urlparse

import flask

from sqlalchemy.event import listen
from sqlalchemy.schema import FetchedValue
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import text

from warehouse import db
from warehouse.database.mixins import UUIDPrimaryKeyMixin, TimeStampedMixin
from warehouse.database.schema import TableDDL
from warehouse.database.types import Enum
from warehouse.database.utils import table_args
from warehouse.utils import get_storage


_normalize_regex = re.compile(r"[^A-Za-z0-9.]+")


classifiers = db.Table("version_classifiers",  # pylint: disable=C0103
    db.Column("classifier_id",
        pg.UUID(as_uuid=True),
        db.ForeignKey("classifiers.id",
            onupdate="CASCADE",
            ondelete="CASCADE"
        ),
        primary_key=True,
    ),
    db.Column("version_id",
        pg.UUID(as_uuid=True),
        db.ForeignKey("versions.id",
            onupdate="CASCADE",
            ondelete="CASCADE"
        ),
        primary_key=True,
    ),
)


class Classifier(UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "classifiers"

    trove = db.Column(db.UnicodeText, unique=True, nullable=False)

    def __init__(self, trove):
        self.trove = trove

    def __repr__(self):
        return "<Classifier: {trove}>".format(trove=self.trove)

    @classmethod
    def get_or_create(cls, trove):
        try:
            obj = cls.query.filter_by(trove=trove).one()
        except NoResultFound:
            obj = cls(trove)
        return obj


class Project(UUIDPrimaryKeyMixin, TimeStampedMixin, db.Model):

    __tablename__ = "projects"
    __table_args__ = declared_attr(table_args((
        TableDDL("""
            CREATE OR REPLACE FUNCTION normalize_name()
            RETURNS trigger AS $$
            BEGIN
                NEW.normalized = lower(
                        regexp_replace(new.name, '[^A-Za-z0-9.]+', '-', 'g'));
                return NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER %(table)s_normalize_name
            BEFORE INSERT OR UPDATE
            ON %(table)s
            FOR EACH ROW
            EXECUTE PROCEDURE normalize_name();
        """),
        TableDDL("""
            CREATE CONSTRAINT TRIGGER cannot_unyank_projects
                AFTER UPDATE OF yanked ON projects
                FOR EACH ROW
                WHEN (OLD.yanked = TRUE AND NEW.yanked = FALSE)
                EXECUTE PROCEDURE cannot_unyank();
        """),
    )))

    yanked = db.Column(db.Boolean,
                nullable=False,
                server_default=text("FALSE")
            )

    name = db.Column(db.UnicodeText, unique=True, nullable=False)
    normalized = db.Column(db.UnicodeText,
                    unique=True,
                    nullable=False,
                    server_default=FetchedValue(),
                    server_onupdate=FetchedValue()
                )

    versions = relationship("Version",
                    cascade="all,delete,delete-orphan",
                    backref="project",
                )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Project: {name}>".format(name=self.name)

    @classmethod
    def get(cls, name):
        normalized = _normalize_regex.sub("-", name).lower()
        return cls.query.filter_by(normalized=normalized).one()

    @classmethod
    def yank(cls, name, synchronize=None):
        kwargs = {}
        if synchronize:
            kwargs["synchronize_session"] = synchronize

        cls.query.filter_by(name=name).update({"yanked": True}, **kwargs)

    def rename(self, name):
        self.name = name
        self.normalized = _normalize_regex.sub("-", name).lower()
        return self


class Version(UUIDPrimaryKeyMixin, TimeStampedMixin, db.Model):

    __tablename__ = "versions"
    __table_args__ = declared_attr(table_args((
        db.Index("idx_project_version", "project_id", "version", unique=True),
        TableDDL("""
            CREATE OR REPLACE RULE yank_versions_from_projects
                AS ON UPDATE TO projects
                WHERE NEW.yanked = TRUE
                DO ALSO
                    UPDATE versions SET yanked = TRUE
                        WHERE project_id = NEW.id;
        """),
        TableDDL("""
            CREATE CONSTRAINT TRIGGER cannot_unyank_versions
                AFTER UPDATE OF yanked ON versions
                FOR EACH ROW
                WHEN (OLD.yanked = TRUE AND NEW.yanked = FALSE)
                EXECUTE PROCEDURE cannot_unyank();
        """),
        TableDDL("""
            CREATE OR REPLACE FUNCTION update_projects_created_from_versions()
            RETURNS trigger as $$
            BEGIN
                UPDATE projects
                SET created = NEW.created
                WHERE id = NEW.project_id AND created > NEW.created;

                return NULL;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER %(table)s_insert_projects_created
            AFTER INSERT
            ON %(table)s
            FOR EACH ROW
            EXECUTE PROCEDURE update_projects_created_from_versions();

            CREATE TRIGGER %(table)s_update_projects_created
            AFTER UPDATE OF created
            ON %(table)s
            FOR EACH ROW
            WHEN (NEW.created < OLD.created)
            EXECUTE PROCEDURE update_projects_created_from_versions();
        """),
    )))

    yanked = db.Column(db.Boolean,
                nullable=False,
                server_default=text("FALSE")
            )

    project_id = db.Column(pg.UUID(as_uuid=True),
                    db.ForeignKey("projects.id", ondelete="CASCADE"),
                    nullable=False
                )
    version = db.Column(db.UnicodeText, nullable=False)

    summary = db.Column(db.UnicodeText, nullable=False, server_default="")
    description = db.Column(db.UnicodeText, nullable=False, server_default="")

    keywords = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                    nullable=False,
                    server_default="{}"
                )

    author = db.Column(db.UnicodeText, nullable=False, server_default="")
    author_email = db.Column(db.UnicodeText, nullable=False, server_default="")

    maintainer = db.Column(db.UnicodeText, nullable=False, server_default="")
    maintainer_email = db.Column(db.UnicodeText,
                            nullable=False,
                            server_default=""
                        )

    license = db.Column(db.UnicodeText, nullable=False, server_default="")

    # URIs
    uris = db.Column(MutableDict.as_mutable(pg.HSTORE),
                nullable=False,
                server_default=text("''::hstore")
            )
    download_uri = db.Column(db.UnicodeText, nullable=False, server_default="")

    # Requirements
    requires_python = db.Column(db.UnicodeText,
                            nullable=False,
                            server_default=""
                        )
    requires_external = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                            nullable=False,
                            server_default="{}"
                        )
    requirements = relationship("Requirement",
                cascade="all,delete,delete-orphan",
                backref="version",
                lazy="joined",
            )
    provides = relationship("Provide",
                cascade="all,delete,delete-orphan",
                backref="version",
                lazy="joined",
            )
    obsoletes = relationship("Obsolete",
                cascade="all,delete,delete-orphan",
                backref="version",
                lazy="joined",
            )
    requires_old = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                        nullable=False,
                        server_default="{}",
                    )
    provides_old = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                        nullable=False,
                        server_default="{}",
                    )
    obsoletes_old = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                        nullable=False,
                        server_default="{}",
                    )

    # Classifiers
    _classifiers = relationship("Classifier",
                        secondary=classifiers,
                        backref=db.backref("versions", lazy='dynamic')
                    )
    classifiers = association_proxy("_classifiers", "trove",
                        creator=Classifier.get_or_create
                    )
    files = relationship("File",
                cascade="all,delete,delete-orphan",
                backref="version",
            )

    def __repr__(self):
        ctx = {"name": self.project.name, "version": self.version}
        return "<Version: {name} {version}>".format(**ctx)


class Requirement(UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "requires"

    version_id = db.Column(pg.UUID(as_uuid=True),
                        db.ForeignKey("versions.id", ondelete="CASCADE"),
                        nullable=False
                    )

    name = db.Column(db.UnicodeText, nullable=False)
    versions = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                    nullable=False,
                    server_default="{}"
                )
    environment = db.Column(db.UnicodeText, nullable=False, server_default="")
    approximate = db.Column(db.Boolean,
                    nullable=False,
                    server_default=text("FALSE"),
                )


class Provide(UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "provides"

    version_id = db.Column(pg.UUID(as_uuid=True),
                        db.ForeignKey("versions.id", ondelete="CASCADE"),
                        nullable=False
                    )

    name = db.Column(db.UnicodeText, nullable=False)
    versions = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                    nullable=False,
                    server_default="{}"
                )
    environment = db.Column(db.UnicodeText, nullable=False, server_default="")


class Obsolete(UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "obsoletes"

    version_id = db.Column(pg.UUID(as_uuid=True),
                        db.ForeignKey("versions.id", ondelete="CASCADE"),
                        nullable=False
                    )

    name = db.Column(db.UnicodeText, nullable=False)
    versions = db.Column(pg.ARRAY(db.UnicodeText, dimensions=1),
                    nullable=False,
                    server_default="{}"
                )
    environment = db.Column(db.UnicodeText, nullable=False, server_default="")


class FileType(Enum):
    source = "sdist", "Source"
    egg = "bdist_egg", "Egg"
    msi = "bdist_msi", "MSI"
    dmg = "bdist_dmg", "DMG"
    rpm = "bdist_rpm", "RPM",
    dumb = "bdist_dumb", "Dumb Binary Distribution"
    windows_installer = "bdist_wininst", "Windows Installer"
    wheel = "bdist_wheel", "Wheel"


class File(UUIDPrimaryKeyMixin, TimeStampedMixin, db.Model):

    __tablename__ = "files"
    __table_args__ = declared_attr(table_args((
        TableDDL("""
            CREATE OR REPLACE RULE yank_files_from_versions
                AS ON UPDATE TO versions
                WHERE NEW.yanked = TRUE
                DO ALSO
                    UPDATE files SET yanked = TRUE WHERE version_id = NEW.id;
        """),
        TableDDL("""
            CREATE CONSTRAINT TRIGGER cannot_unyank_files
                AFTER UPDATE OF yanked ON files
                FOR EACH ROW
                WHEN (OLD.yanked = TRUE AND NEW.yanked = FALSE)
                EXECUTE PROCEDURE cannot_unyank();
        """),
        TableDDL("""
            CREATE OR REPLACE FUNCTION update_versions_created_from_files()
            RETURNS trigger as $$
            BEGIN
                UPDATE versions
                SET created = NEW.created
                WHERE id = NEW.version_id AND created > NEW.created;

                return NULL;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER %(table)s_insert_version_created
            AFTER INSERT
            ON %(table)s
            FOR EACH ROW
            EXECUTE PROCEDURE update_versions_created_from_files();

            CREATE TRIGGER %(table)s_update_version_created
            AFTER UPDATE OF created
            ON %(table)s
            FOR EACH ROW
            WHEN (NEW.created < OLD.created)
            EXECUTE PROCEDURE update_versions_created_from_files();
        """),
    )))

    yanked = db.Column(db.Boolean,
                nullable=False,
                server_default=text("FALSE")
            )

    version_id = db.Column(pg.UUID(as_uuid=True),
                        db.ForeignKey("versions.id", ondelete="CASCADE"),
                        nullable=False
                    )

    file = db.Column(db.UnicodeText, nullable=False, unique=True)

    filename = db.Column(db.UnicodeText, nullable=False, unique=True)
    filesize = db.Column(db.Integer, nullable=False)

    type = db.Column(FileType.db_type(), nullable=False)

    python_version = db.Column(db.UnicodeText,
                        nullable=False,
                        server_default=""
                    )

    comment = db.Column(db.UnicodeText, nullable=False, server_default="")

    hashes = db.Column(MutableDict.as_mutable(pg.HSTORE),
                    nullable=False,
                    server_default=text("''::hstore")
                )

    @property
    def uri(self):
        storage = get_storage()
        return storage.url(self.file)

    @property
    def hashed_uri(self):
        algorithm = flask.current_app.config.get("FILE_URI_HASH")
        digest = self.hashes.get(algorithm)

        if algorithm is not None and digest is not None:
            parsed = urlparse.urlparse(self.uri)
            fragment = "=".join([algorithm, digest])
            return urlparse.urlunparse(parsed[:5] + (fragment,))
        else:
            return self.uri


listen(db.metadata, "before_create",
    db.DDL("""
        CREATE OR REPLACE FUNCTION cannot_unyank()
            RETURNS trigger AS $$
            BEGIN
                -- Check if unyanking is being attempted
                IF OLD.yanked = TRUE AND NEW.yanked = FALSE THEN
                    RAISE EXCEPTION '%% cannot be unyanked.', TG_TABLE_NAME;
                END IF;

                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
    """)
)

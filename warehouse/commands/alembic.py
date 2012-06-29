from __future__ import absolute_import

from alembic import command
from alembic.config import Config
from flask.ext.script import Command, Option

from warehouse.core import app
from warehouse.commands import manager


class AlembicMixin(object):

    def get_config(self):
        if not hasattr(self, "_config"):
            self._config = Config()
            self._config.set_main_option("script_location", "warehouse:migrations")
            self._config.set_main_option("url", app.config["SQLALCHEMY_DATABASE_URI"])
        return self._config


class Migration(AlembicMixin, Command):
    """
    Creates a new Alembic Migration.
    """

    option_list = (
        Option(dest="message", help="Message string to use with 'revision'"),
        Option(
            "--autogenerate", "-a",
            action="store_true", dest="autogenerate",
            help="Populate revision script with candidate migration operations, based on comparison of database to model."
        ),
    )

    def run(self, message=None, autogenerate=None):
        cfg = self.get_config()
        command.revision(cfg, message=message, autogenerate=autogenerate)


class Upgrade(AlembicMixin, Command):
    """
    Upgrades the database.
    """

    option_list = (
        Option(dest="revision", help="Specific revision to upgrade to", nargs="?", default="head"),
        Option(
            "--sql",
            action="store_true", dest="sql",
            help="Don't emit SQL to database - dump to standard output/file instead"
        ),
    )

    def run(self, revision, sql=None):
        cfg = self.get_config()
        command.upgrade(cfg, revision=revision, sql=sql)


class Downgrade(AlembicMixin, Command):
    """
    Downgrades the database.
    """

    option_list = (
        Option(dest="revision", help="Specific revision to upgrade to", nargs="?", default=None),
        Option(
            "--sql",
            action="store_true", dest="sql",
            help="Don't emit SQL to database - dump to standard output/file instead"
        ),
    )

    def run(self, revision, sql=None):
        cfg = self.get_config()
        command.downgrade(cfg, revision=revision, sql=sql)


manager.add_command("migration", Migration())
manager.add_command("upgrade", Upgrade())
manager.add_command("downgrade", Downgrade())

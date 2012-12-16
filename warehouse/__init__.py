from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import importlib
import logging
import os

from flask import Flask

from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy


__all__ = ["__version__", "create_app", "db", "script"]

# - Meta Information -
__version__ = "0.1dev1"
# - End Meta Information -

MODULES = [
    {"name": "packages"},
    {"name": "synchronize", "models": False, "commands": True},
    {"name": "simple", "models": False, "views": True},
]

logger = logging.getLogger("warehouse")

db = SQLAlchemy()


def create_app(config=None):
    # Create the Flask Application
    app = Flask("warehouse")

    # Load Configuration
    logger.debug("Loading configuration")

    app.config.from_object("warehouse.defaults")

    if "WAREHOUSE_CONF" in os.environ:
        app.config.from_envvar("WAREHOUSE_CONF")

    if config:
        app.config.from_pyfile(config)

    # Initialize Extensions
    logger.debug("Initializing extensions")

    db.init_app(app)

    # Load Modules
    logger.debug("Loading modules")

    for module in MODULES:
        # Load Models
        if module.get("models", True):
            logger.debug("Loading models for %s", module["name"])
            importlib.import_module("warehouse.%(name)s.models" % module)

        # Load views
        if module.get("views", False):
            logger.debug("Loading views for %s", module["name"])
            mod = importlib.import_module("warehouse.%(name)s.views" % module)

            for blueprint in mod.BLUEPRINTS:
                app.register_blueprint(blueprint)

    return app

script = Manager(create_app)
script.add_option("-c", "--config", dest="config", required=False)

for module in MODULES:
    # Load commands
    if module.get("commands"):
        logger.debug("Loading commands for %s", module["name"])
        importlib.import_module("warehouse.%(name)s.commands" % module)

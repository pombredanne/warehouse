from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import importlib
import logging
import os

from flask import Flask

from flask.ext.redistore import Redistore  # pylint: disable=E0611,F0401
from flask.ext.script import Manager  # pylint: disable=E0611,F0401
from flask.ext.sqlalchemy import SQLAlchemy  # pylint: disable=E0611,F0401

from warehouse import __about__


__all__ = ["create_app", "db", "script"] + __about__.__all__


# - Meta Information -
# This is pretty ugly
for attr in __about__.__all__:
    if hasattr(__about__, attr):
        globals()[attr] = getattr(__about__, attr)
# - End Meta Information -

MODULES = [
    {"name": "packages", "models": True},
    {"name": "synchronize", "commands": True},
    {"name": "simple", "views": True},
]

logger = logging.getLogger("warehouse")
logger.addHandler(logging.NullHandler())

db = SQLAlchemy(session_options={"autoflush": True})
redis = Redistore()


def create_app(config=None):
    # Create the Flask Application
    app = Flask("warehouse")

    # Load Configuration
    logger.debug("Loading configuration from 'warehouse.defaults'")
    app.config.from_object("warehouse.defaults")

    if "WAREHOUSE_CONF" in os.environ:
        logger.debug(
            "Loading configuration from '%s' via $WAREHOUSE_CONF",
            os.environ["WAREHOUSE_CONF"],
        )
        app.config.from_envvar("WAREHOUSE_CONF")

    if config:
        logger.debug("Loading configuration from '%s' via -c/--config", config)
        app.config.from_pyfile(config)

    # Initialize the database
    logger.debug("Initialize the PostgreSQL database object")
    db.init_app(app)

    # Initialize Redis
    logger.debug("Initialize the Redis database object")
    redis.init_app(app)

    for module in MODULES:  # pylint: disable=W0621
        # Load Models
        if module.get("models"):
            logger.debug("Loading models for %s", module["name"])
            importlib.import_module("warehouse.%(name)s.models" % module)

        # Load views
        if module.get("views"):
            logger.debug("Loading blueprints for %s", module["name"])
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

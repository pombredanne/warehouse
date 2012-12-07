import logging
import os

from flask import Flask

from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy


__all__ = ["create_app", "db", "script"]

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

    return app

script = Manager(create_app)
script.add_option("-c", "--config", dest="config", required=False)

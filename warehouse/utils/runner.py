#!/usr/bin/env python
from logan.runner import run_app

import base64
import os

KEY_LENGTH = 40

CONFIG_TEMPLATE = """# Warehouse Configuration
import os.path

CONF_ROOT = os.path.dirname(__file__)

DATABASES = {
    "default": {
        # You can swap out the engine for MySQL easily by changing this value
        # to ``django.db.backends.mysql`` or to PostgreSQL with
        # ``django.db.backends.postgresql_psycopg2``
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(CONF_ROOT, "warehouse.db"),
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

SECRET_KEY = %(default_key)r

# Mail server configuration

# For more information check Django's documentation:
#  https://docs.djangoproject.com/en/1.3/topics/email/?from=olddocs#e-mail-backends

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "localhost"
EMAIL_HOST_PASSWORD = ""
EMAIL_HOST_USER = ""
EMAIL_PORT = 25
EMAIL_USE_TLS = False
"""


def generate_settings():
    """
    This command is run when ``default_path`` doesn't exist, or ``init`` is
    run and returns a string representing the default data to put into their
    settings file.
    """
    output = CONFIG_TEMPLATE % dict(
        default_key=base64.b64encode(os.urandom(KEY_LENGTH)),
    )

    return output


def main():
    run_app(
        project="warehouse",
        default_config_path="~/.warehouse/warehouse.conf.py",
        default_settings="warehouse.settings.server",
        settings_initializer=generate_settings,
        settings_envvar="WAREHOUSE_CONF",
    )

if __name__ == "__main__":
    main()

from warehouse.settings.server import *

DATABASES = {
    "default": {
        "ENGINE": "django_hstore.postgresql_psycopg2",
        "NAME": "warehouse",
    }
}

SOUTH_DATABASE_ADAPTERS = {
    "default": "south.db.postgresql_psycopg2",
}

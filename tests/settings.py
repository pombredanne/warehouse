from warehouse.settings.base import ApiSettings


class Tests(ApiSettings):

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "warehouse",
        }
    }

import os
import os.path

from configurations import Settings


class BaseSettings(Settings):
    PROJECT_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)

    DEBUG = False
    TEMPLATE_DEBUG = True

    ADMINS = []
    MANAGERS = ADMINS

    INTERNAL_IPS = [
        "127.0.0.1",
    ]

    APPEND_SLASH = True

    SOUTH_DATABASE_ADAPTERS = {}

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }

    SITE_ID = 1

    # Local time zone for this installation. Choices can be found here:
    # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
    # although not all choices may be available on all operating systems.
    # On Unix systems, a value of None will cause Django to use the same
    # timezone as the operating system.
    # If running in a Windows environment this must be set to the same as your
    # system time zone.
    TIME_ZONE = "UTC"

    # Language code for this installation. All choices can be found here:
    # http://www.i18nguy.com/unicode/language-identifiers.html
    LANGUAGE_CODE = "en"

    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    USE_I18N = False

    # If you set this to False, Django will not format dates, numbers and
    # calendars according to the current locale
    USE_L10N = False

    # If you set this to False, Django will not use timezone-aware datetimes.
    USE_TZ = True

    MIDDLEWARE_CLASSES = [
        "django.middleware.gzip.GZipMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.http.ConditionalGetMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ]

    # List of callables that know how to import templates from various sources.
    TEMPLATE_LOADERS = [
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]

    TEMPLATE_DIRS = [
        os.path.join(PROJECT_ROOT, "templates"),
    ]

    APPS = [
        "django.contrib.auth",
        "django.contrib.contenttypes",

        # External
        "haystack",
        "json_field",
        "south",
        "tastypie",

        # Internal
        "warehouse",
    ]

    EMAIL_SUBJECT_PREFIX = "[Warehouse] "

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "console": {
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s]  %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },

        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "console",
            },
        },

        "root": {
            "handlers": ["console"],
            "level": "DEBUG",
        },

        "loggers": {
            "requests.packages.urllib3": {
                "handlers": [],
                "propagate": False,
            },
        },
    }

    HAYSTACK_CONNECTIONS = {
        "default": {
            "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
        },
    }

    def __init__(self):
        # These settings must be set or bad things happens

        for key in self.DATABASES:
            # Ensure database level autocommit
            options = self.DATABASES[key].get("OPTIONS", {})
            options.update({"autocommit": True})
            self.DATABASES[key]["OPTIONS"] = options

            # Set databases to the HSTORE backend (Postgresql)
            if self.DATABASES[key]["ENGINE"] == "django.db.backends.postgresql_psycopg2":
                self.DATABASES[key]["ENGINE"] = "django_hstore.postgresql_psycopg2"

                # Make sure that South respects the new backend
                self.SOUTH_DATABASE_ADAPTERS[key] = "south.db.postgresql_psycopg2"

    @property
    def INSTALLED_APPS(self):
        if not hasattr(self, "_INSTALLED_APPS"):
            apps = []
            seen = set()

            for klass in self.__class__.mro():
                for app in getattr(klass, "APPS", []):
                    if not app in seen:
                        seen.add(app)
                        apps.append(app)

            self._INSTALLED_APPS = apps

        return self._INSTALLED_APPS


class ApiSettings(BaseSettings):

    ROOT_URLCONF = "warehouse.api.urls"


class AppSettings(BaseSettings):

    ROOT_URLCONF = "warehouse.urls"

    APPS = [
        "django.contrib.admin",
        "django.contrib.sessions",
        "django.contrib.sites",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ]

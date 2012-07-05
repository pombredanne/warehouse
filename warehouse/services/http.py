import sys
import gunicorn

from gunicorn import arbiter
from gunicorn.app import djangoapp

from warehouse.services.base import Service


if gunicorn.version_info < (0, 14, 0):
    def _setup_app(app):
        app.validate()
        app.activate_translation()
else:
    def _setup_app(app):
        import gunicorn.util
        djangoapp.make_default_env(app.cfg)
        djwsgi = gunicorn.util.import_module("gunicorn.app.django_wsgi")
        djwsgi.make_wsgi_application()


class WarehouseApplication(djangoapp.DjangoApplication):

    def __init__(self, options):
        self.usage = None
        self.cfg = None
        self.config_file = options.get("config") or ""
        self.options = options
        self.callable = None
        self.project_path = None

        self.do_load_config()

        for k, v in self.options.items():
            if k.lower() in self.cfg.settings and v is not None:
                self.cfg.set(k.lower(), v)

    def init(self, parser, opts, args):
        pass

    def load(self):
        # application should be imported at first to setup env
        from warehouse.wsgi import application
        _setup_app(self)
        return application


class WarehouseHTTPServer(Service):
    name = "http"

    def __init__(self, host=None, port=None, debug=False):
        from django.conf import settings

        self.host = host or settings.WEB_HOST
        self.port = port or settings.WEB_PORT

        options = {
            "bind": "%s:%s" % (self.host, self.port),
            "debug": debug,
            "daemon": False,
            "timeout": 30,
        }
        options.update(settings.WEB_OPTIONS or {})

        self.app = WarehouseApplication(options)

    def run(self):
        try:
            arbiter.Arbiter(self.app).run()
        except RuntimeError, e:
            sys.stderr.write("\nError: %s\n\n" % e)
            sys.stderr.flush()
            sys.exit(1)

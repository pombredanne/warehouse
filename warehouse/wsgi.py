import os

from configurations.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warehouse.settings.base")
os.environ.setdefault("DJANGO_CONFIGURATION", "WarehouseSettings")

application = get_wsgi_application()

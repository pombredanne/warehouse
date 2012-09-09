import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warehouse.settings.base")
os.environ.setdefault("DJANGO_CONFIGURATION", "WarehouseSettings")

from configurations.wsgi import get_wsgi_application

application = get_wsgi_application()

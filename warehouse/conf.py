from django.conf import settings

from appconf import AppConf


class WarehouseAppConf(AppConf):

    PACKAGE_PATH_HASH = "sha256"

    PACKAGE_STORAGE_CLASS = None
    PACKAGE_STORAGE_OPTIONS = {}

    API_HISTORY = True

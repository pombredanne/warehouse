from django.conf import settings

from appconf import AppConf


class WarehouseAppConf(AppConf):

    PACKAGE_PATH_HASH = "sha256"

    SIMPLE_HASH = "sha256"

    PACKAGE_STORAGE_CLASS = None
    PACKAGE_STORAGE_OPTIONS = {}

    SYNC_USERS = []

    API_HISTORY = True

    ALWAYS_MODIFIED_NOW = True

    DOWNLOAD_SOURCES = {}

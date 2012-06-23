import posixpath
import uuid

from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject

from warehouse.conf import settings


def version_file_upload_path(instance, filename):
    filehash = instance.digests.get(settings.WAREHOUSE_PACKAGE_PATH_HASH, None)

    if filehash is None:
        # There is no stored hash, fake it with a UUID
        filehash = str(uuid.uuid4()).replace("-", "")

    basedir = getattr(settings, "WAREHOUSE_PACKAGE_BASE_DIR", None)

    path_parts = []

    if basedir is not None:
        path_parts.append(basedir)

    path_parts += filehash[:4]
    path_parts += [filehash, filename]

    return posixpath.join(*path_parts)


class ConfiguredStorage(LazyObject):
    def _setup(self):
        storage_class = get_storage_class(settings.WAREHOUSE_PACKAGE_STORAGE_CLASS)
        storage_instance = storage_class(**settings.WAREHOUSE_PACKAGE_STORAGE_OPTIONS)

        self._wrapped = storage_instance


package_storage = ConfiguredStorage()

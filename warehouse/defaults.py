from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# The base domain name for this installation. Used to control linking to
#      sub-domains.
SERVER_NAME = "warehouse.local:5000"

# The URI for our PostgreSQL database.
SQLALCHEMY_DATABASE_URI = "postgres:///warehouse"

# The URI for our Redis database.
REDIS_URI = "redis://localhost:6379/0"

# The type of Storage to use.
STORAGE = "stockpile.filesystem:HashedFileSystem"

# Options to pass into the stockpile storage backend
STORAGE_OPTIONS = {
    "location": "data",
    "hash_algorithm": "md5",
    "base_url": "https://files.warehouse.local:5000/",
}

# What type of hash to use when displaying a hashed uri for files
FILE_URI_HASH = "sha256"

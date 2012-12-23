from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# The base domain name for this installation. Used to control linking to
#      sub-domains.
SERVER_NAME = "warehouse.local"

# The URI for our PostgreSQL database.
SQLALCHEMY_DATABASE_URI = "postgres:///warehouse"

# The URI for our Redis database.
REDIS_URI = "redis://localhost:6379/0"

# The type of Storage to use. Can be either Filesystem or S3.
STORAGE = "Filesystem"

# The hash to use in computing filenames.
#   Allowed values: md5, sha1, sha224, sha256, sha384, sha512, None
STORAGE_HASH = "md5"

# Base directory for storage when using the Filesystem.
STORAGE_DIRECTORY = "data"

# The name of the bucket that files will be stored in when using S3.
# STORAGE_BUCKET = "<storage bucket>"

# The S3 Key used to access S3 when using S3 Storage
# S3_KEY = "<S3 Key>"

# The S3 Secret used to access S# when using S3 Storage
# S3_SECRET = "<S3 Secret>"

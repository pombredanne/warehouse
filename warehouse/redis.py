from __future__ import absolute_imports

import redis
from warehouse.conf import settings

# Redis datastore
datastore = redis.StrictRedis(**{k.lower(): v for k, v in settings.REDIS.items()})

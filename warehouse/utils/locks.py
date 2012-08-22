import time
import redis

from warehouse.conf import settings


class Lock(object):
    def __init__(self, key, expires=60, timeout=10, using="default"):
        """
        Distributed locking using Redis SETNX and GETSET.

        Usage::

            with Lock('my_lock'):
                print "Critical section"

        :param  expires     We consider any existing lock older than
                            ``expires`` seconds to be invalid in order to
                            detect crashed clients. This value must be higher
                            than it takes the critical section to execute.
        :param  timeout     If another client has already obtained the lock,
                            sleep for a maximum of ``timeout`` seconds before
                            giving up. A value of 0 means we never wait.
        :param using        Which of the REDIS databases to use for this lock.
        """

        self.key = key
        self.timeout = timeout
        self.expires = expires
        self.using = using
        self.datastore = redis.StrictRedis(**dict([(k.lower(), v) for k, v in settings.REDIS[self.using].items()]))
        self._expiration = None

    def __enter__(self):
        timeout = self.timeout

        while timeout >= 0:
            self._expiration = time.time() + self.expires + 1

            if self.datastore.setnx(self.key, self._expiration):
                # We gained the lock; enter critical section
                return

            current_value = self.datastore.get(self.key)

            # We found an expired lock and nobody raced us to replacing it
            if current_value and float(current_value) < time.time() and \
                self.datastore.getset(self.key, self._expiration) == current_value:
                    return

            timeout -= 1
            time.sleep(1)

        raise LockTimeout("Timeout whilst waiting for lock")

    def __exit__(self, exc_type, exc_value, traceback):
        if self._expiration is not None:
            if self.datastore.get(self.key) == str(self._expiration):
                self.datastore.delete(self.key)


class LockTimeout(BaseException):
    pass

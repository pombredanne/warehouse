from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class FailedSynchronization(Exception):
    pass


class SynchronizationTimeout(Exception):
    """
    A synchronization for a particular project took longer than the timeout.
    """

class FailedSynchronization(Exception):
    pass


class SynchronizationTimeout(Exception):
    """
    A synchronization for a particular project took longer than the timeout.
    """

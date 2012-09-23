from django.db import DEFAULT_DB_ALIAS

from tastypie.transaction import Transaction

from warehouse.utils.transactions import _TransactionWrapper


class XactTransaction(_TransactionWrapper, Transaction):
    """
    A simple Transaction manager that uses the xact transaction system.
    """

    def __init__(self, using=None):
        if using is None:
            using = DEFAULT_DB_ALIAS

        self.using = using
        self.transaction = None

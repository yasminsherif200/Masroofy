"""
core.dao
========

Sub-package exposing the three Data Access Object (DAO) classes for the
**core** application.

DAOs are the only layer that communicates directly with the database through
Django's ORM.  All other layers (services, views) must go through DAOs to
read or write data, keeping SQL/ORM logic in one place and making it easier
to swap the persistence backend in future.

Importing from this package:

.. code-block:: python

    from core.dao import UserDAO, BudgetDAO, TransactionDAO

Modules
-------
user_dao
    ``UserDAO`` — create-or-update user credentials, retrieve the single
    user record.  See ``core/dao/user_dao.py``.
budget_dao
    ``BudgetDAO`` — save, retrieve, and delete ``BudgetCycle`` records.
    See ``core/dao/budget_dao.py``.
transaction_dao
    ``TransactionDAO`` — insert, query, update, and delete ``Transaction``
    records; compute expense totals.  See ``core/dao/transaction_dao.py``.

Pattern
-------
Each DAO is a plain Python class (no Django ``Model`` inheritance) with
instance methods that wrap ORM calls.  This makes DAOs easy to mock in unit
tests without hitting a real database.
"""

from .user_dao import UserDAO
from .budget_dao import BudgetDAO
from .transaction_dao import TransactionDAO

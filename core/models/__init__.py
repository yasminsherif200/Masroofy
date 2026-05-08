"""
core.models
===========

Sub-package that collects all Django ORM model classes for the **core**
application into a single importable namespace.

The imports below allow any other module to write::

    from core.models import User, BudgetCycle, Transaction

instead of importing from each individual model file.

Models
------
User
    Single-user authentication model storing a display name, a SHA-256
    hashed PIN, and a preferred currency code.  See ``core/models/user.py``.

BudgetCycle
    Represents one budget period with a total allowance, a pre-computed
    daily limit, and start/end dates.  Linked to ``User`` via a foreign key.
    See ``core/models/budget_cycle.py``.

Transaction
    An individual expense (or income) entry linked to a ``BudgetCycle``.
    Stores amount, category, date, description, and creation timestamp.
    See ``core/models/transaction.py``.

Database Schema
---------------
The initial schema for all three models is captured in migration
``core/migrations/0001_initial.py``.
"""

from .user import User
from .budget_cycle import BudgetCycle
from .transaction import Transaction

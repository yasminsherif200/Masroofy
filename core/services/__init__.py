"""
core.services
=============

Sub-package that exposes the three service-layer classes used across the
**core** application.  Each class encapsulates the business logic for one
domain, sitting between the view layer (HTTP concerns) and the DAO layer
(database concerns).

Importing from this package:

.. code-block:: python

    from core.services import UserService, BudgetService, TransactionService

Modules
-------
user_service
    ``UserService`` — PIN hashing, login verification, lockout management,
    and credential/username updates.
budget_service
    ``BudgetService`` — budget cycle creation, balance calculation, daily
    limit derivation, category percentage breakdown, threshold checking,
    and cycle reset.
transaction_service
    ``TransactionService`` — expense validation and persistence, edit/delete
    eligibility checks, transaction filtering, and daily-limit recalculation.

Architecture Note
-----------------
Services depend on DAOs (``core.dao``) and models (``core.models``), but
**never** on views.  This keeps business rules testable in isolation without
an HTTP request context.
"""

from .user_service import UserService
from .budget_service import BudgetService
from .transaction_service import TransactionService

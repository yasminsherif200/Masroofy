"""
core.views
==========

Sub-package that organises all view logic for the **core** application into
one module per functional domain.  Django's URL dispatcher (``core/urls.py``)
imports each sub-module directly, so every view function is reachable without
going through this ``__init__``.

The wildcard imports below re-export every sub-module so that callers can
write either::

    from core.views import login_view          # preferred in urls.py
    from core import views; views.login_view   # also works

Modules
-------
login_view
    Authentication: ``login``, ``signup``, ``logout``.
home_view
    Onboarding and main dashboard: ``setup``, ``dashboard``.
add_expense_view
    Expense entry form: ``add_expense``.
history_view
    Transaction list and CRUD: ``history``, ``delete_transaction``,
    ``edit_transaction``.
settings_view
    User preferences and cycle management: ``settings``, ``reset_cycle``.
reports_view
    Spending analytics: ``reports``.
"""

from . import login_view        # login, signup, logout
from . import home_view         # setup, dashboard
from . import settings_view     # settings, reset_cycle
from . import add_expense_view  # add_expense
from . import history_view      # history, delete_transaction, edit_transaction
from . import reports_view      # reports

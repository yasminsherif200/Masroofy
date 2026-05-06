"""
URL Configuration – core
=========================

Defines all user-facing URL patterns for the **core** application.
This module is included by the root URL conf (``masroofy/urls.py``) under
the empty prefix, so all patterns here are mounted at the site root.

URL Map
-------
+--------------------------------------------+----------------------+---------------------------+
| Path                                       | View callable        | URL name                  |
+============================================+======================+===========================+
| ``/``                                      | login_view.login     | ``login``                 |
+--------------------------------------------+----------------------+---------------------------+
| ``/signup/``                               | login_view.signup    | ``signup``                |
+--------------------------------------------+----------------------+---------------------------+
| ``/logout/``                               | login_view.logout    | ``logout``                |
+--------------------------------------------+----------------------+---------------------------+
| ``/setup/``                                | home_view.setup      | ``setup``                 |
+--------------------------------------------+----------------------+---------------------------+
| ``/dashboard/``                            | home_view.dashboard  | ``dashboard``             |
+--------------------------------------------+----------------------+---------------------------+
| ``/settings/``                             | settings_view.settings| ``settings``             |
+--------------------------------------------+----------------------+---------------------------+
| ``/add-expense/``                          | add_expense_view\    | ``add_expense``           |
|                                            | .add_expense         |                           |
+--------------------------------------------+----------------------+---------------------------+
| ``/reset-cycle/``                          | settings_view\       | ``reset_cycle``           |
|                                            | .reset_cycle         |                           |
+--------------------------------------------+----------------------+---------------------------+
| ``/history/``                              | history_view.history | ``history``               |
+--------------------------------------------+----------------------+---------------------------+
| ``/delete-transaction/<transaction_id>/``  | history_view\        | ``delete_transaction``    |
|                                            | .delete_transaction  |                           |
+--------------------------------------------+----------------------+---------------------------+
| ``/edit-transaction/<transaction_id>/``    | history_view\        | ``edit_transaction``      |
|                                            | .edit_transaction    |                           |
+--------------------------------------------+----------------------+---------------------------+
| ``/reports/``                              | reports_view.reports | ``reports``               |
+--------------------------------------------+----------------------+---------------------------+

Path Converters
---------------
``<int:transaction_id>``
    Captures a positive integer from the URL and passes it as the keyword
    argument ``transaction_id`` to the view.  Used by the delete and edit
    transaction endpoints.

Notes
-----
* Views are imported from sub-modules inside ``core/views/`` rather than
  from a single ``views.py`` file, keeping each view domain (auth, home,
  expenses …) in its own module.
* URL names (the ``name`` parameter) allow reverse resolution with
  ``reverse('login')`` or ``{% url 'dashboard' %}`` in templates.

References
----------
Django URL dispatcher:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from core.views import login_view
from core.views import home_view
from core.views import settings_view
from core.views import add_expense_view
from core.views import history_view
from core.views import reports_view
from django.urls import path

urlpatterns = [
    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    # Landing page / login form  →  GET renders form, POST authenticates
    path('', login_view.login, name='login'),

    # New user registration
    path('signup/', login_view.signup, name='signup'),

    # Clears the user's session and redirects to login
    path('logout/', login_view.logout, name='logout'),

    # ------------------------------------------------------------------
    # Onboarding & Dashboard
    # ------------------------------------------------------------------

    # First-time budget setup wizard (income, cycle dates, currency …)
    path('setup/', home_view.setup, name='setup'),

    # Main dashboard: current cycle summary, spending breakdown, quick actions
    path('dashboard/', home_view.dashboard, name='dashboard'),

    # ------------------------------------------------------------------
    # Expense Management
    # ------------------------------------------------------------------

    # Form to record a new expense or income transaction
    path('add-expense/', add_expense_view.add_expense, name='add_expense'),

    # ------------------------------------------------------------------
    # Transaction History
    # ------------------------------------------------------------------

    # Paginated list of all past transactions for the current user
    path('history/', history_view.history, name='history'),

    # Permanently remove a single transaction identified by its primary key
    path(
        'delete-transaction/<int:transaction_id>/',
        history_view.delete_transaction,
        name='delete_transaction',
    ),

    # Edit an existing transaction identified by its primary key
    path(
        'edit-transaction/<int:transaction_id>/',
        history_view.edit_transaction,
        name='edit_transaction',
    ),

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    # User preferences: currency, notification settings, profile info
    path('settings/', settings_view.settings, name='settings'),

    # Resets the current budget cycle (clears totals, sets a new period)
    path('reset-cycle/', settings_view.reset_cycle, name='reset_cycle'),

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    # Spending analytics: charts, category breakdown, trends over time
    path('reports/', reports_view.reports, name='reports'),
]

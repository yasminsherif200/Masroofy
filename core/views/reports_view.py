"""
Reports View – core.views.reports_view
========================================

Provides the spending-analytics page for the active budget cycle.  The view
aggregates transaction data and budget metrics into a single context object
that the template uses to render a summary table, a category-breakdown table,
and a Chart.js doughnut/bar chart.

Data Sources
------------
``TransactionDAO.getTransactionsByCycle``
    Full list of individual transactions (for the detailed table).
``TransactionDAO.getTotalExpensesByCycle``
    Sum of all expenses in the cycle (scalar value).
``BudgetService.calculateCategoryPercentages``
    Dict of ``{category_name: percentage}`` used for the breakdown table and
    chart labels/data.
``BudgetService.getCurrentBalance``
    Remaining unspent budget for the cycle.

Dependencies
------------
``core.dao.BudgetDAO``
    Retrieves the user's active budget cycle.
``core.dao.TransactionDAO``
    Queries transaction totals and lists.
``core.services.BudgetService``
    Computes category percentages and current balance.

Module-level Singletons
-----------------------
``budget_dao``
    Shared ``BudgetDAO`` instance.
``transaction_dao``
    Shared ``TransactionDAO`` instance.
``budget_service``
    Shared ``BudgetService`` instance.
"""

from django.shortcuts import render, redirect
from core.dao import BudgetDAO, TransactionDAO
from core.services import BudgetService

#: Shared DAO instance for budget cycle lookups.
budget_dao = BudgetDAO()

#: Shared DAO instance for transaction queries and aggregations.
transaction_dao = TransactionDAO()

#: Shared service instance for financial calculations.
budget_service = BudgetService()


def reports(request):
    """
    Render the spending-analytics report for the active budget cycle.

    **GET only** – Collects all relevant financial data for the current cycle
    and passes it to ``core/reports.html``, which renders:

    * A summary grid (total budget, total spent, remaining balance).
    * A category-breakdown table (category name → % of spending).
    * A Chart.js chart (labels and values encoded on a ``<canvas>`` element
      and rendered by ``core/js/charts.js``).
    * A print button (``window.print()``).

    Authentication
    --------------
    Redirects to ``'login'`` if ``request.session['user_id']`` is absent.
    Redirects to ``'setup'`` if no active budget cycle exists.

    Parameters
    ----------
    request : django.http.HttpRequest

    Returns
    -------
    django.http.HttpResponse
        Rendered ``core/reports.html`` or a redirect response.

    Template context
    ----------------
    ``transactions`` : QuerySet / list
        All transactions in the active cycle (used for the detailed table).
    ``total_spent`` : float
        Sum of all expenses in the cycle, rounded to 2 decimal places.
    ``category_data`` : dict[str, float]
        Category name → percentage of total spending.  Passed to both the
        HTML table and the ``<canvas>`` ``data-*`` attributes for Chart.js.
    ``balance`` : float
        Remaining unspent budget, rounded to 2 decimal places.
    ``cycle`` : BudgetCycle
        The active cycle instance; provides ``cycle.totalAllowance`` and
        any currency information the template requires.
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    # --- Budget cycle guard ---
    active_cycle = budget_dao.getActiveCycle(user_id)
    if not active_cycle:
        return redirect('setup')

    # Collect all analytics data needed by the template.
    transactions         = transaction_dao.getTransactionsByCycle(active_cycle)
    total_spent          = transaction_dao.getTotalExpensesByCycle(active_cycle)
    category_percentages = budget_service.calculateCategoryPercentages(active_cycle.cycleID)
    balance              = budget_service.getCurrentBalance(active_cycle.cycleID)

    return render(request, 'core/reports.html', {
        'transactions':  transactions,
        'total_spent':   round(total_spent, 2),
        'category_data': category_percentages,
        'balance':       round(balance, 2),
        'cycle':         active_cycle,
    })

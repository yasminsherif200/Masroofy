"""
Add Expense View – core.views.add_expense_view
================================================

Provides a single view function that handles the expense-entry form,
allowing authenticated users to record a new transaction against their
active budget cycle.

Budget Threshold Alert
----------------------
After a successful save, ``TransactionService.addExpense()`` returns a
``threshold_alert`` flag.  When this flag is ``True`` (the user has consumed
≥ 80 % of their budget), the view re-renders the form instead of redirecting,
displaying a warning message alongside the success confirmation.

Dependencies
------------
``core.services.TransactionService``
    Business-logic layer; validates the expense and persists it via the DAO,
    also computing the threshold alert.
``core.dao.BudgetDAO``
    Data-access layer; retrieves the user's active budget cycle.

Module-level Singletons
-----------------------
``transaction_service``
    Shared ``TransactionService`` instance reused across all requests.
``budget_dao``
    Shared ``BudgetDAO`` instance reused across all requests.
"""

from django.shortcuts import render, redirect
from core.services import TransactionService
from core.dao import BudgetDAO

#: Shared service instance for transaction business logic and persistence.
transaction_service = TransactionService()

#: Shared DAO instance for budget cycle lookups.
budget_dao = BudgetDAO()


def add_expense(request):
    """
    Display the add-expense form and save a new transaction on submission.

    **GET** – Renders ``core/add_expense.html`` pre-populated with the active
    cycle context (e.g. to show remaining balance or cycle end date in the UI).

    **POST** – Reads the form fields, delegates persistence to
    ``TransactionService.addExpense()``, and handles three outcomes:

    1. **Success, no threshold alert** – Redirects to ``'dashboard'``.
    2. **Success, threshold alert** – Re-renders the form with an orange
       warning that the user has consumed 80 % or more of their budget.
    3. **Failure** – Re-renders the form with the error message returned by
       the service layer (e.g. negative amount, invalid date).

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
        Rendered ``core/add_expense.html`` or a redirect response.

    Template context
    ----------------
    ``cycle`` : BudgetCycle
        The user's active cycle instance, always present so the template can
        display cycle metadata (remaining balance, end date, etc.).
    ``success`` : str, optional
        Threshold-alert message rendered in orange when the budget is ≥ 80 %
        consumed after adding the expense.
    ``error`` : str, optional
        Validation or persistence error rendered in red on failure.

    POST fields
    -----------
    ``title`` : str
        Short descriptive name for the expense (required).
    ``amount`` : str (numeric)
        Expense amount; must be positive (required).
    ``category`` : str
        Category label (e.g. "Food", "Transport"); optional.
    ``date`` : str
        Expense date in ``YYYY-MM-DD`` format (required).
    ``description`` : str
        Longer free-text note; defaults to ``''`` if omitted (optional).
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    # --- Budget cycle guard ---
    active_cycle = budget_dao.getActiveCycle(user_id)
    if not active_cycle:
        return redirect('setup')

    if request.method == 'POST':
        title       = request.POST.get('title')
        amount      = request.POST.get('amount')
        category    = request.POST.get('category')
        date        = request.POST.get('date')
        description = request.POST.get('description', '')  # Optional field

        # Delegate all validation and persistence to the service layer.
        result = transaction_service.addExpense(
            budget_cycle=active_cycle,
            title=title,
            amount=amount,
            category=category,
            date=date,
            description=description,
        )

        if result['success']:
            if result['threshold_alert']:
                # Budget ≥ 80 % consumed — warn the user but acknowledge the save.
                return render(request, 'core/add_expense.html', {
                    'success': 'Expense added! Warning: you have used 80% of your budget.',
                    'cycle':   active_cycle,
                })
            # Normal success path — go back to the dashboard.
            return redirect('dashboard')
        else:
            # Service-layer validation failed — show the error in the form.
            return render(request, 'core/add_expense.html', {
                'error': result['error'],
                'cycle': active_cycle,
            })

    # GET request — render the blank expense form.
    return render(request, 'core/add_expense.html', {
        'cycle': active_cycle,
    })

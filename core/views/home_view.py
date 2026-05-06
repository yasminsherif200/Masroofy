"""
Home View – core.views.home_view
==================================

Handles the two primary entry-point pages of the application:

* **Dashboard** – The user's main overview screen, showing financial
  summaries for the active budget cycle.
* **Setup** – The first-time (or post-reset) budget configuration wizard,
  where the user defines their total allowance and cycle end date.

Authentication Guard
--------------------
Both views check ``request.session['user_id']`` and redirect unauthenticated
visitors to ``'login'``.  If an authenticated user has no active budget cycle
they are redirected to ``'setup'`` (dashboard) or served the setup form.

Dependencies
------------
``core.services.BudgetService``
    Business-logic layer for budget calculations (balance, daily limit,
    thresholds, remaining days, category breakdown, cycle creation).
``core.dao.BudgetDAO``
    Data-access layer for retrieving and persisting budget cycle records.

Module-level Singletons
-----------------------
``budget_service``
    Shared ``BudgetService`` instance reused across all requests.
``budget_dao``
    Shared ``BudgetDAO`` instance reused across all requests.
"""

from django.shortcuts import render, redirect
from core.services import BudgetService
from core.dao import BudgetDAO

#: Shared service instance for budget calculations and cycle management.
budget_service = BudgetService()

#: Shared DAO instance for budget cycle database operations.
budget_dao = BudgetDAO()


def dashboard(request):
    """
    Render the main financial dashboard for the active budget cycle.

    **GET only** – Computes and assembles all financial metrics for the
    current cycle, then renders ``core/dashboard.html``.

    Authentication
    --------------
    Redirects to ``'login'`` if ``request.session['user_id']`` is absent.
    Redirects to ``'setup'`` if no active budget cycle exists for the user.

    Financial Metrics (passed to template)
    ---------------------------------------
    ``daily_limit`` : float
        Safe amount the user can spend per remaining day without exceeding
        the budget, rounded to 2 decimal places.
    ``balance`` : float
        Remaining unspent budget for the current cycle, rounded to 2 d.p.
    ``remaining_days`` : int
        Calendar days left until the cycle end date.
    ``threshold_reached`` : bool
        ``True`` when ≥ 80 % of the cycle budget has been spent; used to
        display a prominent warning banner.
    ``category_data`` : dict[str, float]
        Mapping of expense category name → percentage of total spending.
    ``cycle`` : BudgetCycle
        The active ``BudgetCycle`` model instance (exposes ``cycleID``,
        ``totalAllowance``, start/end dates, etc.).

    Parameters
    ----------
    request : django.http.HttpRequest

    Returns
    -------
    django.http.HttpResponse
        Rendered ``core/dashboard.html`` or a redirect response.
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    # --- Budget cycle guard ---
    active_cycle = budget_dao.getActiveCycle(user_id)
    if not active_cycle:
        return redirect('setup')

    # --- Compute financial metrics via the service layer ---
    daily_limit          = budget_service.getSafeDailyLimit(active_cycle.cycleID)
    balance              = budget_service.getCurrentBalance(active_cycle.cycleID)
    threshold_reached    = budget_service.checkThreshold(active_cycle.cycleID)
    remaining_days       = budget_service.getRemainingDays(active_cycle.cycleID)
    category_percentages = budget_service.calculateCategoryPercentages(active_cycle.cycleID)

    return render(request, 'core/dashboard.html', {
        'daily_limit':       round(daily_limit, 2),
        'balance':           round(balance, 2),
        'remaining_days':    remaining_days,
        'threshold_reached': threshold_reached,
        'category_data':     category_percentages,
        'cycle':             active_cycle,
    })


def setup(request):
    """
    Display and process the budget setup wizard.

    This view is the entry-point for first-time users or users who have
    reset their budget cycle via ``settings_view.reset_cycle``.

    **GET** – Renders the setup form (``core/setup.html``).  If the user
    already has an active cycle, they are redirected straight to
    ``'dashboard'`` — they cannot set up a second parallel cycle.

    **POST** – Reads ``totalAllowance`` and ``endDate`` from the request body,
    validates them, then creates a new budget cycle:

    1. Both fields must be present (non-empty).
    2. ``endDate`` is parsed from ISO format (``YYYY-MM-DD``); the start date
       defaults to today.
    3. Delegates creation to ``BudgetService.createNewCycle()``.
    4. On success, redirects to ``'dashboard'``.
    5. On failure (invalid amount/dates), re-renders the form with an error.

    Parameters
    ----------
    request : django.http.HttpRequest

    Returns
    -------
    django.http.HttpResponse
        Rendered ``core/setup.html`` or a redirect response.

    Template context
    ----------------
    ``error`` : str, optional
        Validation or creation error displayed in red on the setup form.

    Notes
    -----
    .. warning::
        ``budget_service.createNewCycle()`` is currently called **twice** in
        the POST branch — once before the success check and once inside the
        ``if success:`` block.  The first call should be removed to avoid
        creating a duplicate cycle.

    POST fields
    -----------
    ``totalAllowance`` : str (numeric)
        Total budget for the cycle, in EGP.
    ``endDate`` : str
        Cycle end date in ``YYYY-MM-DD`` format.
    ``startDate`` : str (commented out)
        Planned field — currently hardcoded to ``date.today()``.
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    # Redirect users who already have an active cycle away from setup.
    if budget_dao.getActiveCycle(user_id):
        return redirect('dashboard')

    if request.method == 'POST':
        amount   = request.POST.get('totalAllowance')
        end_date = request.POST.get('endDate')

        # Validate: both fields are required.
        if not amount or not end_date:
            return render(request, 'core/setup.html', {
                'error': 'All fields are required.'
            })

        from datetime import date
        start = date.today()                  # Cycle always starts today.
        end   = date.fromisoformat(end_date)  # Parse ISO date string.

        # TODO: Remove the first call below — it creates a duplicate cycle.
        budget_service.createNewCycle(user_id, float(amount), start, end)

        success = budget_service.createNewCycle(user_id, float(amount), start, end)

        if success:
            return redirect('dashboard')
        else:
            return render(request, 'core/setup.html', {
                'error': 'Invalid amount or dates.'
            })

    # GET request — render the blank setup form.
    return render(request, 'core/setup.html')

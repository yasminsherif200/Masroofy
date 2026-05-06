"""
Settings View – core.views.settings_view
==========================================

Provides view functions for user-profile management and budget cycle
administration:

* ``settings`` – Lets the user update their display name and optionally
  change their 4-digit PIN.
* ``reset_cycle`` – Wipes all transactions from the active cycle, resets the
  cycle itself, and redirects the user back to the setup wizard.

PIN Update Logic
----------------
The PIN field is **optional** on the settings form.  If the user leaves it
blank, only the username is updated (``UserService.updateUserName``).  If a
PIN is supplied, it must be exactly 4 digits and match the confirmation field
before ``UserService.updateSecurity`` is called.

Dependencies
------------
``core.services.UserService``
    Business-logic layer for credential management (``updateSecurity``,
    ``updateUserName``).
``core.dao.UserDAO``
    Data-access layer for fetching the current user's stored data.

The following are imported *inside* ``reset_cycle`` to avoid circular imports
at module load time:

``core.services.BudgetService``
    Resets the active budget cycle record.
``core.dao.BudgetDAO``
    Retrieves the active cycle.
``core.dao.TransactionDAO``
    Deletes all transactions belonging to the cycle before reset.

Module-level Singletons
-----------------------
``user_service``
    Shared ``UserService`` instance reused across all requests.
``user_dao``
    Shared ``UserDAO`` instance reused across all requests.
"""

from django.shortcuts import render, redirect
from core.services import UserService
from core.dao import UserDAO

#: Shared service instance for user credential management.
user_service = UserService()

#: Shared DAO instance for user data retrieval.
user_dao = UserDAO()


def settings(request):
    """
    Display and process the user-settings form.

    **GET** – Fetches the current user record and renders
    ``core/settings.html`` with the stored username pre-populated.

    **POST** – Validates and saves the submitted profile changes:

    * ``userName`` is always required.
    * ``pin`` is optional; when supplied it must be exactly 4 numeric digits
      and must match ``confirmPin``.
    * On PIN update: calls ``UserService.updateSecurity(userName, pin, True)``.
    * On name-only update: calls ``UserService.updateUserName(userName)``.
    * On success: re-renders the settings page with a green success message
      and the refreshed user record.

    Authentication
    --------------
    Redirects to ``'login'`` if ``request.session['user_id']`` is absent.

    Parameters
    ----------
    request : django.http.HttpRequest

    Returns
    -------
    django.http.HttpResponse
        Rendered ``core/settings.html`` or a redirect to ``'login'``.

    Template context
    ----------------
    ``user`` : User
        The current user record; provides ``user.userName`` for form
        pre-population.
    ``error`` : str, optional
        Validation error rendered in red.
    ``success`` : str, optional
        Confirmation message rendered in green after a successful save.

    POST fields
    -----------
    ``userName`` : str
        New display name (required).
    ``pin`` : str
        New 4-digit PIN (optional; leave blank to keep the current PIN).
    ``confirmPin`` : str
        Must match ``pin`` when a new PIN is being set.
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')

    user = user_dao.getUserSecurityData()

    if request.method == 'POST':
        userName   = request.POST.get('userName')
        pin        = request.POST.get('pin')
        confirmPin = request.POST.get('confirmPin')

        # Username is mandatory regardless of whether a PIN is being changed.
        if not userName:
            return render(request, 'core/settings.html', {
                'error': 'Username is required.',
                'user':  user,
            })

        if pin:
            # PIN supplied — validate format (exactly 4 digits).
            if not pin.isdigit() or len(pin) != 4:
                return render(request, 'core/settings.html', {
                    'error': 'PIN must be exactly 4 digits.',
                    'user':  user,
                })
            # PIN must match its confirmation.
            if pin != confirmPin:
                return render(request, 'core/settings.html', {
                    'error': 'PINs do not match.',
                    'user':  user,
                })
            # Persist both the new username and the new PIN.
            user_service.updateSecurity(userName, pin, True)
        else:
            # No PIN supplied — update the username only.
            user_service.updateUserName(userName)

        # Re-fetch after save so the template shows the updated values.
        return render(request, 'core/settings.html', {
            'success': 'Settings saved successfully.',
            'user':    user_dao.getUserSecurityData(),
        })

    # GET request — render the pre-populated settings form.
    return render(request, 'core/settings.html', {
        'user': user,
    })


def reset_cycle(request):
    """
    Reset the active budget cycle and redirect the user to the setup wizard.

    This is a destructive operation:

    1. All transactions in the active cycle are permanently deleted via
       ``TransactionDAO.deleteAllTransactionsByCycle()``.
    2. The cycle itself is reset (balances cleared, dates nulled) via
       ``BudgetService.resetCurrentCycle()``.
    3. The user is redirected to ``'setup'`` to configure a new cycle.

    If there is no active cycle the redirect to ``'setup'`` still occurs,
    making this function idempotent.

    Authentication
    --------------
    Redirects to ``'login'`` if ``request.session['user_id']`` is absent.

    Parameters
    ----------
    request : django.http.HttpRequest
        Expected to be a POST request (submitted via the Reset button in
        ``core/settings.html``), though the method is not explicitly checked.
    transaction_id : –
        Not applicable to this view.

    Returns
    -------
    django.http.HttpResponseRedirect
        Always redirects to ``'setup'``.

    Notes
    -----
    * Dependencies (``BudgetService``, ``BudgetDAO``, ``TransactionDAO``) are
      imported inside the function body to avoid potential circular-import
      issues at module load time.
    * The Reset button in the template uses a separate ``<form>`` posting to
      ``{% url 'reset_cycle' %}``, so it does not interfere with the main
      settings save form.
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    # Local imports to avoid circular dependencies at module load time.
    from core.services import BudgetService
    from core.dao import BudgetDAO, TransactionDAO
    budget_service  = BudgetService()
    budget_dao      = BudgetDAO()
    transaction_dao = TransactionDAO()

    active_cycle = budget_dao.getActiveCycle(user_id)
    if active_cycle:
        # Step 1: Permanently delete all transactions in the cycle.
        transaction_dao.deleteAllTransactionsByCycle(active_cycle)
        # Step 2: Reset the cycle record itself (clears totals / dates).
        budget_service.resetCurrentCycle(active_cycle.cycleID)

    # Send the user back to the setup wizard for a fresh configuration.
    return redirect('setup')

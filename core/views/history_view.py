"""
History View – core.views.history_view
========================================

Provides view functions for listing, deleting, and editing the transactions
that belong to the user's active budget cycle.

Edit / Delete Eligibility
--------------------------
Both mutation operations (delete and edit) are guarded by service-layer
permission checks:

* ``TransactionService.canRemoveExpense(transaction_id)`` – returns ``True``
  only when the transaction is eligible for deletion (e.g. created today).
* ``TransactionService.canEditExpense(transaction)`` – returns ``True`` only
  when the transaction is eligible for editing.

Matching guards are also applied in ``history.html`` via a template date
comparison, keeping the UI consistent with the backend rules.

Dependencies
------------
``core.dao.BudgetDAO``
    Retrieves the active budget cycle for the current user.
``core.dao.TransactionDAO``
    CRUD operations on individual transaction records.
``core.services.TransactionService``
    Business-logic checks for edit/delete eligibility.

Module-level Singletons
-----------------------
``budget_dao``
    Shared ``BudgetDAO`` instance.
``transaction_dao``
    Shared ``TransactionDAO`` instance.
``transaction_service``
    Shared ``TransactionService`` instance.
"""

from django.shortcuts import render, redirect
from core.dao import BudgetDAO, TransactionDAO
from core.services import TransactionService

#: Shared DAO instance for budget cycle lookups.
budget_dao = BudgetDAO()

#: Shared DAO instance for transaction CRUD operations.
transaction_dao = TransactionDAO()

#: Shared service instance for edit/delete eligibility checks.
transaction_service = TransactionService()


def history(request):
    """
    Display a paginated list of all transactions in the active budget cycle.

    **GET only** – Fetches every transaction linked to the current cycle and
    renders them in a searchable table (client-side filtering via JS).

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
        Rendered ``core/history.html`` or a redirect response.

    Template context
    ----------------
    ``transactions`` : QuerySet / list
        All transactions for the active cycle, ordered by the DAO's default
        ordering (expected: most recent first).
    ``cycle`` : BudgetCycle
        The active cycle instance; passed so the template can display cycle
        metadata (e.g. total allowance, date range).
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    # --- Budget cycle guard ---
    active_cycle = budget_dao.getActiveCycle(user_id)
    if not active_cycle:
        return redirect('setup')

    # Fetch all transactions for the current cycle via the DAO.
    transactions = transaction_dao.getTransactionsByCycle(active_cycle)

    return render(request, 'core/history.html', {
        'transactions': transactions,
        'cycle':        active_cycle,
    })


def delete_transaction(request, transaction_id):
    """
    Delete a single transaction if it passes the eligibility check.

    The transaction is fetched by primary key, then validated through
    ``TransactionService.canRemoveExpense()``.  If both checks pass, the
    record is permanently deleted.  The user is always redirected to
    ``'history'`` regardless of outcome (silent no-op on failure).

    Authentication
    --------------
    Redirects to ``'login'`` if the session is unauthenticated.

    Parameters
    ----------
    request : django.http.HttpRequest
    transaction_id : int
        Primary key of the transaction to delete, captured from the URL
        pattern ``/delete-transaction/<int:transaction_id>/``.

    Returns
    -------
    django.http.HttpResponseRedirect
        Always redirects to ``'history'``.

    Notes
    -----
    * No ownership check is currently performed — any authenticated user
      can attempt to delete any transaction by ID.  Consider adding a
      ``transaction.user_id == user_id`` guard before deleting.
    * The view accepts any HTTP method.  Callers (``history.html``) use a
      ``<form method="POST">`` with a CSRF token for safe deletion.
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')

    transaction = transaction_dao.getTransactionByID(transaction_id)

    # Only delete if the transaction exists AND passes the business-rule check.
    if transaction and transaction_service.canRemoveExpense(transaction_id):
        transaction_dao.deleteTransaction(transaction_id)

    return redirect('history')


def edit_transaction(request, transaction_id):
    """
    Display and process the edit form for a single transaction.

    **GET** – Fetches the transaction by primary key, checks edit eligibility,
    and renders ``core/edit_transaction.html`` with the existing field values
    pre-populated.

    **POST** – Reads the updated fields from the request body, mutates the
    in-memory transaction object, and persists it via ``TransactionDAO``.

    Authentication
    --------------
    Redirects to ``'login'`` if the session is unauthenticated.
    Redirects to ``'history'`` if the transaction does not exist or fails the
    ``canEditExpense`` check.

    Parameters
    ----------
    request : django.http.HttpRequest
    transaction_id : int
        Primary key of the transaction to edit, captured from the URL
        pattern ``/edit-transaction/<int:transaction_id>/``.

    Returns
    -------
    django.http.HttpResponse
        Rendered ``core/edit_transaction.html`` (GET) or a redirect to
        ``'history'`` (POST success or eligibility failure).

    Template context
    ----------------
    ``transaction`` : Transaction
        The transaction instance with current field values, used to
        pre-populate the edit form inputs.

    POST fields
    -----------
    ``title`` : str
        Updated transaction title (required).
    ``amount`` : str (numeric)
        Updated amount; must be positive (required).
    ``category`` : str
        Updated category label (optional).
    ``description`` : str
        Updated free-text note; defaults to ``''`` if omitted (optional).

    Notes
    -----
    * The ``date`` field is intentionally not editable — transactions are
      locked to their original date.
    * No ownership check is currently performed — any authenticated user
      can edit any transaction by ID.  Consider adding a user-ownership guard.
    """
    # --- Authentication guard ---
    if not request.session.get('user_id'):
        return redirect('login')

    transaction = transaction_dao.getTransactionByID(transaction_id)

    # Redirect away if the transaction is missing or not eligible for editing.
    if not transaction or not transaction_service.canEditExpense(transaction):
        return redirect('history')

    if request.method == 'POST':
        # Mutate the transaction object with the submitted values.
        transaction.title       = request.POST.get('title')
        transaction.amount      = request.POST.get('amount')
        transaction.category    = request.POST.get('category')
        transaction.description = request.POST.get('description', '')

        # Persist the changes through the DAO.
        transaction_dao.updateTransaction(transaction)
        return redirect('history')

    # GET request — render the pre-populated edit form.
    return render(request, 'core/edit_transaction.html', {
        'transaction': transaction,
    })
   
"""
Transaction Service – core.services.transaction_service
=========================================================

Contains ``TransactionService``, the business-logic class responsible for
validating, persisting, and managing individual financial transactions.

Responsibilities
----------------
* Validate expense inputs (title, amount, date, balance sufficiency).
* Persist new expense transactions via ``TransactionDAO``.
* Trigger the 80 % budget threshold check after each save.
* Determine whether an existing transaction is eligible to be edited or
  deleted (today-only rule).
* Provide a transaction filter helper combining category and date criteria.
* Recalculate the safe daily limit after a transaction is added.

Architecture
------------
``TransactionService`` depends on ``BudgetService`` for threshold and
cycle-balance logic, keeping the responsibilities cleanly separated:

    View  →  TransactionService  →  TransactionDAO / BudgetDAO  →  Database
                                 ↘  BudgetService  (threshold / balance)

Module-level Constants
----------------------
``THRESHOLD_PERCENTAGE`` : Decimal
    The 80 % alert threshold expressed as a ``Decimal`` multiplier (``0.80``).
    Used in ``addExpense`` for the post-save threshold check.
"""

from core.dao import TransactionDAO, BudgetDAO
from core.models import Transaction, BudgetCycle
from core.services import BudgetService
from decimal import Decimal

#: Budget consumption threshold that triggers an alert (80 %).
THRESHOLD_PERCENTAGE = Decimal('0.80')


class TransactionService:
    """
    Service class encapsulating all business logic for transaction management.

    Instantiated as a module-level singleton in each view module that handles
    transactions (``add_expense_view``, ``history_view``).

    Attributes
    ----------
    transactionDAO : TransactionDAO
        DAO instance for transaction CRUD operations.
    budgetDAO : BudgetDAO
        DAO instance for retrieving cycle records needed in calculations.
    budgetService : BudgetService
        Service instance used for balance / threshold delegation.
    """

    def __init__(self):
        self.transactionDAO = TransactionDAO()
        self.budgetDAO      = BudgetDAO()
        self.budgetService  = BudgetService()

    # ------------------------------------------------------------------
    # Core expense operations
    # ------------------------------------------------------------------

    def addExpense(self, budget_cycle, title, amount, category, date, description=''):
        """
        Validate and persist a new expense transaction for a budget cycle.

        Performs the following steps in order:

        1. Convert ``amount`` to ``Decimal`` for safe arithmetic.
        2. Validate that ``title`` is non-empty.
        3. Validate that ``amount > 0``.
        4. Validate that ``date`` is present.
        5. Check that ``amount`` does not exceed the remaining balance.
        6. Insert the transaction record via ``TransactionDAO``.
        7. Re-compute total spend after insertion and evaluate the 80 %
           threshold alert flag.

        Parameters
        ----------
        budget_cycle : BudgetCycle
            The active cycle object that the new transaction belongs to.
            Provides ``totalAllowance`` for balance and threshold checks.
        title : str
            Short label for the expense (required, must be non-empty after
            stripping whitespace).
        amount : str or numeric
            Expense value; converted to ``Decimal`` internally.  Must be > 0
            and must not exceed the remaining balance.
        category : str or None
            Optional category label (e.g. "Food", "Transport").
        date : str or datetime.date
            Date the expense occurred; passed through to the DAO as-is.
        description : str, optional
            Free-text note; defaults to ``''`` if omitted.

        Returns
        -------
        dict
            Always contains the keys:

            ``success`` : bool
                ``True`` on a successful save; ``False`` on any validation error.
            ``transaction`` : Transaction or None
                The newly created ``Transaction`` instance on success;
                absent/``None`` on failure.
            ``error`` : str or None
                Human-readable error message on failure; ``None`` on success.
            ``threshold_alert`` : bool
                ``True`` when total spending after this transaction reaches
                or exceeds 80 % of ``totalAllowance``; ``False`` otherwise.
                Only present in the success response.

        Examples
        --------
        Success response::

            {
                'success': True,
                'transaction': <Transaction: Lunch - 150.00 (expense)>,
                'error': None,
                'threshold_alert': False,
            }

        Failure response::

            {
                'success': False,
                'error': 'Amount exceeds remaining balance of 50.00 EGP.',
            }
        """
        amount = Decimal(str(amount))

        # --- Input validation ---
        if not title or not title.strip():
            return {'success': False, 'error': 'Title is required.'}

        if amount <= 0:
            return {'success': False, 'error': 'Amount must be greater than zero.'}

        if not date:
            return {'success': False, 'error': 'Date is required.'}

        # --- Balance sufficiency check ---
        total_spent = self.transactionDAO.getTotalExpensesByCycle(budget_cycle)
        balance     = Decimal(str(budget_cycle.totalAllowance)) - total_spent
        if amount > balance:
            return {
                'success': False,
                'error': f'Amount exceeds remaining balance of {round(balance, 2)} EGP.',
            }

        # --- Persist to database ---
        transaction = self.transactionDAO.insertTransaction(
            budget_cycle=    budget_cycle,
            title=           title.strip(),   # Strip leading/trailing whitespace
            amount=          amount,
            transaction_type='expense',        # Always 'expense' from this form
            category=        category,
            date=            date,
            description=     description,
        )

        # --- 80 % threshold check (User Story #6) ---
        # Re-query total after insert so the new transaction is included.
        total_spent_after = self.transactionDAO.getTotalExpensesByCycle(budget_cycle)
        total_allowance   = Decimal(str(budget_cycle.totalAllowance))
        threshold_alert   = (total_spent_after / total_allowance) >= THRESHOLD_PERCENTAGE

        return {
            'success':         True,
            'transaction':     transaction,
            'error':           None,
            'threshold_alert': threshold_alert,
        }

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def validateAmount(self, amount):
        """
        Validate that a raw amount value is a positive number.

        Wraps the conversion in a try/except so that non-numeric strings
        (e.g. ``'abc'``) return ``False`` rather than raising an exception.

        Parameters
        ----------
        amount : any
            The raw value to validate (typically a string from a POST request).

        Returns
        -------
        bool
            ``True`` if the value can be converted to a positive ``Decimal``;
            ``False`` for zero, negative values, or non-numeric input.
        """
        try:
            return Decimal(str(amount)) > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Daily limit recalculation
    # ------------------------------------------------------------------

    def calculateUpdatedDailyLimit(self, budget_cycle):
        """
        Recalculate the safe daily spending limit after a transaction is added.

        Computes:  ``(totalAllowance − total_expenses) / remaining_days``

        Intended to be called after ``addExpense`` so that the dashboard
        always shows an up-to-date daily limit.

        Parameters
        ----------
        budget_cycle : int or BudgetCycle
            The budget cycle ID (integer) — passed directly to
            ``BudgetDAO.getCycleByCycleID``.

        Returns
        -------
        Decimal or int
            Updated daily limit, or ``0`` if the cycle is not found or
            no days remain.

        Notes
        -----
        .. warning::
            The parameter name is ``budget_cycle`` but the value is used as
            an integer cycle ID (passed to ``getCycleByCycleID``).  This is
            inconsistent with other methods that accept a ``BudgetCycle``
            object.  Consider renaming to ``cycleID`` for clarity.
        """
        cycle = self.budgetDAO.getCycleByCycleID(budget_cycle)
        if not cycle:
            return 0
        total_expenses = self.transactionDAO.getTotalExpensesByCycle(budget_cycle)
        balance        = Decimal(str(cycle.totalAllowance)) - total_expenses
        remaining_days = cycle.getRemainingDays()
        if remaining_days == 0:
            return 0
        return balance / remaining_days

    # ------------------------------------------------------------------
    # Transaction filtering
    # ------------------------------------------------------------------

    def filterTransactions(self, budget_cycle, category=None, date=None):
        """
        Return a filtered queryset of transactions for a budget cycle.

        Applies category and/or date filters based on which arguments are
        provided.  Falls back to returning all transactions for the cycle
        when no filters are given.

        Parameters
        ----------
        budget_cycle : BudgetCycle
            The cycle whose transactions should be filtered.
        category : str or None, optional
            If provided, only transactions with this category are returned.
        date : datetime.date or None, optional
            If provided, only transactions on this exact date are returned.
            When combined with ``category``, both filters are applied.

        Returns
        -------
        QuerySet
            A filtered ``Transaction`` queryset.  When both ``category`` and
            ``date`` are supplied, the category filter is applied via the DAO
            and the date filter is chained on the resulting queryset.

        Filter logic summary
        --------------------
        +----------+---------+--------------------------------------------------+
        | category |  date   | Behaviour                                        |
        +==========+=========+==================================================+
        | given    | given   | Filter by category via DAO, then chain date=date |
        +----------+---------+--------------------------------------------------+
        | given    | None    | Filter by category only                          |
        +----------+---------+--------------------------------------------------+
        | None     | given   | Filter by exact date range [date, date]          |
        +----------+---------+--------------------------------------------------+
        | None     | None    | Return all transactions for the cycle            |
        +----------+---------+--------------------------------------------------+
        """
        if category and date:
            # Apply category filter through DAO, then narrow by exact date.
            return self.transactionDAO.getTransactionsByCategory(
                budget_cycle, category
            ).filter(date=date)
        elif category:
            return self.transactionDAO.getTransactionsByCategory(
                budget_cycle, category)
        elif date:
            # Single-day range: pass the same date as both start and end.
            return self.transactionDAO.getTransactionsByDateRange(
                budget_cycle, date, date)
        # No filters — return the full transaction list for the cycle.
        return self.transactionDAO.getTransactionsByCycle(budget_cycle)

    # ------------------------------------------------------------------
    # Edit / delete eligibility
    # ------------------------------------------------------------------

    def canEditExpense(self, transaction):
        """
        Determine whether a transaction is eligible to be edited.

        The business rule is: **transactions can only be edited on the same
        day they were created** (``transaction.date == today``).

        This rule is enforced both server-side (called by
        ``history_view.edit_transaction``) and client-side (the Edit button
        is hidden in ``history.html`` for non-today transactions).

        Parameters
        ----------
        transaction : Transaction
            The transaction instance to check.

        Returns
        -------
        bool
            ``True`` if ``transaction.date`` equals today's date;
            ``False`` otherwise.
        """
        # Local import to avoid loading Django timezone utilities at module
        # import time, which can cause issues during early startup.
        from django.utils import timezone
        today = timezone.now().date()
        return transaction.date == today

    def canRemoveExpense(self, transaction_id):
        """
        Determine whether a transaction is eligible to be deleted.

        Applies the same same-day rule as ``canEditExpense``, but accepts a
        transaction ID rather than an object.  Fetches the record internally
        via ``TransactionDAO``.

        Parameters
        ----------
        transaction_id : int
            Primary key of the transaction to check.

        Returns
        -------
        bool
            ``True`` if the transaction exists **and** its date equals today;
            ``False`` if the transaction is not found or was created on a
            previous day.
        """
        transaction = self.transactionDAO.getTransactionByID(transaction_id)
        if not transaction:
            return False
        from django.utils import timezone
        today = timezone.now().date()
        return transaction.date == today

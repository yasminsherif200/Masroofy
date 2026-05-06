"""
Budget Service – core.services.budget_service
===============================================

Contains ``BudgetService``, the business-logic class responsible for all
operations related to budget cycles: creation, validation, financial
calculations, category analytics, threshold alerting, and cycle reset.

This class sits between the view layer and the DAO layer:

    View  →  BudgetService  →  BudgetDAO / TransactionDAO  →  Database

Dependencies
------------
``core.dao.BudgetDAO``
    Persists and retrieves ``BudgetCycle`` records.
``core.dao.TransactionDAO``
    Reads transaction totals used in balance and threshold calculations.
``core.models.BudgetCycle``
    ORM model instantiated during cycle creation.
``decimal.Decimal``
    Used for all monetary arithmetic to avoid floating-point rounding errors.
``datetime``
    Imported at module level (used implicitly via ``date`` objects passed in
    from the view layer).
"""

from core.dao import BudgetDAO
from core.dao import TransactionDAO
from core.models import BudgetCycle
from datetime import datetime
from decimal import Decimal


class BudgetService:
    """
    Service class encapsulating all business logic for budget cycle management.

    Instantiated as a module-level singleton in each view module that requires
    budget operations (``home_view``, ``reports_view``, ``settings_view``).

    Attributes
    ----------
    budgetDAO : BudgetDAO
        DAO instance for budget cycle persistence and retrieval.
    transactionDAO : TransactionDAO
        DAO instance for querying transaction totals needed in calculations.
    """

    def __init__(self):
        self.budgetDAO = BudgetDAO()
        self.transactionDAO = TransactionDAO()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def isFirstTime(self, userID):
        """
        Check whether the user has ever created a budget cycle.

        Parameters
        ----------
        userID : int
            The primary key of the user to check.

        Returns
        -------
        bool
            ``True`` if the user has no existing budget cycle; ``False``
            otherwise.
        """
        cycle = self.budgetDAO.getActiveCycle(userID)
        return cycle is None

    def validateAmount(self, amount):
        """
        Validate that a monetary amount is strictly positive.

        Parameters
        ----------
        amount : float or Decimal
            The amount to validate.

        Returns
        -------
        bool
            ``True`` if ``amount > 0``; ``False`` otherwise.
        """
        return amount > 0

    def validateDate(self, start, end):
        """
        Validate that the end date is strictly after the start date.

        Parameters
        ----------
        start : datetime.date
            The proposed cycle start date.
        end : datetime.date
            The proposed cycle end date.

        Returns
        -------
        bool
            ``True`` if ``end > start``; ``False`` otherwise.
        """
        return end > start

    # ------------------------------------------------------------------
    # Daily limit calculations
    # ------------------------------------------------------------------

    def calculateDailyLimit(self, amount, days):
        """
        Calculate a fixed daily spending limit given a total amount and
        number of days.

        This is used at cycle-creation time to store an initial ``dailyLimit``
        on the ``BudgetCycle`` record.  For a real-time safe daily limit
        (accounting for already-spent money), use ``getSafeDailyLimit()``.

        Parameters
        ----------
        amount : float or Decimal
            Total budget for the cycle.
        days : int
            Total number of days in the cycle.

        Returns
        -------
        float or Decimal
            ``amount / days``, or ``0`` if ``days == 0`` (guards against
            zero-division when start and end dates are the same).
        """
        if days == 0:
            return 0
        return amount / days

    def getSafeDailyLimit(self, cycleID):
        """
        Calculate the current safe daily spending limit based on the
        **remaining balance** and **remaining days** in the cycle.

        Unlike the static ``dailyLimit`` field stored on the model, this
        value is re-derived on every request so it shrinks as money is spent
        and as the end date approaches.

        Parameters
        ----------
        cycleID : int
            Primary key of the budget cycle.

        Returns
        -------
        Decimal or int
            Remaining balance divided by remaining days, or ``0`` if there
            are no days left (end date reached or passed).
        """
        balance = self.getCurrentBalance(cycleID)
        days    = self.getRemainingDays(cycleID)
        if days == 0:
            return 0
        return balance / days

    # ------------------------------------------------------------------
    # Cycle CRUD
    # ------------------------------------------------------------------

    def createNewCycle(self, userID, amount, start, end):
        """
        Create and persist a new budget cycle for the given user.

        Validates both the amount and the date range before creating the
        ``BudgetCycle`` record.  The ``dailyLimit`` field is pre-computed
        from the total allowance and the number of days in the cycle.

        Parameters
        ----------
        userID : int
            Primary key of the owning ``User`` record.
        amount : float
            Total allowance for the new cycle in EGP.
        start : datetime.date
            Cycle start date (typically ``date.today()`` — set by the view).
        end : datetime.date
            Cycle end date chosen by the user.

        Returns
        -------
        bool
            ``True`` on success; ``False`` if validation fails (non-positive
            amount or end date not after start date).

        Notes
        -----
        .. warning::
            ``home_view.setup`` currently calls this method **twice** in the
            same POST request, which will create duplicate ``BudgetCycle``
            records.  The first (unchecked) call on line ~40 of ``home_view``
            should be removed.
        """
        if not self.validateAmount(amount):
            return False
        if not self.validateDate(start, end):
            return False

        days        = (end - start).days
        daily_limit = self.calculateDailyLimit(amount, days)

        # Resolve the User ORM object from the session-stored ID.
        from core.models import User
        user = User.objects.get(userID=userID)

        cycle = BudgetCycle(
            user=          user,
            totalAllowance=amount,
            dailyLimit=    daily_limit,
            startDate=     start,
            endDate=       end,
        )
        self.budgetDAO.saveCycle(cycle)
        return True

    def resetCurrentCycle(self, cycleID):
        """
        Delete the budget cycle identified by ``cycleID``.

        Called by ``settings_view.reset_cycle`` **after** all transactions for
        the cycle have already been deleted via ``TransactionDAO``.  Redirects
        the user to the setup wizard so they can configure a fresh cycle.

        Parameters
        ----------
        cycleID : int
            Primary key of the cycle to delete.

        Returns
        -------
        bool
            Always returns ``True``.
        """
        self.budgetDAO.deleteCycle(cycleID)
        return True

    # ------------------------------------------------------------------
    # Financial calculations
    # ------------------------------------------------------------------

    def getRemainingDays(self, cycleID):
        """
        Return the number of calendar days remaining until the cycle end date.

        Delegates to ``BudgetCycle.getRemainingDays()`` on the model instance,
        which uses ``max(delta.days, 0)`` to prevent negative values on
        expired cycles.

        Parameters
        ----------
        cycleID : int
            Primary key of the budget cycle.

        Returns
        -------
        int
            Days remaining, or ``0`` if the cycle is not found or has expired.
        """
        cycle = self.budgetDAO.getCycleByCycleID(cycleID)
        if not cycle:
            return 0
        return cycle.getRemainingDays()

    def getCurrentBalance(self, cycleID):
        """
        Calculate the remaining unspent budget for a cycle.

        Computed as:  ``totalAllowance  −  total_expenses_so_far``

        Uses ``Decimal`` arithmetic to avoid floating-point drift when
        subtracting the transaction total from the allowance.

        Parameters
        ----------
        cycleID : int
            Primary key of the budget cycle.

        Returns
        -------
        Decimal or int
            Remaining balance, or ``0`` if the cycle is not found.

        Notes
        -----
        ``transactionDAO.getTotalExpensesByCycle`` is called with ``cycleID``
        (an integer) here, but with a ``BudgetCycle`` object in
        ``checkThreshold``.  The DAO should handle both forms consistently —
        verify when modifying either method.
        """
        cycle = self.budgetDAO.getCycleByCycleID(cycleID)
        if not cycle:
            return 0
        total_spent = self.transactionDAO.getTotalExpensesByCycle(cycleID)
        return Decimal(str(cycle.totalAllowance)) - total_spent

    def calculateCategoryPercentages(self, cycleID):
        """
        Compute each expense category's share of total spending for a cycle.

        Uses a Django ORM aggregation query to ``SUM`` transaction amounts
        grouped by ``category``, then converts each group's total to a
        percentage of the overall spend.

        Parameters
        ----------
        cycleID : int
            Primary key of the budget cycle.

        Returns
        -------
        dict[str, float]
            Mapping of ``{category_name: percentage}`` where each percentage
            is rounded to 2 decimal places and all values sum to ≈ 100.
            Returns an empty dict ``{}`` if no expenses have been recorded
            (guards against zero-division).

        Example
        -------
        .. code-block:: python

            {
                'Food':      45.50,
                'Transport': 30.00,
                'Other':     24.50,
            }

        Notes
        -----
        * Imported locally (``Transaction``, ``Sum``) to avoid circular
          imports at module load time.
        * Categories are whatever free-text string the user entered on the
          add-expense form; no normalisation or grouping of similar names
          is applied.
        """
        # Local imports to prevent circular imports at module level.
        from core.models import Transaction
        from django.db.models import Sum

        # Aggregate total spending per category using a GROUP BY query.
        results = Transaction.objects.filter(
            budget_cycle_id=cycleID
        ).values('category').annotate(
            total=Sum('amount')
        )

        total_spent = sum(r['total'] for r in results)
        if total_spent == 0:
            return {}  # No expenses yet — avoid zero-division.

        return {
            r['category']: round((r['total'] / total_spent) * 100, 2)
            for r in results
        }

    def checkThreshold(self, cycleID):
        """
        Determine whether the user has spent 80 % or more of their budget.

        This flag is used in two places:

        * ``home_view.dashboard`` — to show a warning banner on the dashboard.
        * ``add_expense_view.add_expense`` (via ``TransactionService``) — to
          show a threshold alert immediately after adding an expense.

        Parameters
        ----------
        cycleID : int
            Primary key of the budget cycle.

        Returns
        -------
        bool
            ``True`` when ``(total_spent / totalAllowance) * 100 >= 80``;
            ``False`` if the cycle is not found or the allowance is zero.

        Notes
        -----
        .. warning::
            ``getTotalExpensesByCycle`` is called here with the full
            ``BudgetCycle`` **object** (``cycle``), whereas
            ``getCurrentBalance`` passes the integer ``cycleID``.  Ensure the
            DAO method handles both forms, or standardise the call signature.
        """
        cycle = self.budgetDAO.getCycleByCycleID(cycleID)
        if not cycle:
            return False

        # Pass the cycle object (not the ID) — see note in docstring above.
        total_spent     = self.transactionDAO.getTotalExpensesByCycle(cycle)
        total_allowance = Decimal(str(cycle.totalAllowance))

        if total_allowance == 0:
            return False  # Guard against zero-division on a zero-budget cycle.

        percentage = (total_spent / total_allowance) * 100
        return percentage >= 80

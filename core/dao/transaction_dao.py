"""
transaction_dao.py
==================
 
Data Access Object (DAO) for :class:`~core.models.Transaction` operations.
 
The :class:`TransactionDAO` class centralises all ORM interactions related
to financial transactions.  It is consumed exclusively by
:class:`~core.services.TransactionService` and
:class:`~core.services.BudgetService`.
"""
from core.models.transaction import Transaction
from decimal import Decimal


class TransactionDAO:
    """
    Provides database access methods for the
    :class:`~core.models.Transaction` model.
 
    All query and mutation methods that touch the ``Transaction`` table are
    defined here, keeping the service layer free from raw ORM calls.
 
    Design pattern: **Data Access Object (DAO)**.
    """

    def insertTransaction(self, budget_cycle, title, amount, transaction_type, category, date, description=''):
        """
        Create and persist a new :class:`~core.models.Transaction` record.
 
        :param budget_cycle: The cycle this transaction belongs to.
        :type budget_cycle: BudgetCycle
        :param title: Short label for the transaction (e.g. ``"Taxi"``).
        :type title: str
        :param amount: Monetary value (must be > 0).
        :type amount: Decimal
        :param transaction_type: ``'expense'`` or ``'income'``.
        :type transaction_type: str
        :param category: Spending category tag (e.g. ``"Transport"``).
        :type category: str | None
        :param date: Date the transaction occurred.
        :type date: datetime.date
        :param description: Optional free-text note. Defaults to ``''``.
        :type description: str
        :returns: The newly saved transaction instance.
        :rtype: Transaction
 
        Example::
 
            dao = TransactionDAO()
            tx = dao.insertTransaction(
                budget_cycle=cycle, title="Groceries",
                amount=Decimal("250.00"), transaction_type="expense",
                category="Food", date=date.today()
            )
        """
        # Create and save a new transaction to the database
        transaction = Transaction(
            budget_cycle=budget_cycle,
            title=title,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            date=date,
            description=description,
        )
        transaction.save()
        return transaction

    def getAllTransactions(self):
        """
        Return every transaction in the database.
 
        :returns: QuerySet of all :class:`~core.models.Transaction` records.
        :rtype: django.db.models.QuerySet[Transaction]
        """
        # """Return all transactions."""
        return Transaction.objects.all()

    def getTransactionsByCycle(self, budget_cycle):
        """
        Return all transactions belonging to a specific budget cycle.
 
        Results are ordered by ``-date`` then ``-created_at`` (newest first).
 
        :param budget_cycle: The cycle whose transactions to retrieve.
        :type budget_cycle: BudgetCycle
        :returns: Filtered and ordered QuerySet.
        :rtype: django.db.models.QuerySet[Transaction]
        """
        # """Return all transactions for a specific budget cycle."""
        return Transaction.objects.filter(budget_cycle=budget_cycle).order_by('-date', '-created_at')

    def getTransactionByID(self, transaction_id):
        """
        Retrieve a single transaction by its primary key.
 
        :param transaction_id: The ``id`` of the transaction to fetch.
        :type transaction_id: int
        :returns: The matching transaction, or ``None`` if not found.
        :rtype: Transaction | None
        """
        # """Return a single transaction by ID, or None if not found."""
        try:
            return Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return None

    def getTotalExpensesByCycle(self, budget_cycle):
        """
        Sum the amounts of all *expense* transactions in a cycle.
 
        Iterates over the filtered queryset and accumulates amounts as
        :class:`decimal.Decimal` to avoid floating-point errors.
 
        :param budget_cycle: The cycle to aggregate expenses for.
        :type budget_cycle: BudgetCycle
        :returns: Total expenses as a :class:`decimal.Decimal`. Returns
            ``Decimal('0')`` if there are no expense records.
        :rtype: Decimal
 
        Example::
 
            total = dao.getTotalExpensesByCycle(cycle)
            balance = Decimal(str(cycle.totalAllowance)) - total
        """
        # """Return the total amount of all expense transactions in a cycle."""
        expenses = Transaction.objects.filter(
            budget_cycle=budget_cycle,
            transaction_type='expense'
        )
        total = sum(t.amount for t in expenses)
        return Decimal(total)

    def deleteTransaction(self, transaction_id):
        """
        Delete a single transaction by its primary key.
 
        :param transaction_id: The ``id`` of the transaction to delete.
        :type transaction_id: int
        :returns: ``True`` if the transaction was found and deleted,
            ``False`` if no matching record exists.
        :rtype: bool
        """
        # """Delete a transaction by ID."""
        transaction = self.getTransactionByID(transaction_id)
        if transaction:
            transaction.delete()
            return True
        return False
    
    def getTransactionsByCategory(self, budget_cycle, category):
        """
        Filter transactions in a cycle by spending category.
 
        :param budget_cycle: The cycle to search within.
        :type budget_cycle: BudgetCycle
        :param category: The category string to match exactly
            (e.g. ``"Food"``).
        :type category: str
        :returns: QuerySet of matching transactions.
        :rtype: django.db.models.QuerySet[Transaction]
        """
        # Filter Transactions By Category
        return Transaction.objects.filter(
            budget_cycle=budget_cycle,
            category=category
        )
    
    def getTransactionsByDateRange(self, budget_cycle, start, end):
        """
        Filter transactions in a cycle that fall within a date range.
 
        Both ``start`` and ``end`` are inclusive.
 
        :param budget_cycle: The cycle to search within.
        :type budget_cycle: BudgetCycle
        :param start: Earliest date to include.
        :type start: datetime.date
        :param end: Latest date to include.
        :type end: datetime.date
        :returns: QuerySet of matching transactions.
        :rtype: django.db.models.QuerySet[Transaction]
        """
        # Filter Transactions by date
        return Transaction.objects.filter(
            budget_cycle=budget_cycle,
            date__gte=start,
            date__lte=end
        )

    def updateTransaction(self, transaction):
        """
        Persist changes to an existing transaction instance.
 
        :param transaction: A modified transaction instance to save.
        :type transaction: Transaction
        :returns: The updated transaction instance.
        :rtype: Transaction
        """
        # Update transaction
        transaction.save()
        return transaction

    def deleteAllTransactionsByCycle(self, budget_cycle):
        """
        Delete every transaction belonging to the given budget cycle.
 
        .. warning::
            This operation is irreversible.
 
        :param budget_cycle: The cycle whose transactions should be removed.
        :type budget_cycle: BudgetCycle
        :returns: None
        """
        # Delete all transactions
        Transaction.objects.filter(
            budget_cycle=budget_cycle
        ).delete()

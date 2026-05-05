"""
transaction.py
==============
 
Django model representing a single financial transaction.
 
Each :class:`Transaction` belongs to a :class:`~core.models.BudgetCycle`
and records the amount, category, type (expense / income), and date of one
spending or earning event.
"""
from django.db import models


class Transaction(models.Model):
    """
    Represents a single financial transaction within a budget cycle.
 
    Transactions are the core data unit of the application.  Each record
    captures what was spent (or earned), how much, when, and under which
    spending category.  Records are ordered newest-first by default.
 
    :Class Attributes:
 
        TRANSACTION_TYPES (list[tuple]):
            Enumeration of valid transaction kinds: ``'expense'`` and
            ``'income'``.
 
    :Instance Attributes:
 
        id (BigAutoField):
            Auto-incrementing primary key (Django default).
 
        budget_cycle (ForeignKey → BudgetCycle):
            The cycle this transaction belongs to.
            Deleting the cycle cascades to all its transactions.
            Reverse accessor: ``budget_cycle.transactions``.
 
        title (CharField):
            Short descriptive label, e.g. ``"Grocery run"`` (max 255 chars).
 
        amount (DecimalField):
            Monetary value with up to 10 digits and 2 decimal places.
 
        transaction_type (CharField):
            Either ``'expense'`` or ``'income'``.  Defaults to
            ``'expense'``.
 
        category (CharField):
            Optional spending category tag, e.g. ``"Food"`` (max 100 chars).
 
        date (DateField):
            Calendar date on which the transaction occurred.
 
        description (TextField):
            Optional free-text note about the transaction.
 
        created_at (DateTimeField):
            Timestamp set automatically when the record is first saved.
 
    :Meta:
        Records are ordered by ``-date`` then ``-created_at`` (newest first).
    """
    
    TRANSACTION_TYPES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]
    # ---------------------------------------
    # HENA h7ot el link l budgetCycle lma y5ls
    # ---------------------------------------
    budget_cycle = models.ForeignKey(
        'core.BudgetCycle',
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    title = models.CharField(max_length=255)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='expense')
    category = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Default queryset ordering: newest date first, then newest creation time."""
        ordering = ['-date', '-created_at']

    def __str__(self):
        """
        Return a concise string representation of the transaction.

        :returns: A label showing the title, amount, and transaction type.
        :rtype: str

        Example::

            str(tx)   # "Grocery run - 150.00 (expense)"
        """
        return f"{self.title} - {self.amount} ({self.transaction_type})"
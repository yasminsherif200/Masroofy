from core.models.transaction import Transaction
from decimal import Decimal


class TransactionDAO:

    @staticmethod
    def create_transaction(budget_cycle, title, amount, transaction_type, category, date, description=''):
        """Create and save a new transaction to the database."""
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

    @staticmethod
    def get_all_transactions():
        """Return all transactions."""
        return Transaction.objects.all()

    @staticmethod
    def get_transactions_by_cycle(budget_cycle):
        """Return all transactions for a specific budget cycle."""
        return Transaction.objects.filter(budget_cycle=budget_cycle)

    @staticmethod
    def get_transaction_by_id(transaction_id):
        """Return a single transaction by ID, or None if not found."""
        try:
            return Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return None

    @staticmethod
    def get_total_expenses_for_cycle(budget_cycle):
        """Return the total amount of all expense transactions in a cycle."""
        expenses = Transaction.objects.filter(
            budget_cycle=budget_cycle,
            transaction_type='expense'
        )
        total = sum(t.amount for t in expenses)
        return Decimal(total)

    @staticmethod
    def delete_transaction(transaction_id):
        """Delete a transaction by ID."""
        transaction = TransactionDAO.get_transaction_by_id(transaction_id)
        if transaction:
            transaction.delete()
            return True
        return False

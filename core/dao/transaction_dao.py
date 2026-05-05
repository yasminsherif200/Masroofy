from core.models.transaction import Transaction
from decimal import Decimal


class TransactionDAO:

    def insertTransaction(self, budget_cycle, title, amount, transaction_type, category, date, description=''):
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
        # """Return all transactions."""
        return Transaction.objects.all()

    def getTransactionsByCycle(self, budget_cycle):
        # """Return all transactions for a specific budget cycle."""
        return Transaction.objects.filter(budget_cycle=budget_cycle).order_by('-date', '-created_at')

    def getTransactionByID(self, transaction_id):
        # """Return a single transaction by ID, or None if not found."""
        try:
            return Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return None

    def getTotalExpensesByCycle(self, budget_cycle):
        # """Return the total amount of all expense transactions in a cycle."""
        expenses = Transaction.objects.filter(
            budget_cycle=budget_cycle,
            transaction_type='expense'
        )
        total = sum(t.amount for t in expenses)
        return Decimal(total)

    def deleteTransaction(self, transaction_id):
        # """Delete a transaction by ID."""
        transaction = self.getTransactionByID(transaction_id)
        if transaction:
            transaction.delete()
            return True
        return False
    
    def getTransactionsByCategory(self, budget_cycle, category):
        # Filter Transactions By Category
        return Transaction.objects.filter(
            budget_cycle=budget_cycle,
            category=category
        )
    
    def getTransactionsByDateRange(self, budget_cycle, start, end):
        # Filter Transactions by date
        return Transaction.objects.filter(
            budget_cycle=budget_cycle,
            date__gte=start,
            date__lte=end
        )

    def updateTransaction(self, transaction):
        # Update transaction
        transaction.save()
        return transaction

    def deleteAllTransactionsByCycle(self, budget_cycle):
        # Delete all transactions
        Transaction.objects.filter(
            budget_cycle=budget_cycle
        ).delete()

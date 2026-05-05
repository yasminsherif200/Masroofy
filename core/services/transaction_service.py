from core.dao import TransactionDAO
from core.dao import BudgetDAO
from decimal import Decimal

THRESHOLD_PERCENTAGE = Decimal('0.80')  # 80% alert threshold


class TransactionService:

    def __init__(self):
        self.transactionDAO = TransactionDAO()
        self.budgetDAO = BudgetDAO()

    def addExpense(self, budget_cycle, title, amount, category, date, description=''):
        # Validate and save a new expense transaction.
        # Returns a dict with 'transaction', 'success', 'error', and 'threshold_alert'.
        amount = Decimal(str(amount))

        # --- Validation ---
        if not title or not title.strip():
            return {'success': False, 'error': 'Title is required.'}

        if amount <= 0:
            return {'success': False, 'error': 'Amount must be greater than zero.'}

        if not date:
            return {'success': False, 'error': 'Date is required.'}

        # --- Save to DB ---
        transaction = self.transactionDAO.insertTransaction(
            budget_cycle=budget_cycle,
            title=title.strip(),
            amount=amount,
            transaction_type='expense',
            category=category,
            date=date,
            description=description,
        )

        # --- 80% Threshold Check (US#6) ---
        threshold_alert = self.checkThreshold(budget_cycle)

        return {
            'success': True,
            'transaction': transaction,
            'error': None,
            'threshold_alert': threshold_alert,
        }
    
    # Validate the amount of money is postive
    def validateAmount(self, amount):
        try:
            return Decimal(str(amount)) > 0
        except Exception:
            return False
        
    # Update Limit after any new transaction
    def calculateUpdatedDailyLimit(self, budget_cycle):
        from core.dao import BudgetDAO
        budget_dao = BudgetDAO()
        cycle = budget_dao.getCycleByCycleID(budget_cycle.cycleID)
        if not cycle:
            return 0
        total_expenses = self.transactionDAO.getTotalExpensesByCycle(budget_cycle)
        balance = Decimal(str(cycle.totalAllowance)) - total_expenses
        remaining_days = cycle.getRemainingDays()
        if remaining_days == 0:
            return 0
        return balance / remaining_days
    
    # filtering transactions
    def filterTransactions(self, budget_cycle, category=None, date=None):
        if category and date:
            return self.transactionDAO.getTransactionsByCategory(
                budget_cycle, category).filter(date=date)
        elif category:
            return self.transactionDAO.getTransactionsByCategory(
                budget_cycle, category)
        elif date:
            return self.transactionDAO.getTransactionsByDateRange(
                budget_cycle, date, date)
        return self.transactionDAO.getTransactionsByCycle(budget_cycle)
    

    def canEditExpense(self, transaction):
        from django.utils import timezone
        today = timezone.now().date()
        return transaction.date == today
    

    def canRemoveExpense(self, transaction_id):
        transaction = self.transactionDAO.getTransactionByID(transaction_id)
        if not transaction:
            return False
        from django.utils import timezone
        today = timezone.now().date()
        return transaction.date == today
    


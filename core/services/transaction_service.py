from dao.transaction_dao import TransactionDAO
from decimal import Decimal

THRESHOLD_PERCENTAGE = Decimal('0.80')  # 80% alert threshold


class TransactionService:

    @staticmethod
    def add_expense(budget_cycle, title, amount, category, date, description=''):
        """
        Validate and save a new expense transaction.
        Returns a dict with 'transaction', 'success', 'error', and 'threshold_alert'.
        """
        amount = Decimal(str(amount))

        # --- Validation ---
        if not title or not title.strip():
            return {'success': False, 'error': 'Title is required.'}

        if amount <= 0:
            return {'success': False, 'error': 'Amount must be greater than zero.'}

        if not date:
            return {'success': False, 'error': 'Date is required.'}

        # --- Save to DB ---
        transaction = TransactionDAO.create_transaction(
            budget_cycle=budget_cycle,
            title=title.strip(),
            amount=amount,
            transaction_type='expense',
            category=category,
            date=date,
            description=description,
        )

        # --- 80% Threshold Check (US#6) ---
        threshold_alert = TransactionService.check_threshold(budget_cycle)

        return {
            'success': True,
            'transaction': transaction,
            'error': None,
            'threshold_alert': threshold_alert,
        }

    @staticmethod
    def check_threshold(budget_cycle):
        """
        Check if total expenses have reached or exceeded 80% of the budget cycle limit.
        Returns True if alert should be shown, False otherwise.
        """
        try:
            budget_limit = Decimal(str(budget_cycle.budget_limit))
        except AttributeError:
            # If BudgetCycle doesn't have budget_limit yet, skip alert
            return False

        if budget_limit <= 0:
            return False

        total_expenses = TransactionDAO.get_total_expenses_for_cycle(budget_cycle)
        percentage_used = total_expenses / budget_limit

        return percentage_used >= THRESHOLD_PERCENTAGE

    @staticmethod
    def get_transactions_for_cycle(budget_cycle):
        """Return all transactions for a given budget cycle."""
        return TransactionDAO.get_transactions_by_cycle(budget_cycle)

from core.dao import BudgetDAO
from models.budget_cycle import BudgetCycle
from datetime import datetime

class BudgetService:
    # This method creates a new budget cycle for a user, ensuring that there are no active cycles before creating a new one.
    @staticmethod
    def create_new_budget(user, amount, duration_days=30):#30 is adefult value 
        existing_cycle = BudgetDAO.getActiveCycle(user.id)
        if existing_cycle:
            return "Error: User already has an active budget cycle."

        new_cycle = BudgetCycle(
            user=user,
            totalAllowance=amount,
            remainingBalance=amount,
            startDate=datetime.now(),
            isActive=True
        )
        return BudgetDAO.saveCycle(new_cycle)
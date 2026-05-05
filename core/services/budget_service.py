from core.dao import BudgetDAO
from core.dao import TransactionDAO
from core.models import BudgetCycle
from datetime import datetime

class BudgetService:

    def __init__(self):
        self.budgetDAO = BudgetDAO()
        self.transactionDAO = TransactionDAO()

    # Methods
    def isFirstTime(self, userID):
        cycle = self.budgetDAO.getActiveCycle(userID)
        return cycle is None
    
    def validateAmount(self, amount):
        return amount > 0
    
    def validateDate(self, start, end):
        return end > start
    
    def calculateDailyLimit(self, amount, days):
        if days == 0:
            return 0
        return amount / days
    
    def createNewCycle(self, userID, amount, start, end):
        if not self.validateAmount(amount):
            return False
        if not self.validateDate(start, end):
            return False
        days = (end - start).days
        daily_limit = self.calculateDailyLimit(amount, days)
        from core.models import User
        user = User.objects.get(userID=userID)
        cycle = BudgetCycle(
            user=user,
            totalAllowance= amount,
            dailyLimit=     daily_limit,
            startDate=      start,
            endDate=        end
        )
        self.budgetDAO.saveCycle(cycle)
        return True
    
    def getSafeDailyLimit(self, cycleID):
        balance = self.getCurrentBalance(cycleID)
        days = self.getRemainingDays(cycleID)
        if days == 0:
            return 0
        return balance / days

    def getRemainingDays(self, cycleID):
        cycle = self.budgetDAO.getCycleByCycleID(cycleID)
        if not cycle:
            return 0
        return cycle.getRemainingDays()
        
    def getCurrentBalance(self, cycleID):
        cycle = self.budgetDAO.getCycleByCycleID(cycleID)
        if not cycle:
            return 0
        total_spent = self.transactionDAO.getTotalExpensesByCycle(cycleID)
        return cycle.totalAllowance - total_spent

    def calculateCategoryPercentages(self, cycleID):
        from core.models import Transaction
        from django.db.models import Sum
        results = Transaction.objects.filter(
            cycle_id=cycleID
        ).values('category').annotate(
            total=Sum('amount')
        )
        total_spent = sum(r['total'] for r in results)
        if total_spent == 0:
            return {}
        return {
            r['category']: round(
                (r['total'] / total_spent) * 100, 2
            )
            for r in results
        }        

    def resetCurrentCycle(self, cycleID):
        self.budgetDAO.deleteCycle(cycleID)
        return True
    
    def checkThreshold(self, cycleID):
        cycle = self.budgetDAO.getCycleByCycleID(cycleID)
        if not cycle:
            return False
        total_spent = self.transactionDAO.getTotalExpensesByCycle(cycle)
        percentage = (total_spent / cycle.totalAllowance) * 100
        return percentage >= 80


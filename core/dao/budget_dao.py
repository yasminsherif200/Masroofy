from core.models import BudgetCycle
class BudgetDAO:
    def saveCycle(self, budget_cycle_obj):
        budget_cycle_obj.save() # Save the budget cycle object to the database. If it already exists, it will be updated.
        return budget_cycle_obj
   
    def getActiveCycle(self, userID):
        #if there is an active cycle for the user, return it otherwise, return None.
        try:
            return BudgetCycle.objects.filter(user_id=userID).last()
        except BudgetCycle.DoesNotExist:
            return None

    def deleteCycle(self, cycleID):
        BudgetCycle.objects.filter(cycleID=cycleID).delete()
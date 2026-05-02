from ..models.budget_cycle import BudgetCycle
class BudgetDAO:
   
    # Static method to save or update a budget cycle in the database.
    @staticmethod #
    def saveCycle(budget_cycle_obj):
        budget_cycle_obj.save() # Save the budget cycle object to the database. If it already exists, it will be updated.
        return budget_cycle_obj

    @staticmethod
    def getActiveCycle(userID):
        #if there is an active cycle for the user, return it; otherwise, return None.
        try:
            return BudgetCycle.objects.get(user_id=userID, isActive=True)
        except BudgetCycle.DoesNotExist:
            return None

    @staticmethod
    def deleteCycle(cycleID):
        BudgetCycle.objects.filter(cycleID=cycleID).delete()
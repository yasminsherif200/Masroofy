from django.db import models
from .user import User

class BudgetCycle(models.Model):
    cycleID = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    totalAllwance = models.FloatField()
    remainingAllwance = models.FloatField()
    startDate = models.DateField()
    endDate = models.DateField()
    isActive = models.BooleanField(default=True)

    def get_spending_percentage(self):
        if self.totalAllwance == 0:
            return 0
        spent = self.totalAllwance - self.remainingAllwance # Calculate the amount spent
        return (spent / self.totalAllwance) * 100
    
    def __str__(self):
        return f"Cycle {self.cycleID} for {self.user.username}"
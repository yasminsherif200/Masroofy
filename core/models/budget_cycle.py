from django.db import models
from .user import User

class BudgetCycle(models.Model):
    # Attributes
    cycleID = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    totalAllowance = models.FloatField()
    dailyLimit = models.FloatField()
    startDate = models.DateField()
    endDate = models.DateField()

    # Methods
    def getRemainingDays(self):
        from django.utils import timezone
        today = timezone.now().date()
        delta = self.endDate - today
        return max(delta.days, 0)
    
    def getWeeklyLimit(self):
        return self.dailyLimit * 7
    
    def __str__(self):
        return f"Cycle {self.cycleID} for {self.user.userName}"
    
    class Meta:
        db_table = 'budget_cycles'

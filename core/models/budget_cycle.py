"""
budget_cycle.py
===============
 
Django model representing a user's budget cycle (planning period).
 
A :class:`BudgetCycle` captures the total allowance and date range for
one spending period.  Helper methods expose derived values such as the
number of remaining days and a computed weekly spending limit.
"""

from django.db import models
from .user import User

class BudgetCycle(models.Model):
    """
    Represents a single budget cycle for a user.
 
    A budget cycle is a time-bounded spending plan.  It records how much
    money the user has allocated (``totalAllowance``), how much they may
    spend per day (``dailyLimit``), and the start/end dates of the period.
 
    :Attributes:
 
        cycleID (AutoField):
            Auto-incrementing primary key.
 
        user (ForeignKey → User):
            The owner of this budget cycle.
            Deleting the user cascades and removes all related cycles.
 
        totalAllowance (FloatField):
            Total money budgeted for the cycle, in the user's preferred currency.
 
        dailyLimit (FloatField):
            Recommended spending cap per day
            (``totalAllowance / number_of_days``).
 
        startDate (DateField):
            First day of the budget period (inclusive).
 
        endDate (DateField):
        Last day of the budget period (inclusive).
    """ 
           
    # Attributes
    cycleID = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    totalAllowance = models.FloatField()
    dailyLimit = models.FloatField()
    startDate = models.DateField()
    endDate = models.DateField()

    # Methods
    def getRemainingDays(self):
        """
        Calculate the number of days left in the budget cycle.
 
        Compares today's date against :attr:`endDate`.  Returns ``0`` if
        the cycle has already ended (never negative).
 
        :returns: Days remaining until the cycle ends, minimum ``0``.
        :rtype: int
 
        Example::
 
            cycle.endDate = date(2026, 12, 31)
            cycle.getRemainingDays()   # e.g. 240
        """
        from django.utils import timezone
        today = timezone.now().date()
        delta = self.endDate - today
        return max(delta.days, 0)
    
    def getWeeklyLimit(self):
        """
        Compute the recommended weekly spending limit.
 
        Multiplies :attr:`dailyLimit` by 7.  Useful for weekly budget
        summaries shown in the dashboard.
 
        :returns: Weekly spending cap derived from the daily limit.
        :rtype: float
 
        Example::
 
            cycle.dailyLimit = 100.0
            cycle.getWeeklyLimit()   # 700.0
        """
        return self.dailyLimit * 7
    
    def __str__(self):
        """
        Return a concise string representation of the cycle.
 
        :returns: A label combining the cycle ID and the owner's username.
        :rtype: str
 
        Example::
 
            str(cycle)   # "Cycle 3 for Ahmed"
        """
        
        return f"Cycle {self.cycleID} for {self.user.userName}"
    

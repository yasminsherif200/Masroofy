"""
budget_dao.py
=============
 
Data Access Object (DAO) for :class:`~core.models.BudgetCycle` operations.
 
The :class:`BudgetDAO` class centralises all ORM queries that read or
write budget cycle records.  Higher-level business logic lives in
:class:`~core.services.BudgetService`, which delegates all persistence
concerns to this class.
"""
from core.models import BudgetCycle
class BudgetDAO:
    """
    Provides database access methods for the
    :class:`~core.models.BudgetCycle` model.
 
    Design pattern: **Data Access Object (DAO)** — keeps the service layer
    free of raw ORM calls and makes data access easy to mock in tests.
    """
    def saveCycle(self, budget_cycle_obj):
        """
        Persist a :class:`~core.models.BudgetCycle` instance to the database.
 
        Calls Django's ``save()`` method, which performs an ``INSERT`` for
        new objects or an ``UPDATE`` for existing ones (identified by their
        primary key).
 
        :param budget_cycle_obj: The cycle instance to save.
        :type budget_cycle_obj: BudgetCycle
        :returns: The saved (and potentially pk-populated) instance.
        :rtype: BudgetCycle
 
        Example::
 
            dao = BudgetDAO()
            cycle = BudgetCycle(user=user, totalAllowance=5000, ...)
            saved = dao.saveCycle(cycle)
            print(saved.cycleID)   # auto-assigned primary key
        """ 
        budget_cycle_obj.save() # Save the budget cycle object to the database. If it already exists, it will be updated.
        return budget_cycle_obj
   
    def getActiveCycle(self, userID):
        """
        Retrieve the most recent budget cycle for the given user.
 
        Uses ``.last()`` on a filtered queryset (ordered by ``cycleID``)
        to return the newest cycle.  Returns ``None`` when no cycle exists
        for the user.
 
        :param userID: Primary key of the :class:`~core.models.User` to
            look up cycles for.
        :type userID: int
        :returns: The latest :class:`~core.models.BudgetCycle`, or
            ``None`` if the user has no cycles yet.
        :rtype: BudgetCycle | None
 
        Example::
 
            dao = BudgetDAO()
            cycle = dao.getActiveCycle(userID=1)
            if cycle is None:
                # First-time user — prompt for budget setup
                ...
        """
        #if there is an active cycle for the user, return it otherwise, return None.
        try:
            return BudgetCycle.objects.filter(user_id=userID).last()
        except BudgetCycle.DoesNotExist:
            return None

    def deleteCycle(self, cycleID):
        """
        Permanently delete a budget cycle by its primary key.
 
        Because :class:`~core.models.Transaction` has
        ``on_delete=CASCADE``, all transactions linked to this cycle are
        also deleted from the database.
 
        :param cycleID: Primary key of the cycle to remove.
        :type cycleID: int
        :returns: None
 
        .. warning::
            This operation is irreversible.  All associated transactions
            are deleted along with the cycle.
 
        Example::
 
            dao = BudgetDAO()
            dao.deleteCycle(cycleID=3)   # cycle and its transactions gone
        """
        BudgetCycle.objects.filter(cycleID=cycleID).delete()

    # get cycle by its ID
    def getCycleByCycleID(self, cycleID):
        """
        Retrieve a specific budget cycle by its primary key.
 
        :param cycleID: The ``cycleID`` to look up.
        :type cycleID: int
        :returns: The matching :class:`~core.models.BudgetCycle`, or
            ``None`` if no cycle with that ID exists.
        :rtype: BudgetCycle | None
 
        Example::
 
            dao = BudgetDAO()
            cycle = dao.getCycleByCycleID(2)
            if cycle:
                print(cycle.totalAllowance)
        """
        try:
            return BudgetCycle.objects.get(cycleID=cycleID)
        except BudgetCycle.DoesNotExist:
            return None
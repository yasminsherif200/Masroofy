"""
user_service.py
===============
 
Business-logic layer for user authentication and profile management.
 
The :class:`UserService` class orchestrates PIN hashing, credential
persistence (via :class:`~core.dao.UserDAO`), and a simple in-memory
brute-force lock after three consecutive failed login attempts.
 
.. note::
    The lock state (``failedAttempts``, ``isLocked``) is **instance-level**
    and therefore resets on every new request in a stateless Django
    environment.  For persistent locking, move this state to the database
    or session.
"""
from core.dao import UserDAO
import hashlib

class UserService:
    """
    Handles authentication and credential management for the single user.
 
    Wraps :class:`~core.dao.UserDAO` and adds:
 
    * PIN hashing (SHA-256) before any storage call.
    * Failed-attempt tracking with an automatic lock after 3 failures.
    * Helper methods for updating individual profile fields.
 
    :Attributes:
 
        userDAO (UserDAO):
            DAO instance used for all database reads/writes.
 
        failedAttempts (int):
            Counter of consecutive incorrect PIN entries since the last
            successful login.  Resets to ``0`` on success.
 
        isLocked (bool):
            ``True`` when ``failedAttempts >= 3``.  While locked,
            :meth:`verifyLogin` always returns ``False``.
    """
    def __init__(self):
        """
        Initialise the service with a fresh :class:`~core.dao.UserDAO`
        instance and zeroed lock counters.
        """
        self.userDAO = UserDAO()
        self.failedAttempts = 0
        self.isLocked = False

    # called to hash the pin before saving in database in signup
    def updateSecurity(self, userName, pin, enabled): 
        """
        Hash the PIN and persist the user's credentials.
 
        Called during initial sign-up or when the user changes their PIN.
        The raw PIN is **never** stored; only its SHA-256 hex digest is
        passed to the DAO.
 
        :param userName: Display name to save alongside the hashed PIN.
        :type userName: str
        :param pin: Numeric PIN entered by the user (plain text).
        :type pin: int | str
        :param enabled: Flag indicating whether PIN security is active.
        :type enabled: bool
        :returns: None
 
        Example::
 
            svc = UserService()
            svc.updateSecurity("Ahmed", 1234, True)
        """
        
        hashed = hashlib.sha256(str(pin).encode()).hexdigest()
        self.userDAO.saveUserCredentials(userName, hashed, enabled) 

    # handle multiple failed tries
    def handleFailedAttempts(self):
        """
        Increment the failed-login counter and lock the account if
        three consecutive failures have occurred.
 
        Called internally by :meth:`verifyLogin` on each wrong PIN entry.
        Sets :attr:`isLocked` to ``True`` when :attr:`failedAttempts`
        reaches ``3``.
 
        :returns: None
        """
        self.failedAttempts += 1
        if self.failedAttempts >= 3:
            self.isLocked = True

    # called during login
    def verifyLogin(self, pin):
        """
        Verify a PIN against the stored hash and enforce the brute-force lock.
 
        Steps:
 
        1. Return ``False`` immediately if :attr:`isLocked` is ``True``.
        2. Fetch the user record; return ``False`` if none exists.
        3. Hash the supplied PIN and compare with the stored digest.
        4. On match — reset :attr:`failedAttempts` and return ``True``.
        5. On mismatch — call :meth:`handleFailedAttempts` and return ``False``.
 
        :param pin: The PIN entered by the user at the login screen.
        :type pin: int | str
        :returns: ``True`` if the PIN matches and the account is not locked,
            ``False`` otherwise.
        :rtype: bool
 
        Example::
         svc = UserService()
            if svc.verifyLogin(1234):
                # redirect to dashboard
                ...
            else:
                # show error / lock warning
                ...
        """
        if self.isLocked:
            return False
        
        user = self.userDAO.getUserSecurityData()
        if user is None:
            return False
        hashed = hashlib.sha256(str(pin).encode()).hexdigest()
        if hashed == user.hashedPIN:
            self.failedAttempts = 0
            return True
        else:
            self.handleFailedAttempts()
            return False

    # called if user updated only the username without the pin
    def updateUserName(self, userName): 
        """
        Update only the display name, leaving the PIN unchanged.
 
        Retrieves the current hashed PIN from the database and re-saves it
        together with the new username.  Used when the user edits their
        profile without touching their PIN.
 
        :param userName: The new display name to persist.
        :type userName: str
        :returns: None
 
        Example::
 
            svc = UserService()
            svc.updateUserName("Ali")
        """
        
        user = self.userDAO.getUserSecurityData()
        self.userDAO.saveUserCredentials(
            userName, user.hashedPIN, True
        )
    
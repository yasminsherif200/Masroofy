from core.dao import UserDAO
import hashlib

class UserService:
    # Methods

    # create instances
    def __init__(self):
        self.userDAO = UserDAO()
        self.failedAttempts = 0
        self.isLocked = False

    # called to hash the pin before saving in database in signup
    def updateSecurity(self, userName, pin, enabled):
        hashed = hashlib.sha256(str(pin).encode()).hexdigest()
        self.userDAO.saveUserCredentials(userName, hashed, enabled) 

    # handle multiple failed tries
    def handleFailedAttempts(self):
        self.failedAttempts += 1
        if self.failedAttempts >= 3:
            self.isLocked = True

    # called during login
    def verifyLogin(self, pin):
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

    
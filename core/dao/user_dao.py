from core.models import User

class UserDAO:
    # Methods

    # if new user -> Create in db, else -> update in db
    def saveUserCredentials(self, username, hash, isEnabled):
        User.objects.update_or_create(
            userID = 1,
            defaults= {
                'hashedPIN': hash,
                'userName': username, 
            }
        )

    # return the first and only user in db
    def getUserSecurityData(self):
        try:
            return User.objects.first()
        except Exception:
            return None

    
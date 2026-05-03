from django.db import models

class User(models.Model):
    # Attributes
    userID = models.AutoField(primary_key=True)
    userName = models.CharField(max_length=64)
    hashedPIN = models.CharField(max_length=256)
    preferredCurrency = models.CharField(max_length=10, default='EGP')

    # Methods
    def getUserName(self):
        return self.userName
    def __str__(self):
        return (f"User ID: {self.userID},\nUser Name: {self.userName}")
    
    class Meta:
        db_table = 'users'
"""
user.py
=======
 
Django model representing the application's single user account.
 
This module defines the :class:`User` model, which stores authentication
credentials and display preferences for the budget-tracking application.
 
.. note::
    The application is designed for a single-user setup (``userID`` is
    always ``1``). Multi-user support would require migrating this model.
"""
from django.db import models

class User(models.Model):
    """
    Represents the application's user account.
 
    Stores a display name, a hashed PIN for authentication, and the
    user's preferred display currency.  Because the app is single-user,
    only one row is expected in this table (``userID = 1``).
 
    :Attributes:
 
        userID (AutoField):
            Auto-incrementing primary key.
 
        userName (CharField):
            Human-readable display name, up to 64 characters.
 
        hashedPIN (CharField):
            SHA-256 hex digest of the user's numeric PIN.
            Plain-text PINs are **never** stored.
 
        preferredCurrency (CharField):
            ISO 4217 currency code shown in the UI (default: ``'EGP'``).
    """
    # Attributes
    userID = models.AutoField(primary_key=True)
    userName = models.CharField(max_length=64)
    hashedPIN = models.CharField(max_length=256)
    preferredCurrency = models.CharField(max_length=10, default='EGP')

    # Methods
    def getUserName(self):
        """
        Return the user's display name.
 
        :returns: The value of :attr:`userName`.
        :rtype: str
 
        Example::
 
            user = User.objects.first()
            print(user.getUserName())   # "Ahmed"
        """
        return self.userName
    def __str__(self):
        """
        Return a human-readable string representation of the user.
 
        :returns: A multi-line string containing the user ID and name.
        :rtype: str
 
        Example::
 
            str(user)
            # "User ID: 1,\\nUser Name: Ahmed"
        """
        return (f"User ID: {self.userID},\nUser Name: {self.userName}")
    
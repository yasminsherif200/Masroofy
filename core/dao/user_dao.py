"""
user_dao.py
===========

Data Access Object (DAO) for :class:`~core.models.User` database operations.

The :class:`UserDAO` class isolates all direct ORM queries related to the
single application user, keeping business logic in the service layer clean
and database interactions in one place.
"""

from core.models import User


class UserDAO:
    """
    Provides database access methods for the :class:`~core.models.User` model.

    Because the application is single-user, all write operations target the
    row with ``userID = 1`` via ``update_or_create``.  Read operations
    simply return the first (and only) user record.

    Design pattern: **Data Access Object (DAO)** — isolates persistence
    logic from business rules defined in :class:`~core.services.UserService`.
    """

    # ── Methods ─────────────────────────────────────────────────────────

    def saveUserCredentials(self, username, hash, isEnabled):
        """
        Create or update the user's login credentials in the database.

        Uses Django's ``update_or_create`` targeting ``userID = 1``.
        If no user exists yet a new row is inserted; otherwise the
        existing row is updated with the supplied values.

        :param username: The display name to store.
        :type username: str
        :param hash: SHA-256 hex digest of the user's PIN.
        :type hash: str
        :param isEnabled: Reserved flag indicating whether security is
            active (not currently persisted to a model field, kept for
            interface compatibility).
        :type isEnabled: bool
        :returns: None

        Example::

            dao = UserDAO()
            dao.saveUserCredentials("Ahmed", "ab3f...", True)
        """
        User.objects.update_or_create(
            userID=1,
            defaults={
                'hashedPIN': hash,
                'userName': username,
            }
        )

    def getUserSecurityData(self):
        """
        Retrieve the single application user record.

        :returns: The first :class:`~core.models.User` row, or ``None``
            if no user has been created yet or an exception occurs.
        :rtype: User | None

        Example::

            dao = UserDAO()
            user = dao.getUserSecurityData()
            if user:
                print(user.hashedPIN)
        """
        try:
            return User.objects.first()
        except Exception:
            return None

    
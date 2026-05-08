"""
Test Suite – core
==================

Contains automated tests for the **core** application using Django's
built-in test framework (a thin wrapper around Python's ``unittest``).

Running the tests
-----------------
.. code-block:: bash

    python manage.py test core          # run all core tests
    python manage.py test core.tests    # target this module explicitly
    python manage.py test core --verbosity=2  # detailed output

Test Areas to Cover
--------------------
The following test classes should be added to ensure adequate coverage:

``AuthTests``
    * ``GET /`` renders the login template.
    * ``POST /`` with valid credentials redirects to ``/dashboard/``.
    * ``POST /`` with invalid credentials re-renders the form with errors.
    * ``GET /signup/`` renders the signup template.
    * ``POST /signup/`` with valid data creates a user and redirects.
    * ``GET /logout/`` clears the session and redirects to ``/``.

``SetupTests``
    * Unauthenticated access to ``/setup/`` redirects to login.
    * ``POST /setup/`` with valid data creates a ``BudgetCycle`` record.

``DashboardTests``
    * Authenticated ``GET /dashboard/`` returns HTTP 200.
    * Dashboard context includes expected spending totals.

``ExpenseTests``
    * ``POST /add-expense/`` with valid data creates a ``Transaction``.
    * ``POST /add-expense/`` with a negative amount returns a form error.

``HistoryTests``
    * ``GET /history/`` lists the user's transactions.
    * ``POST /delete-transaction/<id>/`` removes the correct record.
    * ``POST /edit-transaction/<id>/`` updates the correct record.

``ReportsTests``
    * ``GET /reports/`` returns HTTP 200.
    * Report context contains category breakdown data.

``SettingsTests``
    * ``POST /settings/`` persists preference changes.
    * ``POST /reset-cycle/`` creates a new ``BudgetCycle`` and
      archives the previous one.

Example skeleton
----------------
.. code-block:: python

    from django.test import TestCase, Client
    from django.contrib.auth.models import User
    from django.urls import reverse

    class AuthTests(TestCase):
        def setUp(self):
            self.client = Client()
            self.user = User.objects.create_user(
                username='testuser', password='securepassword123'
            )

        def test_login_page_loads(self):
            response = self.client.get(reverse('login'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'core/login.html')

        def test_login_with_valid_credentials(self):
            response = self.client.post(reverse('login'), {
                'username': 'testuser',
                'password': 'securepassword123',
            })
            self.assertRedirects(response, reverse('dashboard'))

        def test_login_with_invalid_credentials(self):
            response = self.client.post(reverse('login'), {
                'username': 'testuser',
                'password': 'wrongpassword',
            })
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'error')

References
----------
Django testing documentation:
    https://docs.djangoproject.com/en/6.0/topics/testing/
"""

from django.test import TestCase

# Create your tests here.

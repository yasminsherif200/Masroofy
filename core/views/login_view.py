"""
Login View – core.views.login_view
====================================

Handles all authentication-related HTTP requests: PIN-based login, new user
registration (signup), and session termination (logout).

Authentication Model
--------------------
This application uses a **single-user, PIN-based** authentication model
rather than Django's built-in username/password system.  The authenticated
user's primary key is stored in the session under the key ``'user_id'``.

Session Key
-----------
``request.session['user_id']``
    Set to ``user.userID`` on successful login or signup.
    Absent (or ``None``) when no user is authenticated.

Dependencies
------------
``core.services.UserService``
    Business-logic layer; handles PIN verification, lockout tracking, and
    security-data updates.
``core.dao.UserDAO``
    Data-access layer; retrieves the persisted user record from the database.

Module-level Singletons
-----------------------
``user_service``
    Shared ``UserService`` instance reused across all requests in this module.
``user_dao``
    Shared ``UserDAO`` instance reused across all requests in this module.
"""

from django.shortcuts import render, redirect
from core.services import UserService
from core.dao import UserDAO

#: Shared service instance for user business logic (PIN verification, lockout).
user_service = UserService()

#: Shared DAO instance for direct database reads of user security data.
user_dao = UserDAO()


def login(request):
    """
    Display the login form and authenticate the user via PIN.

    **GET** – Renders the login page (``core/login.html``).  If the user is
    already authenticated (session contains ``'user_id'``), they are
    immediately redirected to the dashboard.

    **POST** – Reads the ``pin`` field from the request body and delegates
    verification to ``UserService.verifyLogin()``.

    * On success: stores ``user.userID`` in the session and redirects to
      ``'dashboard'``.
    * On failure – locked account: re-renders the login page with a lockout
      error message.
    * On failure – wrong PIN: re-renders the login page with a generic
      incorrect-PIN error message.

    Parameters
    ----------
    request : django.http.HttpRequest
        The incoming HTTP request.

    Returns
    -------
    django.http.HttpResponse
        A redirect or a rendered ``core/login.html`` template.

    Template context
    ----------------
    ``error`` : str, optional
        Human-readable error message displayed in red on the login form.
    """
    # Already authenticated — skip the login page entirely.
    if request.session.get('user_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        pin = request.POST.get('pin')
        is_valid = user_service.verifyLogin(pin)

        if is_valid:
            user = user_dao.getUserSecurityData()
            # Persist the authenticated user's ID for the duration of the session.
            request.session['user_id'] = user.userID
            return redirect('dashboard')
        else:
            if user_service.isLocked:
                # Account is temporarily locked after too many failed attempts.
                return render(request, 'core/login.html', {
                    'error': 'Too many failed attempts. Try again later.'
                })
            else:
                return render(request, 'core/login.html', {
                    'error': 'Incorrect PIN. Please try again.'
                })

    # GET request — render the blank login form.
    return render(request, 'core/login.html')


def signup(request):
    """
    Display the registration form and create a new user account.

    **GET** – Renders the signup page (``core/signup.html``).  If the user is
    already authenticated they are redirected to the dashboard.

    **POST** – Validates the submitted form fields:

    1. Ensures ``userName``, ``pin``, and ``confirmPin`` are all present.
    2. Checks that ``pin`` and ``confirmPin`` match.
    3. Calls ``UserService.updateSecurity()`` to persist the new credentials.
    4. Retrieves the newly created user record and stores its ID in the session.
    5. Redirects to the budget-setup wizard (``'setup'``).

    Parameters
    ----------
    request : django.http.HttpRequest
        The incoming HTTP request.

    Returns
    -------
    django.http.HttpResponse
        A redirect to ``'setup'`` on success, or a rendered
        ``core/signup.html`` with validation errors on failure.

    Template context
    ----------------
    ``error`` : str, optional
        Human-readable validation error displayed in red on the signup form.

    Notes
    -----
    * New users are redirected to ``'setup'`` (budget configuration) rather
      than ``'dashboard'`` because no budget cycle exists yet.
    * Field names in the POST body: ``userName``, ``pin``, ``confirmPin``.
    """
    # Already authenticated — no need to sign up again.
    if request.session.get('user_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        userName   = request.POST.get('userName')
        pin        = request.POST.get('pin')
        confirmPin = request.POST.get('confirmPin')

        # Validate: all fields must be supplied.
        if not userName or not pin or not confirmPin:
            return render(request, 'core/signup.html', {
                'error': 'All fields are required.'
            })

        # Validate: PIN and confirmation must match.
        if pin != confirmPin:
            return render(request, 'core/signup.html', {
                'error': 'PINs do not match. Please try again.'
            })

        # Persist the new user credentials via the service layer.
        user_service.updateSecurity(userName, pin, True)

        # Immediately authenticate the new user so they don't have to log in.
        user = user_dao.getUserSecurityData()
        request.session['user_id'] = user.userID
        return redirect('setup')

    return render(request, 'core/signup.html')


def logout(request):
    """
    Terminate the current user session and redirect to the login page.

    Calls ``request.session.flush()`` which deletes all session data **and**
    regenerates the session key, preventing session-fixation attacks.

    Parameters
    ----------
    request : django.http.HttpRequest
        The incoming HTTP request (GET or POST — method is not checked).

    Returns
    -------
    django.http.HttpResponseRedirect
        Redirect to the ``'login'`` URL.
    """
    # Destroy all session data and rotate the session key.
    request.session.flush()
    return redirect('login')

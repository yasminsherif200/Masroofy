"""
App Configuration – core
=========================

Defines the Django ``AppConfig`` subclass for the **core** application.
Django uses this class to hook into application startup events and to
supply metadata (app label, verbose name, etc.) about the application.

The configuration is referenced in ``masroofy/settings.py`` via::

    INSTALLED_APPS = [
        ...
        'core.apps.CoreConfig',
    ]

References
----------
Django application configuration:
    https://docs.djangoproject.com/en/6.0/ref/applications/
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Application configuration for the ``core`` app.

    Attributes
    ----------
    name : str
        The full Python path to the application package.  Must match the
        directory name (``core``) so Django can locate the app's models,
        views, and templates.
    """

    name = 'core'

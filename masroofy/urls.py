"""
Root URL Configuration – masroofy
===================================

Maps top-level URL prefixes to sub-applications.  Django loads this module
because it is referenced by ``ROOT_URLCONF = 'masroofy.urls'`` in
``masroofy/settings.py``.

URL Patterns
------------
``/admin/``
    Django's built-in admin interface.

``/`` (prefix-less)
    Delegates all remaining URL resolution to ``core/urls.py`` via
    ``include('core.urls')``.  This keeps routing concerns inside the
    ``core`` app and makes it easier to mount the app under a different
    prefix in future (e.g. ``path('app/', include('core.urls'))``).

References
----------
Django URL dispatcher:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin site — available at /admin/
    path('admin/', admin.site.urls),

    # Delegate all other URL patterns to the core application.
    # core/urls.py defines the full set of user-facing routes.
    path('', include('core.urls')),
]

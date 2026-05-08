"""
WSGI Configuration – masroofy
==============================

Exposes the WSGI-compatible callable ``application`` that traditional,
synchronous web servers (e.g. Gunicorn, uWSGI, mod_wsgi) use to communicate
with this Django project.

The module-level ``application`` variable is the single entry-point required
by the WSGI specification (PEP 3333).

References
----------
Django WSGI deployment docs:
    https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Point Django at the project settings before the application object is built.
# This must happen before any Django models or settings are imported.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masroofy.settings')

#: The WSGI application callable consumed by the web server.
application = get_wsgi_application()

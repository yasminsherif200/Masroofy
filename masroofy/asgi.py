"""
ASGI Configuration – masroofy
==============================

Exposes the ASGI-compatible callable ``application`` that async-capable web
servers (e.g. Daphne, Uvicorn, Hypercorn) use to communicate with this
Django project.

The module-level ``application`` variable is the single entry-point required
by the ASGI specification (PEP 3333 / ASGI v3).

References
----------
Django ASGI deployment docs:
    https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Point Django at the project settings before the application object is built.
# This must happen before any Django models or settings are imported.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masroofy.settings')

#: The ASGI application callable consumed by the web server.
application = get_asgi_application()

"""
Admin Registration – core
==========================

Registers ``core`` models with Django's built-in admin interface, making
them manageable through the ``/admin/`` site without writing custom views.

Usage
-----
To expose a model in the admin, import it and call ``admin.register()``:

.. code-block:: python

    from django.contrib import admin
    from .models import Transaction, BudgetCycle

    @admin.register(Transaction)
    class TransactionAdmin(admin.ModelAdmin):
        list_display  = ('user', 'amount', 'category', 'date')
        list_filter   = ('category',)
        search_fields = ('description',)

    admin.site.register(BudgetCycle)

References
----------
Django admin documentation:
    https://docs.djangoproject.com/en/6.0/ref/contrib/admin/
"""

from django.contrib import admin

# Register your models here.

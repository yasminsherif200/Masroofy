"""
Forms – core
=============

Contains all Django ``Form`` and ``ModelForm`` classes used by the **core**
application.  Forms handle data validation and cleaning before values reach
the view or the database.

Planned Forms
-------------
The forms below should be implemented to support the views in
``core/views/``:

``SignupForm``
    Collects username, email, password, and password confirmation for new
    user registration.  Should extend ``UserCreationForm`` or validate
    password equality manually.

``LoginForm``
    Accepts username and password; thin wrapper around
    ``django.contrib.auth.forms.AuthenticationForm``.

``SetupForm``
    Gathers initial budget configuration: income amount, cycle start date,
    and preferred currency.

``AddExpenseForm``
    Validates a new transaction: amount (positive decimal), category, date,
    and optional description.

``EditTransactionForm``
    Same fields as ``AddExpenseForm``; used for the edit-transaction view.

``SettingsForm``
    Allows the user to update their profile preferences (e.g. currency,
    notification settings).

Example skeleton
----------------
.. code-block:: python

    from django import forms
    from .models import Transaction

    class AddExpenseForm(forms.ModelForm):
        class Meta:
            model  = Transaction
            fields = ['amount', 'category', 'date', 'description']
            widgets = {
                'date': forms.DateInput(attrs={'type': 'date'}),
            }

        def clean_amount(self):
            amount = self.cleaned_data['amount']
            if amount <= 0:
                raise forms.ValidationError("Amount must be greater than zero.")
            return amount

References
----------
Django forms documentation:
    https://docs.djangoproject.com/en/6.0/topics/forms/
Django ModelForm reference:
    https://docs.djangoproject.com/en/6.0/topics/forms/modelforms/
"""

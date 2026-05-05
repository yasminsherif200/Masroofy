from django.shortcuts import render, redirect
from core.services import TransactionService
from core.dao import BudgetDAO

transaction_service = TransactionService()
budget_dao = BudgetDAO()

def add_expense(request):
    # check that user exist
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    active_cycle = budget_dao.getActiveCycle(user_id)
    if not active_cycle:
        return redirect('setup')

    if request.method == 'POST':
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        date = request.POST.get('date')
        description = request.POST.get('description', '')

        # adding expense
        result = transaction_service.addExpense(
            budget_cycle=active_cycle,
            title=title,
            amount=amount,
            category=category,
            date=date,
            description=description,
        )

        if result['success']:
            # check threshold
            if result['threshold_alert']:
                return render(request, 'core/add_expense.html', {
                    'success': 'Expense added! Warning: you have used 80% of your budget.',
                    'cycle': active_cycle,
                })
            return redirect('dashboard')
        else:
            return render(request, 'core/add_expense.html', {
                'error': result['error'],
                'cycle': active_cycle,
            })

    return render(request, 'core/add_expense.html', {
        'cycle': active_cycle,
    })
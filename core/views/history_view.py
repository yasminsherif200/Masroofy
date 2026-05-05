from django.shortcuts import render, redirect
from core.dao import BudgetDAO, TransactionDAO

budget_dao = BudgetDAO()
transaction_dao = TransactionDAO()

def history(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    active_cycle = budget_dao.getActiveCycle(user_id)
    if not active_cycle:
        return redirect('setup')

    transactions = transaction_dao.getTransactionsByCycle(active_cycle)

    return render(request, 'core/history.html', {
        'transactions': transactions,
        'cycle': active_cycle,
    })
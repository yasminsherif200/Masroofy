from django.shortcuts import render, redirect
from core.dao import BudgetDAO, TransactionDAO
from core.services import BudgetService

budget_dao = BudgetDAO()
transaction_dao = TransactionDAO()
budget_service = BudgetService()

def reports(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    active_cycle = budget_dao.getActiveCycle(user_id)
    if not active_cycle:
        return redirect('setup')

    transactions = transaction_dao.getTransactionsByCycle(active_cycle)
    total_spent = transaction_dao.getTotalExpensesByCycle(active_cycle)
    category_percentages = budget_service.calculateCategoryPercentages(active_cycle.cycleID)
    balance = budget_service.getCurrentBalance(active_cycle.cycleID)

    return render(request, 'core/reports.html', {
        'transactions': transactions,
        'total_spent': round(total_spent, 2),
        'category_data': category_percentages,
        'balance': round(balance, 2),
        'cycle': active_cycle,
    })
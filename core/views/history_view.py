from django.shortcuts import render, redirect
from core.dao import BudgetDAO, TransactionDAO
from core.services import TransactionService

budget_dao = BudgetDAO()
transaction_dao = TransactionDAO()
transaction_service = TransactionService()

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


def delete_transaction(request, transaction_id):
    if not request.session.get('user_id'):
        return redirect('login')

    transaction = transaction_dao.getTransactionByID(transaction_id)
    if transaction and transaction_service.canRemoveExpense(transaction_id):
        transaction_dao.deleteTransaction(transaction_id)

    return redirect('history')

def edit_transaction(request, transaction_id):
    if not request.session.get('user_id'):
        return redirect('login')

    transaction = transaction_dao.getTransactionByID(transaction_id)
    if not transaction or not transaction_service.canEditExpense(transaction):
        return redirect('history')

    if request.method == 'POST':
        transaction.title = request.POST.get('title')
        transaction.amount = request.POST.get('amount')
        transaction.category = request.POST.get('category')
        transaction.description = request.POST.get('description', '')
        transaction_dao.updateTransaction(transaction)
        return redirect('history')

    return render(request, 'core/edit_transaction.html', {
        'transaction': transaction,
    })
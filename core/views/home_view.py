from django.shortcuts import render, redirect
from core.services import BudgetService
from core.dao import BudgetDAO

budget_service = BudgetService()
budget_dao = BudgetDAO()

def dashboard(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    active_cycle = budget_dao.getActiveCycle(user_id)
    if not active_cycle:
        return redirect('setup')
    

    daily_limit = budget_service.getSafeDailyLimit(active_cycle.cycleID)
    balance = budget_service.getCurrentBalance(active_cycle.cycleID)
    threshold_reached = budget_service.checkThreshold(active_cycle.cycleID)
    remaining_days = budget_service.getRemainingDays(active_cycle.cycleID)
    category_percentages = budget_service.calculateCategoryPercentages(active_cycle.cycleID)

    return render(request, 'core/dashboard.html', {
        'daily_limit': round(daily_limit, 2),
        'balance': round(balance, 2),
        'remaining_days': remaining_days,
        'threshold_reached': threshold_reached,
        'category_data': category_percentages,
        'cycle': active_cycle,
    })


def setup(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')

    if budget_dao.getActiveCycle(user_id):
        return redirect('dashboard')
    
    if request.method == 'POST':
        amount = request.POST.get('totalAllowance')
        end_date = request.POST.get('endDate')

        if not amount or not end_date:
            return render(request, 'core/setup.html', {
                'error': 'All fields are required.'
            })
        
        from datetime import date
        start = date.today()
        end = date.fromisoformat(end_date)

        budget_service.createNewCycle(user_id, float(amount), start, end)

        success = budget_service.createNewCycle(user_id, float(amount), start, end)

        if success:
            return redirect('dashboard')
        else:
            return render(request, 'core/setup.html', {
                'error': 'Invalid amount or dates.'
            })
        
    return render(request, 'core/setup.html')






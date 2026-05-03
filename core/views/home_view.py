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


def home_view(request):
    
    active_cycle = BudgetDAO.getActiveCycle(request.user.id)

    if request.method == 'POST':
        amount = request.POST.get('totalAllowance')
        
        #if user entered amount, create new budget cycle
        if amount:
            BudgetService.create_new_budget(
                user=request.user, 
                amount=float(amount)
            )
            return redirect('home')
        
    context = {
        'active_cycle': active_cycle,
        'user': request.user,
        'has_active_budget': active_cycle is not None
    }
    
    return render(request, 'core/home.html', context)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ..services.budget_service import BudgetService
from ..dao.budget_dao import BudgetDAO

@login_required # Ensure that only authenticated users can access the home view.
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
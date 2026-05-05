from core.views import login_view
from core.views import home_view
from core.views import settings_view
from core.views import add_expense_view
from core.views import history_view
from core.views import reports_view
from django.urls import path

urlpatterns = [
    path('', login_view.login, name='login'),
    path('signup/', login_view.signup, name='signup'),
    path('logout/', login_view.logout, name='logout'),
    path('setup/', home_view.setup, name='setup'), 
    path('dashboard/', home_view.dashboard, name='dashboard'),
    path('settings/', settings_view.settings , name='settings'),
    path('add-expense/', add_expense_view.add_expense, name='add_expense'),
    path('reset-cycle/', settings_view.reset_cycle, name='reset_cycle'),
    path('history/', history_view.history, name='history'),
    path('reports/', reports_view.reports, name='reports'),
]
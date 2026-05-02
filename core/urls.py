from core.views import login_view
from core.views import home_view
from django.urls import path

urlpatterns = [
    path('', login_view.login, name='login'),
    path('signup/', login_view.signup, name='signup'),
    path('logout/', login_view.logout, name='logout'),
    path('logout/', home_view.home_view, name='home'),
    path('setup/', login_view.setup_placeholder, name='setup'),
    path('dashboard/', login_view.dashboard_placeholder, name='dashboard'),
]
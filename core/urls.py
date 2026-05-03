from core.views import login_view
from core.views import home_view
from django.urls import path

urlpatterns = [
    path('', login_view.login, name='login'),
    path('signup/', login_view.signup, name='signup'),
    path('logout/', login_view.logout, name='logout'),
    path('setup/', home_view.setup, name='setup'),
    path('dashboard/', home_view.dashboard, name='dashboard'),
]
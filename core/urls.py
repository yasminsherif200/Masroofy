from core.views import login_view
from django.urls import path

urlpatterns = [
    path('', login_view.login, name='login'),
    path('signup/', login_view.signup, name='signup'),
    path('logout/', login_view.logout, name='logout'),
]
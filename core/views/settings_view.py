from django.shortcuts import render, redirect
from core.services import UserService
from core.dao import UserDAO

user_service = UserService()
user_dao = UserDAO()

def settings(request):
    if not request.session.get('user_id'):
        return redirect('login')

    user = user_dao.getUserSecurityData()

    if request.method == 'POST':
        userName = request.POST.get('userName')
        pin = request.POST.get('pin')
        confirmPin = request.POST.get('confirmPin')

        if not userName:
            return render(request, 'core/settings.html', {
                'error': 'Username is required.',
                'user': user,
            })

        if pin:
            if not pin.isdigit() or len(pin) != 4:
                return render(request, 'core/settings.html', {
                    'error': 'PIN must be exactly 4 digits.',
                    'user': user,
                })
            if pin != confirmPin:
                return render(request, 'core/settings.html', {
                    'error': 'PINs do not match.',
                    'user': user,
                })

            user_service.updateSecurity(userName, pin, True)
        else:
            user_service.updateUserName(userName)
        
        return render(request, 'core/settings.html', {
            'success': 'Settings saved successfully.',
            'user': user_dao.getUserSecurityData(),
        })

    return render(request, 'core/settings.html', {
        'user': user,
    })
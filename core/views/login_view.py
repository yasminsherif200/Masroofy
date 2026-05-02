from django.shortcuts import render, redirect
from core.services import UserService
from core.dao import UserDAO

user_service = UserService()
user_dao = UserDAO()

def login(request):
    # if user already logged in redirect to dashboard
    if request.session.get('user_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        pin = request.POST.get('pin')
        is_valid = user_service.verifyLogin(pin)

        if is_valid:
            user = user_dao.getUserSecurityData()
            request.session['user_id'] = user.userID
            return redirect('dashboard')
        else:
            if user_service.isLocked:
                return render(request, 'core/login.html', {
                    'error': 'Too many failed attempts. Try again later.'
                })
            else:
                return render(request, 'core/login.html', {
                    'error': 'Incorrect PIN. Please try again.'
                })
            
    # GET request
    return render(request, 'core/login.html')

def signup(request):
    # if user already logged in redirect to dashboard
    if request.session.get('user_id'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        # get data from form
        userName = request.POST.get('userName')
        pin = request.POST.get('pin')
        confirmPin = request.POST.get('confirmPin')

        # check if feilds empty
        if not userName or not pin or not confirmPin:
            return render(request, 'core/signup.html', {
                'error': 'All fields are required.'
            })
        
        # check if pin matches
        if pin != confirmPin:
            return render(request, 'core/signup.html', {
                'error': 'PINs do not match. Please try again.'
            })
        
        # save user to database
        user_service.updateSecurity(userName, pin, True)

        user = user_dao.getUserSecurityData()
        request.session['user_id'] = user.userID
        return redirect('setup')
    return render(request, 'core/signup.html')

def logout(request):
    request.session.flush()
    return redirect('login')
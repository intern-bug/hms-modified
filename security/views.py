from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

# Create your views here.
def security_check(user):
    return user.is_authenticated and user.is_security

@user_passes_test(security_check)
def home(request):
    user = request.user
    security = user.security
    return render(request, 'security/home.html',{'security':security})

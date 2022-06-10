from django.http import HttpResponse
from students.models import Outing
from .models import OutingInOutTimes 
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import user_passes_test

# Create your views here.
def security_check(user):
    return user.is_authenticated and user.is_security

@user_passes_test(security_check)
def home(request):
    user = request.user
    security = user.security

    return render(request, 'security/home.html',{'security':security})

@user_passes_test(security_check)
def scan(request):
    user = request.user
    security = user.security
    if request.method == 'POST':
        uid = request.POST['qrcode']
        outing = get_object_or_404(Outing, uuid=uid)

        return render(request, 'security/outing_detail.html', {'outing':outing})
    return render(request, 'security/scan3.html')

@user_passes_test(security_check)
def outing_action(request, pk):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'Permitted':
            outingInOutObj = OutingInOutTimes(outing = pk)
            outingInOutObj.save()
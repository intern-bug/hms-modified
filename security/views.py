from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from students.models import Outing
from .models import OutingInOutTimes 
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone



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
        outing_obj = get_object_or_404(Outing, uuid=uid)
        outingInOutTimes_obj = ''
        if OutingInOutTimes.objects.filter(outing=outing_obj.id).exists():
            outingInOutTimes_obj = OutingInOutTimes.objects.get(outing=outing_obj.id)
            if OutingInOutTimes.objects.get(outing=outing_obj.id).inTime != None:
                messages.error(request, 'Outing is already closed for that QR code')
                return HttpResponseRedirect(reverse('security:home'))
        return render(request, 'security/outing_detail.html', {'outing':outing_obj, 'outingInOutTimes':outingInOutTimes_obj})
    return render(request, 'security/scan3.html')

@user_passes_test(security_check)
def outing_action(request, pk):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'Allowed':
            outing_obj = get_object_or_404(Outing, id=pk)
            outingInOutObj = OutingInOutTimes(outing = outing_obj)
            outingInOutObj.save()
            messages.success(request, 'Outing Allowed successfully')
        elif action == 'Disallowed':
            messages.failure(request, 'Outing Rejected successfully')
        elif action == 'Outing Closed':
            outingInOutObj = get_object_or_404(OutingInOutTimes, outing=pk)
            print(timezone.now(), timezone.localtime())
            outingInOutObj.inTime = timezone.localtime()
            outingInOutObj.save()
            messages.success(request, 'Outing closed successfully')
        return HttpResponseRedirect(reverse('security:home'))
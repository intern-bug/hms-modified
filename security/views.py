from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from students.models import Outing
from .models import OutingInOutTimes 
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
import math



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
    if request.method == 'POST':
        uid = request.POST['qrcode']
        outing_obj = get_object_or_404(Outing, uuid=uid)
        if outing_obj.is_upcoming() and outing_obj.fromDate <= timezone.now():
            return redirect('security:outing_action', pk=outing_obj.id)
        elif not outing_obj.is_upcoming():
            messages.error(request, 'Outing is outdated.')
            return redirect('security:home')
        elif outing_obj.fromDate > timezone.now():
            msg = "Outing activates in " + str(math.ceil((outing_obj.fromDate-timezone.now()).total_seconds()/60)) + " minutes."
            messages.error(request, msg)
            return redirect('security:home')
    return render(request, 'security/scan3.html')

@user_passes_test(security_check)
def outing_action(request, pk):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'Allowed':
            outing_obj = get_object_or_404(Outing, id=pk)
            outingInOutObj = OutingInOutTimes(outing = outing_obj)
            outingInOutObj.save()
            outing_obj.status = 'In Outing'
            outing_obj.save()
            messages.success(request, 'Outing Allowed successfully')
        elif action == 'Disallowed':
            messages.success(request, 'Outing Rejected successfully')
        elif action == 'Outing Closed':
            outingInOutObj = get_object_or_404(OutingInOutTimes, outing=pk)
            outingInOutObj.inTime = timezone.now()
            outingInOutObj.save()
            outing_obj = get_object_or_404(Outing, id=pk)
            outing_obj.status = 'Closed'
            outing_obj.save()
            messages.success(request, 'Outing closed successfully')
        return redirect('security:home')
    else:
        outing_obj = get_object_or_404(Outing, id=pk)
        outingInOutTimes_obj = None
        if OutingInOutTimes.objects.filter(outing=pk).exists():
            outingInOutTimes_obj = OutingInOutTimes.objects.get(outing=pk)
            if OutingInOutTimes.objects.get(outing=pk).inTime != None:
                messages.error(request, 'Outing is already closed for that QR code')
                return redirect('security:home')
        return render(request, 'security/outing_detail.html', {'outing':outing_obj, 'outingInOutTimes':outingInOutTimes_obj})

@user_passes_test(security_check)
def get_outing_sheet(request):
    from .utils import OutingBookGenerator
    from django.utils import timezone
    from django.http import HttpResponse
    
    year_month_day = request.GET.get("year_month_day")
    block_id = request.GET.get("block_id")

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
    response['Content-Disposition'] = 'attachment; filename=Outing({date}).xlsx'.format(date=timezone.now().strftime('%d-%m-%Y'),)
    
    BookGenerator = OutingBookGenerator(block_id, year_month_day)
    workbook = BookGenerator.generate_workbook()
    workbook.save(response)

    return response
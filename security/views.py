from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from students.models import Outing
from .models import OutingInOutTimes 
from institute.models import Student
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
            if outingInOutObj.outing.is_upcoming():
                if request.POST['textarea']:
                    outingInOutObj.remark_by_security=request.POST['textarea']+" @ "+str(timezone.localtime().strftime('%d-%m-%Y -  %H:%M:%S'))
            else:
                messages.error(request, 'Outing is outdated.')
                return redirect('security:home')
            if outingInOutObj.outing.type != 'Vacation':
                outing_obj.status = 'In Outing'
            else:
                outing_obj.status = 'Closed'
                outingInOutObj.inTime = timezone.now()
            outing_obj.save()
            outingInOutObj.save()
            messages.success(request, 'Outing Allowed successfully')
        elif action == 'Disallowed':
            # outing_obj = get_object_or_404(Outing, id=pk)
            # outingInOutObj = OutingInOutTimes(outing = outing_obj)
            # outingInOutObj.remark_by_security+=request.POST['textarea']+" @ "+str(timezone.localtime().strftime('%d-%m-%Y -  %H:%M:%S'))
            # outingInOutObj.save()
            messages.success(request, 'Outing Rejected successfully')
        elif action == 'Outing Closed':
            outingInOutObj = get_object_or_404(OutingInOutTimes, outing=pk)
            student = get_object_or_404(Student, id=outingInOutObj.outing.student.id)
            outingInOutObj.inTime = timezone.now()
            if request.POST['textarea']:
                if outingInOutObj.remark_by_security!=None:
                    outingInOutObj.remark_by_security+=" "+request.POST['textarea']+" @ "+str(timezone.localtime().strftime('%d-%m-%Y -  %H:%M:%S'))
                else:
                    outingInOutObj.remark_by_security=request.POST['textarea']+" @ "+str(timezone.localtime().strftime('%d-%m-%Y -  %H:%M:%S'))
            outingInOutObj.save()
            outing_obj = get_object_or_404(Outing, id=pk)
            outing_obj.status = 'Closed'
            outing_obj.save()
            student.outing_rating = student.calculate_rating(outingInOutObj=outingInOutObj)
            student.save()
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
def outing_log(request):
    user = request.user
    # official = user.official
    student = None
    outing_list=None
    # if official.is_chief():
    #     outing_list = OutingInOutTimes.objects.all()
    # else:
    #     outing_list = OutingInOutTimes.objects.filter(outing__student__in = official.block.students())
    if request.method == 'GET':
        student_outing_list = None
        if request.GET.get('by_regd_no'):
            try:
                student = Student.objects.get(regd_no=request.GET.get('by_regd_no'))
            except Student.DoesNotExist:
                messages.error(request, "Invalid Student Registration No.")
            student_outing_list = OutingInOutTimes.objects.filter(outing__student=student)
            
        
        calendar_outing_list = None
        if request.GET.get('by_date'):
            outDate_outing_list = OutingInOutTimes.objects.filter(outTime__date=request.GET.get('by_date'))
            inDate_outing_list = OutingInOutTimes.objects.filter(inTime__date=request.GET.get('by_date'))
            calendar_outing_list = (outDate_outing_list|inDate_outing_list)
        elif request.GET.get('by_month'):
            year, month = request.GET.get('by_month').split('-')
            outDate_outing_list = OutingInOutTimes.objects.filter(outTime__year=year).filter(outTime__month=month)
            inDate_outing_list = OutingInOutTimes.objects.filter(inTime__year=year).filter(inTime__month=month)
            calendar_outing_list = (outDate_outing_list|inDate_outing_list)
        elif request.GET.get('by_year'):
            outDate_outing_list = OutingInOutTimes.objects.filter(outTime__year=request.GET.get('by_year'))
            inDate_outing_list = OutingInOutTimes.objects.filter(inTime__year=request.GET.get('by_year'))
            calendar_outing_list = (outDate_outing_list|inDate_outing_list)
        
        if request.GET.get('by_regd_no') and (request.GET.get('by_date') or request.GET.get('by_month') or request.GET.get('by_year')):
            outing_list = student_outing_list & calendar_outing_list
        elif request.GET.get('by_regd_no'):
            outing_list = student_outing_list
        elif (request.GET.get('by_date') or request.GET.get('by_month') or request.GET.get('by_year')):
            outing_list = calendar_outing_list

            
        if outing_list!=None and len(outing_list) == 0:
            messages.error(request, 'No Outing records found.')
            return redirect('security:outing-log')


    
    return render(request, 'security/outing_log.html', {'outing_list':outing_list, 'date':request.GET.get('by_date'), \
        'month':request.GET.get('by_month'), 'year':request.GET.get('by_year'), 'regno':request.GET.get('by_regd_no')})

@user_passes_test(security_check)
def get_outing_sheet(request):
    from .utils import OutingBookGenerator
    from django.utils import timezone
    from django.http import HttpResponse
    
    if request.GET.get('dwnld_by_date'):
        year_month_day = request.GET.get("dwnld_by_date")
    elif request.GET.get('dwnld_by_month'):
        year_month_day = request.GET.get("dwnld_by_month") + '-0'
    elif request.GET.get('dwnld_by_year'):
        year_month_day = request.GET.get('dwnld_by_year') + '-0-0'
    elif request.GET.get('dwnld_by_all'):
        year_month_day = 'all'
    block_id = request.GET.get("block_id")

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
    response['Content-Disposition'] = 'attachment; filename=Outing({date}).xlsx'.format(date=year_month_day+" "+str(timezone.now().strftime('%d-%m-%Y')),)
    
    BookGenerator = OutingBookGenerator(block_id, year_month_day)
    workbook = BookGenerator.generate_workbook()
    workbook.save(response)

    return response
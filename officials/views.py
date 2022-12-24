from calendar import weekday
from datetime import datetime, timedelta
from django.forms import CharField
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from acknowledgementform import create_acknowledge_form
from institute.models import Announcements, Block, Student, Official
from security.models import OutingInOutTimes
from students.models import Attendance, RoomDetail, Outing, ExtendOuting, Vacation, FeeDetail
from django.contrib import messages
from django.http.response import Http404, HttpResponseForbidden
from complaints.models import Complaint
from mess_feedback.models import MessFeedback
from workers.models import Worker, Attendance as AttendanceWorker
import uuid
from django.db.models import IntegerField, F, Q, Sum, Value, CharField
from django.db.models.functions import Cast, ExtractDay, TruncDate
from django.contrib.messages.views import SuccessMessageMixin
import io
from acknowledgementform import create_acknowledge_form
from django.http import Http404, FileResponse





def official_check(user):
    return user.is_authenticated and user.is_official
def chief_warden_check(user):
    return official_check(user) and (user.official.is_chief() or user.official.is_hostel_office())


def mess_incharge_check(user):
    if user.is_worker:
        worker = user.worker
        return worker.designation == 'Mess Incharge'
    return False
    
def mess_feedback_check(user):
    if(official_check(user) or mess_incharge_check(user)):
        return True
    return False
# Create your views here.
@user_passes_test(official_check)
def home(request):
    user = request.user
    official = user.official
    outing_requests = ''
    announce_obj = None
    if official.is_chief() or official.is_hostel_office():
        present_students = Attendance.objects.filter(status='Present')
        absent_students = Attendance.objects.filter(status='Absent')
        complaints = official.related_complaints(pending=False)
        complaints_pending = complaints.filter(status__in = ['Registered', 'Processing'])
        complaints_resolved = complaints.filter(status = 'Resolved')
        announce_obj = Announcements.objects.all()[:5]
     
    elif official.is_boys_deputy_chief():
        present_students = Attendance.objects.filter(status="Present", student__roomdetail__block__gender='Male')
        absent_students = Attendance.objects.filter(status="Absent", student__roomdetail__block__gender='Male')
        complaints = official.related_complaints(pending=False)
        complaints_pending = complaints.filter(status__in = ['Registered', 'Processing'])
        complaints_resolved = complaints.filter(status = 'Resolved')
        announce_obj = official.related_announcements()[:5]
    
    elif official.is_girls_deputy_chief():
        present_students = Attendance.objects.filter(status="Present", student__roomdetail__block__gender='Female')
        absent_students = Attendance.objects.filter(status="Absent", student__roomdetail__block__gender='Female')
        complaints = official.related_complaints(pending=False)
        complaints_pending = complaints.filter(status__in = ['Registered', 'Processing'])
        complaints_resolved = complaints.filter(status = 'Resolved')
        announce_obj = official.related_announcements()[:5]

    else:
        if not official.block: 
            raise Http404('You are currently not appointed any block! Please contact Admin')

        student_rooms = official.block.roomdetail_set.all()
        student_ids = student_rooms.values_list('student', flat=True)
        students = Student.objects.filter(pk__in=student_ids)
        present_students = Attendance.objects.filter(student__in=students, status='Present')
        absent_students = Attendance.objects.filter(student__in=students, status='Absent')
        complaints_pending = official.related_complaints(pending=False).filter(status__in = ['Registered', 'Processing'])
        complaints_resolved = official.related_complaints(pending=False).filter(status = 'Resolved')
        outing_requests = official.related_outings()
        announce_obj = official.related_announcements()

    return render(request, 'officials/home.html', {'user_details': official, 'present':present_students, \
        'absent':absent_students, 'complaints_pending':complaints_pending, 'complaints_resolved':complaints_resolved, 'outings':outing_requests, 'announce_obj':announce_obj})


@user_passes_test(official_check)
def profile(request):
    user = request.user
    official = user.official
    complaints = Complaint.objects.filter(user = user)
    return render(request, 'officials/profile.html', {'official': official, 'complaints': complaints})

def announcements_list(request):
    if request.user.is_official:
        announce_obj = request.user.official.related_announcements()
    elif request.user.is_student:
        announce_obj = request.user.student.related_announcements()
    return render(request, 'officials/announcements.html', {'announce_obj':announce_obj, 'user':request.user})

@user_passes_test(official_check)
@csrf_exempt
def attendance(request):
    user = request.user
    official = user.official
    block = official.block
    attendance_list  = Attendance.objects.filter(student__in=block.students())
    date_format = (timezone.localtime() - timedelta(hours=1)).date()

    date = date_format.strftime('%Y-%m-%d')

    for item in attendance_list:
        outingInOutTimes_obj = OutingInOutTimes.objects.filter(outing__student=item.student)[0]
        if outingInOutTimes_obj.outing.status == 'In Outing':
            item.outing_status = 'In Outing'
        else:
            item.outing_status = 'In College'
        if item.present_dates:
            present_dates = set(item.present_dates.split(','))
            present_dates = [row.split('@')[0] for row in present_dates]
            if date in present_dates: item.present_on_date = True
        if item.absent_dates:
            absent_dates = set(item.absent_dates.split(','))
            absent_dates = [row.split('@')[0] for row in absent_dates]
            if date in absent_dates: item.absent_on_date = True
    if request.method == 'POST' and request.POST.get('submit'):
        for attendance in attendance_list:
            if request.POST.get(str(attendance.id)) and request.POST.get(str(attendance.id))!='not_marked': attendance.mark_attendance(date, request.POST.get(str(attendance.id)))
        attendance_list  = Attendance.objects.filter(student__in=block.students())
        for item in attendance_list:
            outingInOutTimes_obj = OutingInOutTimes.objects.filter(outing__student=item.student)[0]
            if outingInOutTimes_obj.outing.status == 'In Outing':
                item.outing_status = 'In Outing'
            else:
                item.outing_status = 'In College'
            if item.present_dates:
                present_dates = set(item.present_dates.split(','))
                present_dates = [row.split('@')[0] for row in present_dates]
                if date in present_dates: item.present_on_date = True
            if item.absent_dates:
                absent_dates = set(item.absent_dates.split(','))
                absent_dates = [row.split('@')[0] for row in absent_dates]
                if date in absent_dates: item.absent_on_date = True

        messages.success(request, f'Attendance marked for date: {date}')


    return render(request, 'officials/attendance.html', {'official': official, 'attendance_list': attendance_list, 'date': date_format})


@user_passes_test(official_check)
@csrf_exempt
def attendance_workers(request):
    user = request.user
    official = user.official
    block = official.block
    attendance_list  = AttendanceWorker.objects.filter(worker__in=block.worker_set.all())
    date_format = (timezone.localtime() - timedelta(hours=1)).date()

    date = date_format.strftime('%Y-%m-%d')

    for item in attendance_list:
        if item.present_dates:
            present_dates = set(item.present_dates.split(','))
            present_dates = [row.split('@')[0] for row in present_dates]
            if date in present_dates: item.present_on_date = True
        if item.absent_dates:
            absent_dates = set(item.absent_dates.split(','))
            absent_dates = [row.split('@')[0] for row in absent_dates]
            if date in absent_dates: item.absent_on_date = True

    if request.method == 'POST' and request.POST.get('submit'):
        for attendance in attendance_list:
            if request.POST.get(str(attendance.id)) and request.POST.get(str(attendance.id))!='not_marked': attendance.mark_attendance(date, request.POST.get(str(attendance.id)))
        attendance_list  = AttendanceWorker.objects.filter(worker__in=block.worker_set.all())
        for item in attendance_list:
            if item.present_dates:
                present_dates = set(item.present_dates.split(','))
                present_dates = [row.split('@')[0] for row in present_dates]
                if date in present_dates: item.present_on_date = True
            if item.absent_dates:
                absent_dates = set(item.absent_dates.split(','))
                absent_dates = [row.split('@')[0] for row in absent_dates]
                if date in absent_dates: item.absent_on_date = True
        messages.success(request, f'Staff Attendance marked for date: {date}')

    return render(request, 'officials/attendance_workers.html', {'official': official, 'attendance_list': attendance_list, \
        'date': date})


@user_passes_test(official_check)
def attendance_log(request):
    user = request.user
    official = user.official
    student = None
    present_attendance = None
    absent_attendance = None
    present_dates = None
    absent_dates = None

    if official.is_chief() or official.is_hostel_office():
        attendance_list = Attendance.objects.all()
    elif official.is_boys_deputy_chief():
        attendance_list = Attendance.objects.filter(student__roomdetail__block__gender='Male')
    elif official.is_girls_deputy_chief():
        attendance_list = Attendance.objects.filter(student__roomdetail__block__gender='Female')
    else:
        attendance_list = Attendance.objects.filter(student__in = official.block.students())

    if request.GET.get('by_regd_no'):
        try:
            student = attendance_list.get(student__regd_no = request.GET.get('by_regd_no')).student
            if student.attendance.present_dates: 
                present_dates = student.attendance.present_dates.split(',')
                present_dates = [present_date.split('@')[0] for present_date in present_dates]
            if student.attendance.absent_dates: 
                absent_dates = student.attendance.absent_dates.split(',')
                absent_dates = [absent_date.split('@')[0] for absent_date in absent_dates]
        except Attendance.DoesNotExist:
            messages.error(request, "Invalid Student Registration No.")

    if request.GET.get('by_date'):
        present_attendance = attendance_list.filter(present_dates__contains = request.GET.get('by_date'))
        absent_attendance = attendance_list.filter(absent_dates__contains = request.GET.get('by_date'))

        if present_attendance.count() == 0 and absent_attendance.count() == 0:
            messages.error(request, "No Attendance Records Found!")

    return render(request, 'officials/attendance_log.html', {'official':official, 'student': student, 'date': request.GET.get('by_date'),\
        'present_attendance': present_attendance, 'absent_attendance': absent_attendance, \
            'present_dates': present_dates, 'absent_dates': absent_dates})


@user_passes_test(official_check)
def generate_attendance_sheet(request):
    from .utils import AttendanceBookGenerator
    from django.utils import timezone
    from django.http import HttpResponse
    
    year_month = request.GET.get("year_month")
    block_id = request.GET.get("block_id")

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
    response['Content-Disposition'] = 'attachment; filename=Attendance({date}).xlsx'.format(date=timezone.now().strftime('%d-%m-%Y'),)
    
    BookGenerator = AttendanceBookGenerator(block_id, year_month)
    workbook = BookGenerator.generate_workbook()
    workbook.save(response)

    return response

@user_passes_test(official_check)
def grant_outing(request):
    user = request.user
    official = user.official
    outings = official.related_outings()
    return render(request, 'officials/grant_outing.html', {'official': official, 'outings': outings})

from django.core.mail import send_mail
from django.conf import settings
def send_outing_mail(outing):
    student=outing.student
    warden=Official.objects.filter(block=student.roomdetail.block.id, designation='Warden')[0]
    email = warden.user.email
    send_mail(
    subject='Outing Request Raised',
    message='Outing request is raised by Student',
    from_email=settings.EMAIL_HOST_USER,
    recipient_list=[email],
    fail_silently=False,
    html_message="Outing request is raised by : "+str(student.name)+" "+(student.roll_no)
    )
@user_passes_test(official_check)
def outing_detail(request, pk):
    outing = get_object_or_404(Outing, id=pk)
    user = request.user
    official = user.official
    type1 = outing.type
    outingExtendObj = None
    if outing.permission=='Pending Extension' or outing.permission=='Processing Extension':
        outingExtendObj = ExtendOuting.objects.filter(outing=outing).order_by('-id')
        outingExtendObj = outingExtendObj[0]
    # mess_rebate = 0
    # if ((outing.toDate-outing.fromDate).days) >= 5 or (outingExtendObj and (((outingExtendObj.toDate-outingExtendObj.fromDate).days) >= 5)):
    #     mess_rebate = 1
    if(request.method=='POST'):
        user = request.user
        if(user.official.is_warden()):
            if (request.POST.get('textarea')):
                if(request.POST.get('textarea').lstrip()!=outing.remark_by_warden):
                    if outing.permission == 'Processing':
                        outing.remark_by_warden =request.POST.get('textarea')+" @ "+str(timezone.localtime().strftime('%d-%m-%Y -  %H:%M:%S'))
                    elif outing.permission =='Processing Extension':
                        outing.remark_by_warden = request.POST.get('textarea')+" @ "+str(timezone.localtime().strftime('%d-%m-%Y -  %H:%M:%S'))

            if request.POST.get('permission'):
                if request.POST.get('permission') == 'Granted':
                    if outing.type not in ['Local','Vacation'] and request.POST.get('permission') == 'Granted':
                        if outing.permission == 'Processing':
                            outing.permission = 'Granted'
                        elif outing.permission == 'Processing Extension':
                            outing.permission = 'Extension Granted'
                            prev_fromDate = outing.fromDate
                            prev_toDate = outing.toDate
                            prev_place_of_visit = outing.place_of_visit
                            prev_purpose = outing.purpose
                            prev_mode_of_journey_from = outing.mode_of_journey_from
                            prev_mode_of_journey_to = outing.mode_of_journey_to
                            prev_emergency_contact = outing.emergency_contact
                            prev_emergency_missue = outing.emergency_medical_issue
                            outing.fromDate = outingExtendObj.fromDate
                            outing.toDate = outingExtendObj.toDate
                            outing.place_of_visit = outingExtendObj.place_of_visit
                            outing.purpose = outingExtendObj.purpose
                            outingExtendObj.fromDate = prev_fromDate
                            outingExtendObj.toDate = prev_toDate
                            outingExtendObj.place_of_visit = prev_place_of_visit
                            outingExtendObj.purpose = prev_purpose
                            outingExtendObj.mode_of_journey_from = prev_mode_of_journey_from
                            outingExtendObj.mode_of_journey_to = prev_mode_of_journey_to
                            outingExtendObj.emergency_contact = prev_emergency_contact
                            outingExtendObj.emergency_medical_issue = prev_emergency_missue
                            outingExtendObj.permission = 'Extension Granted'
                            outingExtendObj.save()
                    if outing.type == 'Vacation':
                        outing.permission = 'Granted'
                        outing_list = Outing.objects.filter(toDate__gte=outing.fromDate, student=outing.student).exclude(status='In Outing')
                        for out in outing_list:
                            out.permission='Revoked'
                            out.save()
                    if outing.status != 'In Outing':
                        uid = uuid.uuid4()
                        outing.uuid = uid
                elif request.POST.get('permission') == 'Rejected':
                    if outing.type != 'Local' and request.POST.get('permission') == 'Rejected':
                        if outing.permission == 'Processing':
                            outing.permission = 'Rejected'
                        elif outing.permission == 'Processing Extension':
                            outingExtendObj.permission = 'Extension Rejected'
                            outingExtendObj.save()
                            outing.permission = 'Extension Rejected'
            
            if request.POST.get('mess_rebate'):
                outing.mess_rebate = request.POST.get('mess_rebate')
        elif(user.official.is_caretaker()):
            if(request.POST.get('textarea')):
                if(request.POST.get('textarea')!=outing.remark_by_caretaker):
                    if outing.permission == 'Pending':
                        outing.remark_by_caretaker = request.POST.get('textarea')+" @ "+str(timezone.localtime().strftime('%d-%m-%Y -  %H:%M:%S'))
                    elif outing.permission == 'Pending Extension':
                        outing.remark_by_caretaker =request.POST.get('textarea')+" @ "+str(timezone.localtime().strftime('%d-%m-%Y -  %H:%M:%S'))
                        # outingExtendObj.remark_by_caretaker = request.POST.get('textarea')
                        # outingExtendObj.save()
            if(request.POST.get('parent_consent')):
                if outing.permission == 'Pending':
                    outing.parent_consent = request.POST.get('parent_consent')
                elif outing.permission == 'Pending Extension':
                    outingExtendObj.parent_consent = request.POST.get('parent_consent')
                    outingExtendObj.save()
            if request.POST.get('permission'):
                if outing.type != 'Local' and request.POST.get('permission') == 'Granted':
                    if outing.permission == 'Pending':
                        outing.permission = 'Processing'
                    elif outing.permission == 'Pending Extension':
                        outingExtendObj.permission = 'Processing Extension'
                        outingExtendObj.save()
                        outing.permission = 'Processing Extension'
                        # send mail to warden here
                    send_outing_mail(outing)
                elif outing.type != 'Local' and request.POST.get('permission') == 'Rejected':
                    if outing.permission == 'Pending':
                        outing.permission = 'Rejected'
                    elif outing.permission == 'Pending Extension':
                        outingExtendObj.permission = 'Extension Rejected'
                        outingExtendObj.save()
                        outing.permission = 'Extension Rejected'
                if outing.type == 'Local' and request.POST.get('permission') == 'Granted':
                    outing.permission = 'Granted'
                    uid = uuid.uuid4()
                    outing.uuid = uid
                elif outing.type == 'Local' and request.POST.get('permission') == 'Rejected':
                    outing.permission = 'Rejected'
        outing.save()
        messages.success(request, f'Outing successfully {outing.permission.lower()} to {outing.student.name}')
        return redirect('officials:grant_outing')
    return render(request, 'officials/outing_show.html', {'type':type1, 'official':official.designation, \
        'outing': outing, 'extendOuting':outingExtendObj})


@user_passes_test(chief_warden_check)
@csrf_exempt
def blockSearch(request):
    user = request.user
    official = user.official
    blocks = Block.objects.all()

    if request.POST:
        block_id = request.GET.get('block')
        if request.POST.get('Add'):
            block = Block.objects.get(id = request.POST.get('block_id'))
            from json import dumps
            current_floor = request.POST.get('floor')
            current_floor_json = dumps(current_floor)
            try:
                student = Student.objects.get(regd_no = request.POST.get('regd_no'))
                if not student.is_hosteller:
                    raise ValidationError("Cannot assign room to day scholars.")
                room_detail = student.roomdetail
                if room_detail.block and room_detail.room():
                    messages.error(request, f'Student {student.regd_no} already alloted room in {room_detail.block.name} {room_detail.room()}!')
                else:
                    room_detail.block = block
                    room_detail.floor = request.POST.get('floor')
                    room_detail.room_no = request.POST.get('room_no')
                    room_detail.bed = request.POST.get('bed') 
                    room_detail.full_clean()
                    room_detail.save()
                    # fee_detail = FeeDetail.objects.filter(student=student, room_detail=room_detail)
                    fee_detail = FeeDetail.objects.filter(student=student, room_detail=room_detail).first()
                    fee_detail.mode_of_payment = request.POST.get('payment_mode')
                    fee_detail.amount_paid = request.POST.get('amount_paid')
                    fee_detail.dop = request.POST.get('date_of_payment')
                    fee_detail.save()
                    messages.success(request, f'Student {student.regd_no} successfully alloted room in {room_detail.block.name} {room_detail.room()}!')
            except RoomDetail.DoesNotExist as error:
                # Day Scholars have no room detail.
                messages.error(request, "Cannot assign room to day scholars.")
            except ValidationError as error:
                for message in error.messages:
                    messages.error(request, message)
            except Student.DoesNotExist:
                messages.error(request, f'Student not found!')
            from django.core.serializers import serialize
            block = Block.objects.get(id = request.POST.get('block_id'))
            block_json = serialize('json', [block])
            room_number_json = dumps(room_detail.room())
            return render(request, 'officials/block_layout.html',{'blocks':blocks, 'current_block': block, 'current_block_json': block_json, 'current_floor_json':current_floor_json, 'room_number_json':room_number_json})

        if request.POST.get('remove'):
            room_detail = RoomDetail.objects.get(id = request.POST.get('roomdetail_id'))
            room_detail.block = None
            room_detail.floor = None
            room_detail.room_no = None
            room_detail.save()
            fee_detail = FeeDetail.objects.filter(student=room_detail.student, room_detail=room_detail).first()
            fee_detail.amount_paid = 0
            fee_detail.mode_of_payment = None
            fee_detail.dop = None
            fee_detail.save()
            messages.success(request, f'Student {room_detail.student.regd_no} removed from room.')
        
        if request.POST.get('download'):
            room_detail = RoomDetail.objects.get(id = request.POST.get('roomdetail_id'))
            fee_detail = FeeDetail.objects.get(student=room_detail.student, room_detail=room_detail)
            buf = io.BytesIO()
            context = {'room':room_detail, 'fee':fee_detail}
            create_acknowledge_form(buf, context)
            buf.seek(0)
            file = 'Acknowledgement_form-{}/{}.{}'.format(room_detail.__str__(), room_detail.student.regd_no,'pdf')
            return FileResponse(buf, as_attachment=True, filename=file)

        return redirect(reverse_lazy('officials:blockSearch') + '?block={}'.format(block_id))


    if request.GET.get('block'):
        from django.core.serializers import serialize
        block = Block.objects.get(id=request.GET.get('block'))
        block_json = serialize('json', [block])
        return render(request, 'officials/block_layout.html',{'blocks':blocks, 'current_block': block, 'current_block_json': block_json})

    return render(request, 'officials/block_layout.html',{'blocks':blocks})

@user_passes_test(official_check)
def outing_log(request):
    user = request.user
    official = user.official
    student = None
    outing_list=None
    if official.is_chief() or official.is_hostel_office():
        valid_outing_list = OutingInOutTimes.objects.all()
    elif official.is_boys_deputy_chief():
        valid_outing_list = OutingInOutTimes.objects.filter(outing__student__roomdetail__block__gender = 'Male')
    elif official.is_girls_deputy_chief():
        valid_outing_list = OutingInOutTimes.objects.filter(outing__student__roomdetail__block__gender = 'Female')
    else:
        valid_outing_list = OutingInOutTimes.objects.filter(outing__student__in = official.block.students())
    if request.method == 'GET':
        student_outing_list = None
        if request.GET.get('by_regd_no'):
            try:
                if not official.is_chief():
                    student = official.block.students()
                else:
                    student = Student.objects.all()
                student = student.get(regd_no=request.GET.get('by_regd_no'))
                student_outing_list = valid_outing_list.filter(outing__student=student)
            except Student.DoesNotExist:
                messages.error(request, "Invalid Student Registration No.")
                return redirect('officials:outing-log')
            
        
        calendar_outing_list = None
        if request.GET.get('by_date'):
            outDate_outing_list = valid_outing_list.filter(outTime__date=request.GET.get('by_date'))
            inDate_outing_list = valid_outing_list.filter(inTime__date=request.GET.get('by_date'))
            calendar_outing_list = (outDate_outing_list|inDate_outing_list)
        elif request.GET.get('by_month'):
            year, month = request.GET.get('by_month').split('-')
            outDate_outing_list = valid_outing_list.filter(outTime__year=year).filter(outTime__month=month)
            inDate_outing_list = valid_outing_list.filter(inTime__year=year).filter(inTime__month=month)
            calendar_outing_list = (outDate_outing_list|inDate_outing_list)
        elif request.GET.get('by_year'):
            outDate_outing_list = valid_outing_list.filter(outTime__year=request.GET.get('by_year'))
            inDate_outing_list = valid_outing_list.filter(inTime__year=request.GET.get('by_year'))
            calendar_outing_list = (outDate_outing_list|inDate_outing_list)
        
        if request.GET.get('by_regd_no') and (request.GET.get('by_date') or request.GET.get('by_month') or request.GET.get('by_year')):
            outing_list = student_outing_list & calendar_outing_list
        elif request.GET.get('by_regd_no'):
            outing_list = student_outing_list
        elif (request.GET.get('by_date') or request.GET.get('by_month') or request.GET.get('by_year')):
            outing_list = calendar_outing_list

            
        if outing_list!=None and len(outing_list) == 0:
            messages.error(request, 'No Outing records found.')
            return redirect('officials:outing-log')


    
    return render(request, 'officials/outing_log.html', {'outing_list':outing_list, 'date':request.GET.get('by_date'), \
        'month':request.GET.get('by_month'), 'year':request.GET.get('by_year'), 'regno':request.GET.get('by_regd_no')})

@user_passes_test(official_check)
def get_outing_sheet(request):
    from .utils import OutingBookGenerator
    from django.utils import timezone
    from django.http import HttpResponse
    user = request.user
    official = user.official
    if request.GET.get('dwnld_by_date'):
        year_month_day = request.GET.get("dwnld_by_date")
    elif request.GET.get('dwnld_by_month'):
        year_month_day = request.GET.get("dwnld_by_month") + '-0'
    elif request.GET.get('dwnld_by_year'):
        year_month_day = request.GET.get('dwnld_by_year') + '-0-0'
    elif request.GET.get('dwnld_by_all'):
        year_month_day = 'all'
    if official.is_chief() or official.is_hostel_office():
        block_id = 'all'
    elif official.is_boys_deputy_chief():
        block_id = 'boys'
    elif official.is_girls_deputy_chief():
        block_id = 'girls'
    else:
        block_id = official.block.id

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
    response['Content-Disposition'] = 'attachment; filename=Outing({date}).xlsx'.format(date=year_month_day+" "+str(timezone.now().strftime('%d-%m-%Y')),)
    
    BookGenerator = OutingBookGenerator(block_id, year_month_day)
    workbook = BookGenerator.generate_workbook()
    workbook.save(response)

    return response

@user_passes_test(mess_feedback_check)
def mess_feedback_analysis(request):
    calendar_feedback = None
    type_feedback = None
    weekday_feedback = None
    if request.method == 'POST':
        # if request.POST.get('by_date'):
        #     calendar_feedback = MessFeedback.objects.filter(date=request.POST.get('by_date'))
        # elif request.POST.get('by_month'):
        #     year, month = request.POST.get('by_month').split('-')
        #     calendar_feedback = MessFeedback.objects.filter(date__year=year, date__month=month)
        if request.POST.get('by_range_from_date') and request.POST.get('by_range_to_date'):
            calendar_feedback = MessFeedback.objects.filter(date__range=[request.POST.get('by_range_from_date'), request.POST.get('by_range_to_date')])
            if request.POST.get('by_day'):
                weekday_feedback = MessFeedback.objects.filter(date__week_day=request.POST.get('by_day'))
            if calendar_feedback and weekday_feedback:
                calendar_feedback = calendar_feedback & weekday_feedback
        elif request.POST.get('by_year'):
            calendar_feedback = MessFeedback.objects.filter(date__year=request.POST.get('by_year'))
            if request.POST.get('by_day'):
                weekday_feedback = MessFeedback.objects.filter(date__week_day=request.POST.get('by_day'))
            if calendar_feedback and weekday_feedback:
                calendar_feedback = calendar_feedback & weekday_feedback

        elif request.POST.get('by_day'):
            calendar_feedback = MessFeedback.objects.filter(date__week_day=request.POST.get('by_day'))
        if calendar_feedback!=None and len(calendar_feedback)==0:
            messages.error(request, 'No feedback found.')
            return render(request, 'officials/mess_feedback_analysis.html')
        
        if request.POST.get('by_type'):
            if request.POST.get('by_type') != 'all':
                type_feedback = MessFeedback.objects.filter(type=request.POST.get('by_type'))
            else:
                type_feedback = MessFeedback.objects.all()
            if len(type_feedback)==0:
                messages.error(request, 'No feedback found.')
                return render(request, 'officials/mess_feedback_analysis.html')
        
        if not calendar_feedback and not type_feedback:
            messages.error(request, 'No feedback found.')
            return render(request, 'officials/mess_feedback_analysis.html')
        elif calendar_feedback and type_feedback:
            feedback_obj = calendar_feedback & type_feedback
        elif calendar_feedback:
            feedback_obj = calendar_feedback
        elif type_feedback:
            feedback_obj = type_feedback
        ratings_sum = feedback_obj.aggregate(Sum('rating'))['rating__sum']
        rating = (ratings_sum/len(feedback_obj))
        percent_5 = round(((feedback_obj.filter(rating=5).count())/len(feedback_obj))*100)
        percent_4 = round(((feedback_obj.filter(rating=4).count())/len(feedback_obj))*100)
        percent_3 = round(((feedback_obj.filter(rating=3).count())/len(feedback_obj))*100)
        percent_2 = round(((feedback_obj.filter(rating=2).count())/len(feedback_obj))*100)
        percent_1 = round(((feedback_obj.filter(rating=1).count())/len(feedback_obj))*100)
        context = {'rating':rating, 
                   'percent_5':percent_5, 
                   'percent_4':percent_4,
                   'percent_3':percent_3, 
                   'percent_2':percent_2, 
                   'percent_1':percent_1,
                   'from_date': request.POST.get('by_range_from_date'),
                   'to_date': request.POST.get('by_range_to_date'),
                   'day': request.POST.get('by_day'),
                   'year': request.POST.get('by_year'),
                   'type': request.POST.get('by_type'),
                   'count': len(feedback_obj)
        }
        return render(request, 'officials/mess_feedback_analysis.html', context=context)

    return render(request, 'officials/mess_feedback_analysis.html')


@user_passes_test(official_check)
def mess_rebate_action(request):
    # outing_obj = Outing.objects.filter(mess_rebate='Enabled', mess_rebate_status='NA')
    outingInOut_obj = None
    calendar_outings = None
    regd_no_outings = None
    if request.method == 'GET':
        if request.GET.get('by_month'):
            year, month = request.GET.get('by_month').split('-')
            calendar_outings = OutingInOutTimes.objects.filter(inTime__year=year, inTime__month=month, \
                outing__mess_rebate='Enabled', outing__mess_rebate_status='NA').alias(days=Cast(ExtractDay(TruncDate(F('inTime')) - TruncDate(F('outTime'))), \
                    IntegerField())).annotate(days=F('days')).alias(applied_days=Cast(ExtractDay(TruncDate(F('inTime')) - TruncDate(F('outTime'))), \
                    IntegerField())).annotate(applied_days=F('applied_days'))
        
        if request.GET.get('by_regd_no'):
            regd_no_outings = OutingInOutTimes.objects.filter(outing__student__regd_no=request.GET.get('by_regd_no'),
                outing__mess_rebate='Enabled', outing__mess_rebate_status='NA').alias(days=Cast(ExtractDay(TruncDate(F('inTime')) - TruncDate(F('outTime'))), \
                    IntegerField())).annotate(days=F('days')).alias(applied_days=Cast(ExtractDay(TruncDate(F('inTime')) - TruncDate(F('outTime'))), \
                    IntegerField())).annotate(applied_days=F('applied_days'))
        
        if not calendar_outings and not regd_no_outings and (request.GET.get('by_month') or request.GET.get('by_regd_no')):
            messages.error(request, 'No records found.')
            return render(request, 'officials/mess_rebate_action.html')
        elif calendar_outings and regd_no_outings:
            outingInOut_obj = calendar_outings & regd_no_outings
        elif calendar_outings:
            outingInOut_obj = calendar_outings
        elif regd_no_outings:
            outingInOut_obj = regd_no_outings
        if request.GET.get('submit_action'):
            for outing in outingInOut_obj:
                if ('status_'+str(outing.id)) in request.GET.keys():
                    outing_obj = get_object_or_404(Outing,id=outing.outing.id)
                    outing_obj.mess_rebate_status = request.GET.get('status_'+str(outing.id))
                    outing_obj.mess_rebate_days = request.GET.get('no_of_days_'+str(outing.id))
                    if ('remark'+str(outing.id)):
                        outing_obj.mess_rebate_remarks = request.GET.get('remark'+str(outing.id))
                    outing_obj.save()
            messages.success(request, 'Mess Rebate status updated successfully.')
            return render(request, 'officials/mess_rebate_action.html')
            
        return render(request, 'officials/mess_rebate_action.html', {'outing_obj':outingInOut_obj, 'regd_no': request.GET.get('by_regd_no') or '',\
            'month': request.GET.get('by_month')})

    return render(request, 'officials/mess_rebate_action.html')


@user_passes_test(official_check)
def mess_rebate_detail_log(request):
    calendar_rebate_list=None
    regd_no_rebate_list = None
    rebate_list = None
    if request.method == 'GET':
        if 'submit' in request.GET.keys() or 'download' in request.GET.keys():
            total_days = (datetime.strptime(request.GET.get('by_range_to_date'), '%Y-%m-%d')-datetime.strptime(request.GET.get('by_range_from_date'),'%Y-%m-%d')).days
            if request.GET.get('by_mode') == 'Rebate':
                if request.GET.get('by_range_from_date') and request.GET.get('by_range_to_date'):
                    calendar_rebate_list = OutingInOutTimes.objects.filter(~Q(outing__mess_rebate_status='NA'), inTime__date__range=[request.GET.get('by_range_from_date'), request.GET.get('by_range_to_date')])
                
                if request.GET.get('by_regd_no'):
                    regd_no_rebate_list = OutingInOutTimes.objects.filter(~Q(outing__mess_rebate_status='NA'), outing__student__regd_no=request.GET.get('by_regd_no'))
                if not calendar_rebate_list and not regd_no_rebate_list:
                    messages.error(request, 'No record foundd.')
                    return render(request, 'officials/mess_rebate_log.html')
                elif calendar_rebate_list and regd_no_rebate_list:
                    rebate_list = calendar_rebate_list & regd_no_rebate_list
                elif  request.GET.get('by_regd_no') and request.GET.get('by_range_from_date') and request.GET.get('by_range_to_date'):
                    messages.error(request, 'No Records found.')
                    return render(request, 'officials/mess_rebate_log.html')
                elif calendar_rebate_list:
                    rebate_list = calendar_rebate_list
                elif regd_no_rebate_list:
                    rebate_list = regd_no_rebate_list
                rebate_list = rebate_list.values('outing__student__regd_no', 'outing__student__name').annotate(no_of_days=Sum('outing__mess_rebate_days'), \
                    effective_days=total_days-F('no_of_days'), from_date=Value(request.GET.get('by_range_from_date'), output_field=CharField()), to_date=Value(request.GET.get('by_range_to_date'), output_field=CharField()),\
                        total_days=Value(total_days, output_field=IntegerField()))
            elif request.GET.get('by_mode') == 'all':
                if request.GET.get('by_range_from_date') and request.GET.get('by_range_to_date'):
                    rebate_list = []
                    students = Student.objects.all()
                    if request.GET.get('by_regd_no'):
                        students = students.filter(regd_no=request.GET.get('by_regd_no'))
                    for student in students:
                        rebate={}
                        rebate['outing__student__regd_no']=student.regd_no
                        rebate['outing__student__name'] = student.name
                        rebate['from_date'] = request.GET.get('by_range_from_date')
                        rebate['to_date'] = request.GET.get('by_range_to_date')
                        rebate_days = 0
                        for outing in student.outing_set.all():
                            if outing.outinginouttimes_set.filter(inTime__date__range=[request.GET.get('by_range_from_date'), request.GET.get('by_range_to_date')]):
                                rebate_days+=outing.mess_rebate_days
                        rebate['no_of_days']=rebate_days
                        rebate['effective_days']=total_days-rebate_days
                        rebate['total_days'] = total_days
                        rebate_list.append(rebate)

            if request.GET.get('submit'):
                context = {
                    'from_date': request.GET.get('by_range_from_date'),
                    'to_date': request.GET.get('by_range_to_date'),
                    'rebate_list': rebate_list,
                    'regd_no': request.GET.get('by_regd_no'),
                    'mode': request.GET.get('by_mode'),
                }
                return render(request, 'officials/mess_rebate_log.html', context=context)
            elif request.GET.get('download'):
                from django.http import HttpResponse
                from .utils import MessReportBookGenerator

                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
                filename = str(timezone.localtime().strftime("%d-%m-%Y_%H:%M:%S"))
                response['Content-Disposition'] = 'attachment; filename=MessReportLog({date}).xlsx'.format(date=filename)
                BookGenerator = MessReportBookGenerator(rebate_list=rebate_list)
                workbook = BookGenerator.generate_workbook()
                workbook.save(response)
                return response
    return render(request, 'officials/mess_rebate_log.html')      

@user_passes_test(official_check)
def vacation_mess_report(request):
    students = Student.objects.all()
    rebate_list=[]
    for student in students:
        rebate={}
        rebate['outing__student__regd_no']=student.regd_no
        rebate['outing__student__name'] = student.name
        rebate['from_date'] = student.roomdetail.allotted_on
        vacation = Vacation.objects.filter(room_detail__student=student)
        if vacation and vacation[0].vacation_outing_obj:
            outingInOut_obj = OutingInOutTimes.objects.filter(outing=vacation[0].vacation_outing_obj)
            if outingInOut_obj:
                rebate['to_date'] = outingInOut_obj.outTime.date()
                rebate['total_days'] = (rebate['to_date']-rebate['from_date']).days
            else:
                rebate['to_date'] = 'Not vacated'
                rebate['total_days'] = (timezone.localdate()-rebate['from_date']).days
        else:
            rebate['to_date'] = 'Not vacated'
            rebate['total_days'] = (timezone.localdate()-rebate['from_date']).days

        rebate_days = 0
        for outing in student.outing_set.all():
            if outing.outinginouttimes_set.all():
                rebate_days+=outing.mess_rebate_days
        rebate['no_of_days']=rebate_days
        rebate['effective_days']=rebate['total_days']-rebate_days
        rebate_list.append(rebate)
        context = {'rebate_list':rebate_list}

        from django.http import HttpResponse
        from .utils import MessReportBookGenerator

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
        filename = str(timezone.localtime().strftime("%d-%m-%Y_%H:%M:%S"))
        response['Content-Disposition'] = 'attachment; filename=VacationMessReportLog({date}).xlsx'.format(date=filename)
        BookGenerator = MessReportBookGenerator(rebate_list=rebate_list)
        workbook = BookGenerator.generate_workbook()
        workbook.save(response)
        return response

@user_passes_test(official_check)
def vacation_student_details(request):
    applied_students = None
    unapplied_students = None
    if request.user.official.is_chief() or request.user.official.is_hostel_office(): 
        applied_students = Vacation.objects.all().order_by('submitted')
    elif request.user.official.is_boys_deputy_chief():
        students =  Student.objects.filter(roomdetail__block__gender='Male')
        applied_students = Vacation.objects.filter(room_detail__block__gender = 'Male').order_by('-submitted')
        applied_students_room_detail = applied_students.values('room_detail__student__id')
        unapplied_students = students.exclude(id__in=applied_students_room_detail)
    elif request.user.official.is_girls_deputy_chief():
        students =  Student.objects.filter(roomdetail__block__gender='Female')
        applied_students = Vacation.objects.filter(room_detail__block__gender = 'Female').order_by('-submitted')
        applied_students_room_detail = applied_students.values('room_detail__student__id')
        unapplied_students = students.exclude(id__in=applied_students_room_detail)
    else: 
        students =  request.user.official.block.students()
        applied_students = Vacation.objects.filter(room_detail__block = request.user.official.block).order_by('-submitted')
        applied_students_room_detail = applied_students.values('room_detail__student__id')
        unapplied_students = students.exclude(id__in=applied_students_room_detail)
    return render(request, 'officials/vacation_list.html', {'unapplied_students': unapplied_students, \
        'vacation_list':applied_students, 'user':request.user})

@user_passes_test(official_check)
def vacation_detail(request, pk):
    vac = get_object_or_404(Vacation, id=pk)
    if request.method == 'POST':
        if request.POST.get('submit'):
            vac.submitted = True
            vacation_outing = Outing(
                student = vac.room_detail.student, 
                fromDate = vac.vacated_on,
                toDate = vac.vacated_on,
                purpose = 'vacation',
                type = 'Vacation',
                place_of_visit = vac.journey_destination,
                mode_of_journey_from = vac.mode_of_journey,
            )
            vacation_outing.save()
            vac.vacation_outing_obj = vacation_outing
            vac.save()
            messages.success(request, 'Vacation object submitted successfully.')
        elif request.POST.get('delete'):
            vac.submitted=False
            vac.save()
            vacation_outing = Outing.objects.filter(student=vac.room_detail.student, fromDate=vac.vacated_on, toDate=vac.vacated_on, type='Vacation')
            if vacation_outing:
                vacation_outing.delete()
            else:
                raise Http404('Error: Outing object not found.')
            messages.error(request, 'Vacation object revoked successfully.')
        return redirect('officials:vacation_list')
    return render(request, 'officials/vacation_detail.html', {'vac':vac})

# @user_passes_test(official_check)
# def vacation_history(request):
#     is_chief = request.user.official.is_chief()
#     if is_chief:
#         vacation_list = Vacation.objects.all()
#     else:
#         vacation_list = Vacation.objects.filter(room_detail__block = request.user.official.block)
        
#     return render(request, 'officials/vacation_history.html', {'vacation_list':vacation_list, 'is_chief':is_chief})
# @user_passes_test(official_check)
# def vacation_form(request, ):
#     return render(request, 'officials/room_vacation.html')


# @user_passes_test(chief_warden_check)
# @csrf_exempt
# def watercan(request):
#     name = request.COOKIES['username_off']
#     off_details = Officials.objects.get(emp_id=str(name))
#     block_details = Blocks.objects.get(emp_id_id=str(name))

#     if request.method == 'POST':
#         if request.POST.get('submit_btn'):
#             date = request.POST.get('date')
#             received = request.POST.get('received')
#             given = request.POST.get('given')

#             if WaterCan.objects.filter(block=block_details, date=date).exists():
#                 current = WaterCan.objects.get(block=block_details, date=date)
#                 current.received = received
#                 current.given = given
#                 current.save()
#             else:
#                 newCan = WaterCan(block=block_details, date=date, received=received, given=given)
#                 newCan.save()
#             messages.success(request, 'Water Cans Info updated')
#             return redirect('officials:watercan')

#         elif request.POST.get('count_btn'):
#             if request.POST.get('date_hist'):
#                 date_hist = request.POST.get('date_hist')
#                 if WaterCan.objects.filter(block=block_details, date=date_hist).exists():
#                     dateRec = WaterCan.objects.get(block=block_details, date=date_hist).received
#                     dateGiven = WaterCan.objects.get(block=block_details, date=date_hist).given
#                 else:
#                     dateRec = -10
#                     dateGiven = -10
#                 return render(request, 'officials/water-can.html', {'dateRec':dateRec, 'dateGiven':dateGiven, 'dateUsed':dateGiven})

#             elif request.POST.get('month_hist'):
#                 month = int(request.POST.get('month_hist').split('-')[1])
#                 if WaterCan.objects.filter(block=block_details, date__month=month).exists():
#                     month_set = WaterCan.objects.filter(block=block_details, date__month=month).order_by('-date')
#                     month_rec = month_set.aggregate(Sum('received'))['received__sum']
#                     month_given = month_set.aggregate(Sum('given'))['given__sum']
#                     month_used = month_given
#                     return render(request, 'officials/water-can.html', {'month':request.POST.get('month_hist'), 'month_empty':False, 'month_set':month_set, 'month_rec':month_rec, 'month_given':month_given, 'month_used':month_used})
#                 else:
#                     return render(request, 'officials/water-can.html', {'month_empty':True})



#     return render(request, 'officials/water-can.html')


from .forms import AnnouncementCreationForm, StudentForm, VacationForm, WorkerForm
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy

class OfficialTestMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_official

class ChiefWardenTestMixin(OfficialTestMixin):
    def test_func(self):
        is_official = super().test_func() 
        return is_official and (self.request.user.official.is_chief() or self.request.user.official.is_hostel_office())

class ChiefTestMixin(OfficialTestMixin):
    def test_func(self):
        is_official = super().test_func()
        return is_official and (self.request.user.official.is_chief() or self.request.user.official.is_boys_deputy_chief() or self.request.user.official.is_girls_deputy_chief() or self.request.user.official.is_hostel_office())

class StudentListView(OfficialTestMixin, ListView):
    model = Student
    template_name = 'officials/student_list.html'

    def get_queryset(self):
        if (self.request.user.official.is_chief() or self.request.user.official.is_hostel_office()): return Student.objects.all()
        elif self.request.user.official.is_boys_deputy_chief(): return Student.objects.filter(roomdetail__block__gender='Male')
        elif self.request.user.official.is_girls_deputy_chief(): return Student.objects.filter(roomdetail__block__gender='Female')
        else: return Student.objects.filter(roomdetail__block=self.request.user.official.block) 

class StudentDetailView(OfficialTestMixin, DetailView):
    model = Student
    template_name = 'officials/student_detail.html'

    def get(self, request, *args, **kwargs):
        response =  super().get(request, *args, **kwargs)
        if not (self.request.user.official.is_chief() or self.request.user.official.is_boys_deputy_chief() or self.request.user.official.is_hostel_office() or \
            self.request.user.official.is_girls_deputy_chief()) and (self.object.roomdetail.block != self.request.user.official.block): 
            return HttpResponseForbidden()
        return response


class StudentRegisterView(ChiefWardenTestMixin, CreateView):
    template_name = 'officials/student-register-form.html'
    model = Student
    form_class = StudentForm
    success_url = reverse_lazy('officials:student_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Register Student'
        return context

class StudentUpdateView(ChiefWardenTestMixin, LoginRequiredMixin, UpdateView):
    template_name = 'officials/student-register-form.html'
    model = Student
    form_class = StudentForm
    success_url = reverse_lazy('officials:student_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Student Details'
        return context

class StudentDeleteView(ChiefWardenTestMixin, LoginRequiredMixin, DeleteView):
    model = Student
    success_url = reverse_lazy('officials:student_list')

class OfficialListView(ChiefTestMixin, ListView):
    model = Official
    template_name = 'officials/official_list.html'

    def get_queryset(self):
        if self.request.user.official.is_chief() or self.request.user.official.is_hostel_office():
            return Official.objects.all()
        elif self.request.user.official.is_boys_deputy_chief():
            return Official.objects.filter(block__gender='Male')
        elif self.request.user.official.is_girls_deputy_chief():
            return Official.objects.filter(block__gender='Female')

class OfficialRegisterView(ChiefWardenTestMixin, CreateView):
    template_name = 'officials/official-register-form.html'
    model = Official
    fields = ['emp_id', 'name', 'designation', 'phone', 'account_email', 'email', 'block']
    success_url = reverse_lazy('officials:emp_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Register Official'
        return context

class OfficialUpdateView(ChiefWardenTestMixin, LoginRequiredMixin, UpdateView):
    template_name = 'officials/official-register-form.html'
    model = Official
    fields = ['emp_id', 'name', 'designation', 'phone', 'account_email', 'email', 'block']
    success_url = reverse_lazy('officials:emp_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Official Details'
        return context

class OfficialDeleteView(ChiefWardenTestMixin, LoginRequiredMixin, DeleteView):
    model = Official
    success_url = reverse_lazy('officials:emp_list')

class WorkerListView(ChiefTestMixin, ListView):
    model = Worker
    template_name = 'officials/workers_list.html'

    def get_queryset(self):
        if self.request.user.official.is_chief() or self.request.user.official.is_hostel_office():
            return Worker.objects.all()
        elif self.request.user.official.is_boys_deputy_chief():
            return Worker.objects.filter(block__gender='Male')
        elif self.request.user.official.is_girls_deputy_chief():
            return Worker.objects.filter(block__gender='Female')

class WorkerRegisterView(ChiefWardenTestMixin, CreateView):
    template_name = 'officials/official-register-form.html'
    model = Worker
    form_class = WorkerForm
    success_url = reverse_lazy('officials:workers_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Register Staff'
        return context

class WorkerUpdateView(ChiefWardenTestMixin, LoginRequiredMixin, UpdateView):
    template_name = 'officials/official-register-form.html'
    model = Worker
    form_class = WorkerForm
    success_url = reverse_lazy('officials:workers_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Staff Details'
        return context

class WorkerDeleteView(ChiefWardenTestMixin, LoginRequiredMixin, DeleteView):
    model = Worker
    success_url = reverse_lazy('officials:workers_list')

class ComplaintListView(OfficialTestMixin, LoginRequiredMixin, ListView):
    model = Complaint
    template_name = 'officials/complaint_list.html'

    def get_queryset(self):
        return self.request.user.official.related_complaints(pending=False)

class MedicalIssueListView(OfficialTestMixin, LoginRequiredMixin, ListView):
    model = Complaint
    template_name = 'officials/medical_issue_list.html'

    def get_queryset(self):
        return self.request.user.official.related_medical_issues(pending=False)

class VacationDetails(OfficialTestMixin, SuccessMessageMixin, CreateView):
    template_name = 'officials/room_vacation.html'
    model = Vacation
    form_class = VacationForm
    success_url = reverse_lazy('officials:vacation_list')
    success_message = 'Vacation form created successfully.'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Vacation form'
        return context
    
    def form_valid(self, form):
        roomDetail = get_object_or_404(RoomDetail, id=self.kwargs['pk'])
        form.instance.room_detail = roomDetail
        return super().form_valid(form)

class VacationEditView(OfficialTestMixin, SuccessMessageMixin, UpdateView):
    model = Vacation
    template_name = 'officials/room_vacation.html'
    form_class = VacationForm
    success_message = 'Vacation form updated successfully.'
    success_url = reverse_lazy('officials:vacation_list')

    def get(self, request, *args, **kwargs):
        response =  super().get(request, *args, **kwargs)
        if self.object.submitted: 
            raise Http404('Cannot edit the outing application.')
        return response

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Vacation Application'
        return context

    def form_valid(self,form):
        vacation_obj = get_object_or_404(Vacation, id=self.kwargs['pk'])
        if not vacation_obj.submitted:
            return super().form_valid(form)
        else:
            raise Http404('Cannot edit the outing application.')


    


class AnnouncementCreateView(OfficialTestMixin, SuccessMessageMixin, CreateView):
    template_name = 'officials/announcement_new.html'
    success_message = 'Announcement added successfully.'
    success_url = reverse_lazy('officials:home')
    model = Announcements
    form_class = AnnouncementCreationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create New Announcement'
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class AnnouncementsEditView(OfficialTestMixin, SuccessMessageMixin, UpdateView):
    model =  Announcements
    template_name = 'officials/announcement_new.html'
    form_class = AnnouncementCreationForm
    success_message = 'Announcement Updated successfully.'
    success_url = reverse_lazy('officials:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Announcement'
        return context
    

@user_passes_test(official_check)
def announcement_delete(request, pk):
    if not (request.user.official.is_chief() or request.user.official.is_boys_deputy_chief() or request.user.official.is_girls_deputy_chief() or request.user.official.is_hostel_office()):
        return redirect('officials:home')
    announcement = get_object_or_404(Announcements, id=pk)
    if request.user == announcement.created_by:
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully.')
    return redirect('officials:home')

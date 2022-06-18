from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from django.db.models import Sum
from institute.models import Block, Student, Official
from security.models import OutingInOutTimes
from students.models import Attendance, RoomDetail, Outing, ExtendOuting
from django.contrib import messages
from django.http.response import Http404, HttpResponseForbidden
from complaints.models import Complaint
from mess_feedback.models import MessFeedback
from workers.models import Worker, Attendance as AttendanceWorker
import uuid

def official_check(user):
    return user.is_authenticated and user.is_official
def chief_warden_check(user):
    return official_check(user) and user.official.is_chief()


# Create your views here.
@user_passes_test(official_check)
def home(request):
    user = request.user
    official = user.official
    outing_requests = ''

    if official.is_chief():
        present_students = Attendance.objects.filter(status='Present')
        absent_students = Attendance.objects.filter(status='Absent')
        complaints = official.related_complaints()

    else:
        if not official.block: 
            raise Http404('You are currently not appointed any block! Please contact Admin')

        student_rooms = official.block.roomdetail_set.all()
        student_ids = student_rooms.values_list('student', flat=True)
        students = Student.objects.filter(pk__in=student_ids)
        present_students = Attendance.objects.filter(student__in=students, status='Present')
        absent_students = Attendance.objects.filter(student__in=students, status='Absent')
        complaints = official.related_complaints()
        outing_requests = official.related_outings()

    return render(request, 'officials/home.html', {'user_details': official, 'present':present_students, \
        'absent':absent_students, 'complaints':complaints, 'outings':outing_requests})


@user_passes_test(official_check)
def profile(request):
    user = request.user
    official = user.official
    complaints = Complaint.objects.filter(user = user)
    return render(request, 'officials/profile.html', {'official': official, 'complaints': complaints})


@user_passes_test(official_check)
@csrf_exempt
def attendance(request):
    user = request.user
    official = user.official
    block = official.block
    attendance_list  = Attendance.objects.filter(student__in=block.students())
    date = None

    if request.method == 'POST' and request.POST.get('submit'):
        date = request.POST.get('date')
        for attendance in attendance_list:
            if request.POST.get(str(attendance.id)) and request.POST.get(str(attendance.id))!='not_marked': attendance.mark_attendance(date, request.POST.get(str(attendance.id)))

        messages.success(request, f'Attendance marked for date: {date}')

    if request.GET.get('for_date'):
        date = request.GET.get('for_date')
        messages.info(request, f'Selected date: {date}')
        for item in attendance_list:
            if item.present_dates and date in set(item.present_dates.split(',')): item.present_on_date = True
            if item.absent_dates and date in set(item.absent_dates.split(',')): item.absent_on_date = True

    return render(request, 'officials/attendance.html', {'official': official, 'attendance_list': attendance_list, 'date': date})


@user_passes_test(official_check)
@csrf_exempt
def attendance_workers(request):
    user = request.user
    official = user.official
    block = official.block
    attendance_list  = AttendanceWorker.objects.filter(worker__in=block.worker_set.all())
    date = None 

    if request.method == 'POST' and request.POST.get('submit'):
        date = request.POST.get('date')
        for attendance in attendance_list:
            if request.POST.get(str(attendance.id)): attendance.mark_attendance(date, request.POST.get(str(attendance.id)))

        messages.success(request, f'Staff Attendance marked for date: {date}')

    if request.GET.get('for_date'):
        date = request.GET.get('for_date')
        messages.info(request, f'Selected date: {date}')
        for item in attendance_list:
            if item.present_dates and  date in set(item.present_dates.split(',')): item.present_on_date = True
            if item.absent_dates and date in set(item.absent_dates.split(',')): item.absent_on_date = True

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

    if official.is_chief():
        attendance_list = Attendance.objects.all()
    else:
        attendance_list = Attendance.objects.filter(student__in = official.block.students())

    if request.GET.get('by_regd_no'):
        try:
            student = attendance_list.get(student__regd_no = request.GET.get('by_regd_no')).student
            if student.attendance.present_dates: present_dates = student.attendance.present_dates.split(',') 
            if student.attendance.absent_dates: absent_dates = student.attendance.absent_dates.split(',')
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


@user_passes_test(official_check)
def outing_detail(request, pk):
    outing = get_object_or_404(Outing, id=pk)
    user = request.user
    official = user.official
    type = outing.type
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
            if(request.POST.get('textarea')):
                if outing.permission == 'Processing':
                    outing.remark_by_warden = request.POST.get('textarea')
                elif outing.permission == 'Processing Extension':
                    outingExtendObj.remark_by_warden = request.POST.get('textarea')
                    outingExtendObj.save()

            if request.POST.get('permission'):
                if request.POST.get('permission') == 'Granted':
                    if outing.type != 'Local' and request.POST.get('permission') == 'Granted':
                        if outing.permission == 'Processing':
                            outing.permission = 'Granted'
                        elif outing.permission == 'Processing Extension':
                            outing.permission = 'Extension Granted'
                            outing.fromDate = outingExtendObj.fromDate
                            outing.toDate = outingExtendObj.toDate
                            outing.place_of_visit = outingExtendObj.place_of_visit
                            outing.purpose = outingExtendObj.purpose
                            outing.remark_by_caretaker = outingExtendObj.remark_by_caretaker
                            outing.remark_by_warden = outingExtendObj.remark_by_warden
                            outingExtendObj.permission = 'Extension Granted'
                            outingExtendObj.save()
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
                if outing.permission == 'Pending':
                    outing.remark_by_caretaker = request.POST.get('textarea')
                elif outing.permission == 'Pending Extension':
                    outingExtendObj.remark_by_caretaker = request.POST.get('textarea')
                    outingExtendObj.save()
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
    return render(request, 'officials/outing_show.html', {'type':type, 'official':official.designation, \
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
                    room_detail.full_clean()
                    room_detail.save()
                    messages.success(request, f'Student {student.regd_no} successfully alloted room in {room_detail.block.name} {room_detail.room()}!')
            except RoomDetail.DoesNotExist as error:
                # Day Scholars have no room detail.
                messages.error(request, "Cannot assign room to day scholars.")
            except ValidationError as error:
                for message in error.messages:
                    messages.error(request, message)
            except Student.DoesNotExist:
                messages.error(request, f'Student not found!')

        if request.POST.get('remove'):
            room_detail = RoomDetail.objects.get(id = request.POST.get('roomdetail_id'))
            room_detail.block = None
            room_detail.floor = None
            room_detail.room_no = None
            room_detail.save()
            messages.success(request, f'Student {room_detail.student.regd_no} removed from room.')

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
    if official.is_chief():
        valid_outing_list = OutingInOutTimes.objects.all()
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
    if official.is_chief():
        block_id = 'all'
    else:
        block_id = official.block.id
    print(year_month_day)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
    response['Content-Disposition'] = 'attachment; filename=Outing({date}).xlsx'.format(date=year_month_day+" "+str(timezone.now().strftime('%d-%m-%Y')),)
    
    BookGenerator = OutingBookGenerator(block_id, year_month_day)
    workbook = BookGenerator.generate_workbook()
    workbook.save(response)

    return response

@user_passes_test(official_check)
def mess_feedback_analysis(request):
    calendar_feedback = None
    type_feedback = None
    if request.method == 'POST':
        if request.POST.get('by_date'):
            calendar_feedback = MessFeedback.objects.filter(date=request.POST.get('by_date'))
        elif request.POST.get('by_month'):
            year, month = request.POST.get('by_month').split('-')
            calendar_feedback = MessFeedback.objects.filter(date__year=year, date__month=month)
        elif request.POST.get('by_year'):
            calendar_feedback = MessFeedback.objects.filter(date__year=request.POST.get('by_year'))
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
        print(feedback_obj)
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
                   'date': request.POST.get('by_date'),
                   'month': request.POST.get('by_month'),
                   'year': request.POST.get('by_year'),
                   'type': request.POST.get('by_type'),
                   'count': len(feedback_obj)
        }
        return render(request, 'officials/mess_feedback_analysis.html', context=context)

    return render(request, 'officials/mess_feedback_analysis.html')
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


from .forms import StudentForm, WorkerForm
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy

class OfficialTestMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_official

class ChiefWardenTestMixin(OfficialTestMixin):
    def test_func(self):
        is_official = super().test_func() 
        return is_official and self.request.user.official.is_chief()

class StudentListView(OfficialTestMixin, ListView):
    model = Student
    template_name = 'officials/student_list.html'

    def get_queryset(self):
        if self.request.user.official.is_chief(): return Student.objects.all()
        else: return Student.objects.filter(roomdetail__block=self.request.user.official.block) 

class StudentDetailView(OfficialTestMixin, DetailView):
    model = Student
    template_name = 'officials/student_detail.html'

    def get(self, request, *args, **kwargs):
        response =  super().get(request, *args, **kwargs)
        if not self.request.user.official.is_chief() and (self.object.roomdetail.block != self.request.user.official.block): 
            return HttpResponseForbidden()
        return response


class StudentRegisterView(CreateView):
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

class OfficialListView(ChiefWardenTestMixin, ListView):
    model = Official
    template_name = 'officials/official_list.html'

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

class WorkerListView(ChiefWardenTestMixin, ListView):
    model = Worker
    template_name = 'officials/workers_list.html'

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

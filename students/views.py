from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.http import Http404, HttpResponse
from institute.models import Student
from security.models import OutingInOutTimes
from students.models import ExtendOuting, Outing
from complaints.models import Complaint
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import user_passes_test
from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from .forms import OutingExtendForm, OutingForm
from django.db.models import F
from django.contrib import messages



class StudentTestMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_student

def student_check(user):
    return user.is_authenticated and user.is_student

# Create your views here.

@user_passes_test(student_check)
def home(request):
    user = request.user
    student = user.student
    present_dates_count = (student.attendance.present_dates and len(student.attendance.present_dates.split(','))) or 0
    absent_dates_count = (student.attendance.absent_dates and len(student.attendance.absent_dates.split(','))) or 0
    outing_count = len(student.outing_set.all())
    rating = student.rating
    complaints = Complaint.objects.filter(user = user, status="Registered") | Complaint.objects.filter(user = user, status="Processing")

    return render(request, 'students/home.html', {'student': student, 'present_dates_count':present_dates_count, \
        'absent_dates_count':absent_dates_count, 'outing_count': outing_count, 'complaints':complaints, 'rating':rating})


class OutingListView(StudentTestMixin, ListView):
    model = Student
    template_name = 'students/outing_list.html'
    context_object_name = 'outing_list'

    def get_queryset(self):
        outing_set = Outing.objects.filter(student=self.request.user.student).annotate(outTime=F('outinginouttimes__outTime'), \
            inTime=F('outinginouttimes__inTime'))
        return outing_set


class OutingCreateView(StudentTestMixin, SuccessMessageMixin, CreateView):
    model = Outing
    form_class = OutingForm
    template_name = 'students/outing_form.html'
    success_url = reverse_lazy('students:outing_list')
    success_message = 'Outing application successfully created!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Outing Application'
        return context
    def get_form_kwargs(self):
        kwargs = super(OutingCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    def form_valid(self, form):
        form.instance.student = self.request.user.student
        return super().form_valid(form)

# class OutingUpdateView(StudentTestMixin, SuccessMessageMixin, UpdateView):
#     model = Outing
#     form_class = OutingForm
#     template_name = 'students/outing_form.html'
#     success_url = reverse_lazy('students:outing_list')
#     success_message = 'Outing application successfully updated!'

#     def get(self, request, *args, **kwargs):
#         response =  super().get(request, *args, **kwargs)
#         if not (self.object.student == self.request.user.student and self.object.is_editable()): 
#             raise Http404('Cannot edit the outing application.')
#         return response

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if self.object.is_editable():
#             context['form_title'] = 'Edit Outing Application'
#         return context
    
#     def get_form_kwargs(self):
#         kwargs = super(OutingUpdateView, self).get_form_kwargs()
#         kwargs['request'] = self.request
#         return kwargs

#     def form_valid(self, form):
#         form.instance.student = self.request.user.student
#         return super().form_valid(form)


@user_passes_test(student_check)
def attendance_history(request):
    student = request.user.student
    present_dates = (student.attendance.present_dates and student.attendance.present_dates.split(',')) or None
    absent_dates = (student.attendance.absent_dates and student.attendance.absent_dates.split(',')) or None

    return render(request, 'students/attendance_history.html', {'student': student, 'present_dates': present_dates, 'absent_dates': absent_dates})

@user_passes_test(student_check)
def cancel_outing(request, pk):
    if request.method == 'POST':
        outing = get_object_or_404(Outing, id=pk)
        print(outing.status)
        if outing.permission == 'Pending':
            Outing.objects.get(id=pk).delete()
        elif outing.status!='In Outing':
            outing.permission = 'Revoked'
            outing.save()
        return redirect('students:outing_list')
    else:
        return HttpResponse("not post")

@user_passes_test(student_check)
def outing_QRCode(request, pk):
    outing_obj = get_object_or_404(Outing, id=pk)
    if outing_obj.is_qr_viewable():
        return render(request, 'students/render_qr_code.html', {'outing':outing_obj})
    messages.error(request, 'Qr is not viewable yet.')
    return redirect('students:home')


@user_passes_test(student_check)
def outing_details(request, pk):
    outing_set = Outing.objects.filter(id=pk).annotate(outTime=F('outinginouttimes__outTime'), \
            inTime=F('outinginouttimes__inTime'), remark_by_security=F('outinginouttimes__remark_by_security'))
    return render(request, 'students/outing_specific.html', {'outing':outing_set[0]})
class OutingExtendView(StudentTestMixin, SuccessMessageMixin, CreateView):
    model = ExtendOuting
    form_class = OutingExtendForm
    template_name = 'students/outing_form.html'
    success_url = reverse_lazy('students:outing_list')
    success_message = 'Outing application successfully extended!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Extend Outing Application'
        return context
    def get_form_kwargs(self):
        kwargs = super(OutingExtendView, self).get_form_kwargs()
        outing = get_object_or_404(Outing, id=self.kwargs['pk'])
        kwargs['object'] = outing
        kwargs['request'] = self.request
        return kwargs
    def form_valid(self, form):
        outing = get_object_or_404(Outing, id=self.kwargs['pk'])
        outing.permission = 'Pending Extension'
        outing.save()
        form.instance.outing = outing
        return super().form_valid(form)




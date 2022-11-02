from django.urls import reverse
from .models import Complaint, MedicalIssue
from institute.models import Official, Student
from django.http.response import Http404
from django.views.generic import DetailView, UpdateView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from .forms import MedicalIssueUpdationForm
from complaints.forms import ComplaintUpdationForm
import re
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages



# Create your views here.
class ComplaintDetailView(LoginRequiredMixin, DetailView):
    template_name = 'complaints/show.html'

    def get(self, request, *args, **kwargs):
        response =  super().get(request, *args, **kwargs)
        if self.request.user.is_student and (self.object.entity() != self.request.user.student): 
            raise Http404()
        return response


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.object.can_edit(self.request.user)
        if self.model == Complaint:
            form = ComplaintUpdationForm(instance=self.object, request=self.request)
            context['form'] = form
        else:
            context['form'] = MedicalIssueUpdationForm(instance=self.object)
        context['user'] = self.request.user
        return context

class ComplaintCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'complaints/new.html'
    
    def get_success_message(self, cleaned_data):
        if self.model == Complaint:
            if self.object.type== 'Civil':
                self.send_estate_civil_mail()
            elif self.object.type== 'Electrical':
                self.send_estate_electrical_mail()
            elif self.object.type== 'Food Issues':
                self.send_mess_mail()
            elif self.object.type== 'Network Issue':
                self.send_network_mail()
        elif self.model== MedicalIssue:
            self.send_doctor_mail()
        
        return '{} created successfully!'.format(self.model.__name__)

    def send_estate_civil_mail(self):
        from django.core.mail import send_mail
        from django.conf import settings
        student=self.object.user.student
        email = ['']
        send_mail(
        subject='Civil Issue',
        message='Civil issue is raised by student',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=email,
        fail_silently=False,
        html_message="Civil issue is raised by : "+str(student.name)+"\n "+(student.roll_no) +'\n  Summary: '+str(self.object.summary)+', \n Details: '+str(self.object.detailed)
        )
    def send_estate_electrical_mail(self):
        from django.core.mail import send_mail
        from django.conf import settings
        student=self.object.user.student
        email = ['']
        send_mail(
        subject='Electrical Issue',
        message='Electrical issue is raised by student',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=email,
        fail_silently=False,
        html_message="Electrical issue is raised by : "+str(student.name)+"\n "+(student.roll_no) +'\n  Summary: '+str(self.object.summary)+', \n Details: '+str(self.object.detailed)
        )
    def send_network_mail(self):
        from django.core.mail import send_mail
        from django.conf import settings
        student=self.object.user.student
        email = ['']
        send_mail(
        subject='Network Issue',
        message='Network Issue is raised by student',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=email,
        fail_silently=False,
        html_message="Network Issue is raised by : "+str(student.name)+"\n "+(student.roll_no) +'\n  Summary: '+str(self.object.summary)+', \n Details: '+str(self.object.detailed)
        )
    def send_mess_mail(self):
        from django.core.mail import send_mail
        from django.conf import settings
        student=self.object.user.student
        email = ['']
        send_mail(
        subject='Food Issue',
        message='Food issue is raised by student',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=email,
        fail_silently=False,
        html_message="Food issue is raised by : "+str(student.name)+"\n "+(student.roll_no) +'\n  Summary: '+str(self.object.summary)+', \n Details: '+str(self.object.detailed)
        )
    
    def send_doctor_mail(self):
        from django.core.mail import send_mail
        from django.conf import settings
        student=self.object.user.student
        email = ['']
        send_mail(
        subject='Health Issue',
        message='Health issue is raised by student',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=email,
        fail_silently=False,
        html_message="Health issue is raised by : "+str(student.name)+"\n "+(student.roll_no) +'\n  Summary: '+str(self.object.summary)+', \n Details: '+str(self.object.detailed)
        )


    def get_success_url(self):
        return self.request.user.home_url()

    def form_valid(self, form):
        form.instance.user = self.request.user

        if self.model == Complaint:
            form.instance.complainee = form.cleaned_data.get('complainee_id') and Student.objects.get(regd_no = form.cleaned_data.get('complainee_id'))

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model_label = re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', self.model.__name__) # CamelCase to Title Case
        context['form_title'] = 'Register {}'.format(model_label)
        context['object_name'] = model_label
        return context

    
class ComplaintUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    def get_success_message(self, cleaned_data):
        return '{} updated successfully!'.format(self.get_object().model_name())

    def get_success_url(self):
        # return self.request.user.home_url()
        return reverse('complaints:{}_detail'.format((self.model.__name__).lower()), args=[self.get_object().pk])
    def form_valid(self, form):
        if form.cleaned_data['status']=='Resolved' and 'indisciplinary_points' in form.data and form.data['indisciplinary_points']!='':
            student = get_object_or_404(Student, regd_no=form.instance.complainee.regd_no)
            student.update_disciplinary_rating(points=int(form.data['indisciplinary_points']))
            student.save()
        return super().form_valid(form)

class ComplaintDeleteView(LoginRequiredMixin, DeleteView):

    def get_success_url(self):
        return self.request.user.home_url()

    def form_valid(self, form):
        if self.object.status == 'Registered' and self.object.user == self.request.user:
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Unauthorized to delete complaint')
            return redirect (self.get_success_url())
        
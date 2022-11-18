from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from mess_feedback.models import MessFeedback, get_type
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone

# Create your views here.
def official_check(user):
    return user.is_authenticated and user.is_official
def student_check(user):
    return user.is_authenticated and user.is_student 

def mess_incharge_check(user):
    if user.is_worker:
        worker = user.worker
        return worker.designation == 'Mess Incharge'
    return False

def mess_feedback_check(user):
    if(official_check(user) or mess_incharge_check(user)):
        return True
    return False

# @user_passes_test(user_check)
def mess_feedback_view(request):
    session = get_type()
    if not session:
        messages.error(request, 'No active mess session.') 
        return redirect(request.user.home_url())
    if request.method == 'POST':
        if session!=request.POST.get('type'):
            messages.error(request, 'No active mess session.') 
            return redirect(request.user.home_url())
        mess_feedback_obj = MessFeedback.objects.filter(user=request.user, date=timezone.localdate(), \
            type=request.POST.get('type'))
        if len(mess_feedback_obj)==0:
            mess_feedback_obj = MessFeedback(user=request.user, date=timezone.localdate(), \
                type=request.POST.get('type'), rating=request.POST.get('rating'), review=request.POST.get('review'))
            mess_feedback_obj.save()
        else:
            mess_feedback_obj[0].rating = request.POST.get('rating')
            mess_feedback_obj[0].review = request.POST.get('review')
            mess_feedback_obj[0].save()
        messages.success(request, 'Feedback noted Successfully!')
        return redirect(request.user.home_url())
    return render(request, 'mess_feedback/mess_feedback.html', {'form_title': 'Mess Feedback', 'date':timezone.localdate(), 'session':session})


from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from mess_feedback.models import MessFeedback
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

# Create your views here.
def official_check(user):
    return user.is_authenticated and user.is_official
def student_check(user):
    return user.is_authenticated and user.is_student


@user_passes_test(student_check)
def mess_feedback_view(request):
    if request.method == 'POST':
        mess_feedback_obj = MessFeedback.objects.filter(user=request.user, date=request.POST.get('date'), \
            type=request.POST.get('type'))
        if len(mess_feedback_obj)==0:
            mess_feedback_obj = MessFeedback(user=request.user, date=request.POST.get('date'), \
                type=request.POST.get('type'), rating=request.POST.get('rating'), review=request.POST.get('review'))
            mess_feedback_obj.save()
        else:
            mess_feedback_obj[0].rating = request.POST.get('rating')
            mess_feedback_obj[0].review = request.POST.get('review')
            mess_feedback_obj[0].save()
        messages.success(request, 'Feedback noted Successfully!')
        return redirect('students:home')
            
        
    return render(request, 'mess_feedback/mess_feedback.html', {'form_title': 'Mess Feedback'})

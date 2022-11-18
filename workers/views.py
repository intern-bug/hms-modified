from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from complaints.models import Complaint, MedicalIssue
from django.contrib.auth.decorators import user_passes_test, login_required

def worker_check(user):
    return user.is_authenticated and user.is_worker


# def mess_incharge_check(user):
#     if user.is_worker:
#         worker = user.worker
#         return worker.designation == 'Mess Incharge'
#     return False


# Create your views here.
@user_passes_test(worker_check)
def home(request):
    user = request.user
    worker = user.worker    

    if worker.designation == 'Electrician':
        complaints = Complaint.objects.filter(type='Electrical', status__in=['Registered', 'Processing', 'Resolved'])
    elif worker.designation == 'Estate Staff':
        complaints = Complaint.objects.filter(type__in=['Electrical', 'Civil'], status__in=['Registered', 'Processing', 'Resolved'])
    elif worker.designation == 'Mess Incharge':
        complaints = Complaint.objects.filter(type='Food Issues', status__in=['Registered', 'Processing', 'Resolved'])
    elif worker.designation == 'Doctor':
        complaints = MedicalIssue.objects.all()
    else:
        raise PermissionDenied

    return render(request, 'workers/home.html', {'worker': worker, 'complaints': complaints,})

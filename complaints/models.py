from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from institute.models import Student
from django.conf import settings

User = get_user_model()

# Create your models here.
class Complaint(models.Model):
    STATUS = (
        ('Registered','Registered'),
        ('Processing','Processing'),
        ('Resolved','Resolved')
    )

    def complaint_file_storage(instance, filename):
        extension = filename.split('.')[-1]
        name = str(instance.user_id)+'_'+str((instance.created_at.strftime("%d-%m-%Y_%H-%M-%S")))
        return 'Complaints/Year-{}/{}.{}'.format(timezone.localtime().year, name, extension)
        
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=40, null=False)
    complainee = models.ForeignKey(Student, on_delete=models.DO_NOTHING, null=True, blank=True)
    summary = models.CharField(max_length=200,null=False)
    detailed = models.TextField(null=False)
    status = models.CharField(max_length=20,null=False,default='Registered',choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remark = models.TextField(null=True, blank=True)
    file = models.FileField(null=True, blank=True, upload_to=complaint_file_storage)
    
    def entity(self):
        return self.user.entity()

    def can_edit(self, user):
        if user.is_official and user.official.is_chief():
            return True
        elif user.is_official and user.official.is_warden() and self.status == 'Processing' and ((self.user.entity_type() != 'Student' and self.entity().block == user.official.block) or self.entity().roomdetail.block == user.official.block):
            return True
        elif user.is_official and user.official.is_caretaker() and self.status == 'Registered' and ((self.user.entity_type() != 'Student' and self.entity().block == user.official.block) or self.entity().roomdetail.block == user.official.block):
            return True
        elif user.is_worker:
            return True

        return False

    def model_name(self):
        return "Complaint"

class MedicalIssue(models.Model):
    STATUS = (
        ('Registered','Registered'),
        ('Processing','Processing'),
        ('Resolved','Resolved')
    )

    EMERGENCY_OUTING_OPTIONS = (
        ('NA', '----------'),
        ('Allow', 'Allow'),
        ('Disallow', 'Disallow')
    )

    def medical_issue_file_storage(instance, filename):
        extension = filename.split('.')[-1]
        name = str(instance.user_id)+'_'+str((instance.created_at.strftime("%d-%m-%Y_%H-%M-%S")))
        return 'Medical_Issue/Year-{}/{}.{}'.format(timezone.localtime().year, name, extension)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20,null=False,default='Registered',choices=STATUS)
    summary = models.CharField(max_length=200,null=False)
    detailed = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remark = models.TextField(null=True, blank=True)
    emergency_outing_permission = models.CharField(max_length=8, choices=EMERGENCY_OUTING_OPTIONS, default='NA')
    file = models.FileField(null=True, blank=True, upload_to=medical_issue_file_storage)

    def entity(self):
        return self.user.entity()

    def can_edit(self, user):
        if user.is_worker and user.worker.designation == 'Doctor':
            return True
        return False

    def model_name(self):
        return "Medical Issue"
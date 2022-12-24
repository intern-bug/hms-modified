from unicodedata import decimal
import complaints
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.validators import MinLengthValidator
from institute.validators import numeric_only, date_no_future
from institute.constants import FLOOR_OPTIONS
from students.models import Outing
from security.models import OutingInOutTimes
from django.utils import timezone
from django.contrib.auth import get_user_model


User = get_user_model()

# Create your models here.
class Student(models.Model):
    YEAR = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
    )

    GENDER=(
        ('Male','Male'),
        ('Female','Female'),
    )

    PROGRAMME_OPTIONS=(
        ('B.Tech.', 'B.Tech.'),
        ('M.Tech.', 'M.Tech.'),
        ('MS(Research)','MS(Research)'),
        ('Ph.D', 'Ph.D'),
        ('Project Staff', 'Project Staff'),
        ('Interns', 'Interns'),
        ('Others', 'Others')
    )

    def photo_storage_path(instance, filename):
        extension = filename.split('.')[-1]
        return 'Student-Photos/Year-{}/{}.{}'.format(instance.year, instance.regd_no, extension)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    account_email = models.EmailField(unique=True, null=True, blank=True)
    regd_no = models.CharField(unique=True, null=False, max_length=8, validators=[MinLengthValidator(6)])
    roll_no = models.CharField(unique=True, null=True, blank=True, max_length=8, validators=[MinLengthValidator(6)])
    name = models.CharField(max_length=100, null=False)
    email = models.EmailField(null=True, blank=True)
    year = models.IntegerField(null=False, choices=YEAR)
    branch = models.CharField(max_length=40,null=True, blank=True)
    gender = models.CharField(max_length=7,choices=GENDER,null=False)
    pwd = models.BooleanField(null=False, default=False, blank=True)
    community = models.CharField(max_length=25, null=True, blank=True)
    aadhar_number = models.CharField(max_length=12, null=True, blank=True, validators=[MinLengthValidator(4)], default='0000')
    dob = models.DateField(null=True, default="2000-01-01",validators=[date_no_future], blank=True)
    blood_group = models.CharField(max_length=25, null=True, blank=True)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(null=False, max_length=10, validators=[numeric_only])
    parents_phone = models.CharField(null=True, max_length=10, validators=[numeric_only], blank=True)
    emergency_phone = models.CharField(null=True, blank=True, max_length=10, validators=[numeric_only])
    address = models.TextField(null=True, blank=True)
    photo = models.ImageField(null=True, blank=True, upload_to=photo_storage_path)
    is_hosteller = models.BooleanField(null=False, default=True)
    outing_rating = models.DecimalField(null=False,blank=True, default=5.0, max_digits=3, decimal_places=2)
    discipline_rating = models.DecimalField(null=False, blank=True, default=5.0, max_digits=3, decimal_places=2)
    specialization = models.CharField(max_length=15, choices=PROGRAMME_OPTIONS, null=False)

    def __str__(self):
        return str(self.regd_no)

    def clean(self):
        super().clean()
        if not self.is_hosteller and hasattr(self, 'roomdetail'):
            raise ValidationError("Day scholars cannot be alloted a room.")

    def block(self):
        return self.roomdetail.block

    def calculate_rating(self, outingInOutObj):
        outingInOutObjs = OutingInOutTimes.objects.filter(outing__student=self).filter(inTime__isnull=False)
        invalid = round((5-self.outing_rating)*len(outingInOutObjs))
        if outingInOutObj.outing.type == 'Local':
            if outingInOutObj.outing.student.gender == 'Male' and outingInOutObj.inTime != None:
                if (outingInOutObj.inTime.date()!=outingInOutObj.outing.toDate.date()) or ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/3600) > 6 :
                    invalid+=1.5
                elif ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/60) > 60.0:
                    invalid+=1
                elif ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/60) > 15.0:
                    invalid+=0.5
            elif outingInOutObj.outing.student.gender == 'Female' and outingInOutObj.inTime != None:
                if (outingInOutObj.inTime.date()!=outingInOutObj.outing.toDate.date()) or (outingInOutObj.inTime.hour*100 + outingInOutObj.inTime.minute) > 2145 :
                    invalid+=1.5
                elif ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/60) > 60.0:
                    invalid+=1
                elif ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/60) > 15.0:
                    invalid+=0.5 
        else:
            if outingInOutObj.inTime != None and ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/3600) > 24:
                invalid+=2
            elif outingInOutObj.inTime != None and ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/3600) > 12:
                invalid+=1.5
            elif outingInOutObj.inTime != None and ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/3600) > 6:
                invalid+=1
            elif outingInOutObj.inTime != None and ((outingInOutObj.inTime - outingInOutObj.outing.toDate).total_seconds()/3600) > 1.5:
                invalid+=0.5
        if len(outingInOutObjs)!=0:
            rating = 5-(invalid/(len(outingInOutObjs)+1))
        elif (len(outingInOutObjs)-invalid) < 0:
            rating = 0
        else:
            rating = 5
        return rating

    def update_disciplinary_rating(self, points):
        if (float(self.discipline_rating) - (points/5)) > 0:
            self.discipline_rating = float(self.discipline_rating) - (points/5)
        else:
            self.discipline_rating = 0

    def related_announcements(self):
        warden = (self.block().warden() and self.block().warden().user.id) or None
        chief = (self.block().chief_warden() and self.block().chief_warden()[0].user.id) or None
        deputy = (self.block().deputy_chief_warden() and self.block().deputy_chief_warden()[0].user.id) or None
        return Announcements.objects.filter(created_by__in=[warden, chief, deputy]).exclude(officials_only = True)


class Official(models.Model):
    EMP=(
        ('Caretaker','Caretaker'),
        ('Warden','Warden'),
        ('Deputy Chief-Warden Boys', 'Deputy Chief-Warden Boys'),
        ('Deputy Chief-Warden Girls', 'Deputy Chief-Warden Girls'),
        ('Chief-Warden','Chief-Warden'),
        ('Hostel Office','Hostel Office'),
        
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    account_email = models.EmailField(unique=True, null=False)
    emp_id = models.CharField(unique=True,null=False, max_length=20)
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=25,choices=EMP)
    phone = models.CharField(max_length=10, null=False, validators=[numeric_only])
    email = models.EmailField(null=True, blank=True)
    block = models.ForeignKey('institute.Block', on_delete=models.SET_NULL, null=True, blank=True)

    def is_chief(self):
        return (self.designation == 'Deputy Chief-Warden' or self.designation == 'Chief-Warden')
    
    def is_caretaker(self):
        return (self.designation == 'Caretaker')

    def is_warden(self):
        return self.designation == 'Warden'
    
    def is_boys_deputy_chief(self):
        return self.designation == 'Deputy Chief-Warden Boys'
    
    def is_girls_deputy_chief(self):
        return self.designation == 'Deputy Chief-Warden Girls'

    

    def is_hostel_office(self):
        return self.designation == 'Hostel Office'

    def clean(self):
        if (self.is_chief() or self.is_boys_deputy_chief() or self.is_girls_deputy_chief() or self.is_hostel_office()) and self.block != None:
            raise ValidationError('Chief Warden and Deputy Chief Warden cannot be assigned a block.')
    
    def related_outings(self):
        if self.is_warden():
            return Outing.objects.filter(student__in=self.block.students(), permission__in=['Processing', 'Processing Extension']).\
                filter(toDate__gt=timezone.now()).exclude(status='Closed') | Outing.objects.filter(~Q(status='Closed'), type='Vacation', permission__in=['Processing', 'Processing Extension'])
        elif self.is_caretaker():
            return Outing.objects.filter(student__in=self.block.students(), permission__in=['Pending', 'Pending Extension']).\
                filter(toDate__gt=timezone.now()).exclude(status='Closed') | Outing.objects.filter(~Q(status='Closed'), type='Vacation', permission__in=['Pending', 'Pending Extension'])
        else:
            raise ValidationError('You are not authorized to view outings.')

    def related_complaints(self, pending=True):
        if self.is_chief() or self.is_hostel_office():
            if pending:
                return complaints.models.Complaint.objects.filter(status__in=['Registered', 'Processing']) # | complaints.models.Complaint.objects.filter(status='Processing')
            else:
                return complaints.models.Complaint.objects.all()
        elif self.is_boys_deputy_chief():
            users = User.objects.filter(Q(official__block__gender='Male') | Q(student__roomdetail__block__gender='Male'))
            if pending:
                return complaints.models.Complaint.objects.filter(user__in=users, status__in=['Registered', 'Processing'])
            else:
                return complaints.models.Complaint.objects.filter(user__in=users)
        elif self.is_girls_deputy_chief():
            users = User.objects.filter(Q(official__block__gender='Female') | Q(student__roomdetail__block__gender='Female'))
            if pending:
                return complaints.models.Complaint.objects.filter(user__in=users, status__in=['Registered', 'Processing'])
            else:
                return complaints.models.Complaint.objects.filter(user__in=users)
        else:
            students = self.block.students()
            users = list(students.values_list('user', flat=True))
            officials = self.block.officials()
            users = users + list(officials.values_list('user', flat=True))
            workers = self.block.workers()
            users = users + list(workers.values_list('user', flat=True))
            if pending:
                return complaints.models.Complaint.objects.filter(user__in=users, status__in=['Registered', 'Processing']) | self.user.complaint_set.filter(status__in=['Registered', 'Processing'])
            else:
                return complaints.models.Complaint.objects.filter(user__in=users) | self.user.complaint_set.all()

    def related_medical_issues(self, pending=True):
        if self.is_chief() or self.is_hostel_office():
            if pending:
                return complaints.models.MedicalIssue.objects.filter(status='Registered')
            else:
                return complaints.models.MedicalIssue.objects.all()
        elif self.is_boys_deputy_chief():
            users = User.objects.filter(Q(official__block__gender='Male') | Q(student__roomdetail__block__gender='Male'))
            if pending:
                return complaints.models.MedicalIssue.objects.filter(user__in=users, status='Registered')
            else:
                return complaints.models.MedicalIssue.objects.filter(user__in=users)
        elif self.is_girls_deputy_chief():
            users = User.objects.filter(Q(official__block__gender='Female') | Q(student__roomdetail__block__gender='Female'))
            if pending:
                return complaints.models.MedicalIssue.objects.filter(user__in=users, status='Registered')
            else:
                return complaints.models.MedicalIssue.objects.filter(user__in=users)
        else:
            students = self.block.students()
            users = students.values_list('user', flat=True)
            if pending:
                return complaints.models.MedicalIssue.objects.filter(user__in=users, status='Registered') | self.user.medicalissue_set.filter(status='Registered')
            else:
                return complaints.models.MedicalIssue.objects.filter(user__in=users) | self.user.medicalissue_set.all()

    def related_announcements(self):
        if self.is_chief() or self.is_hostel_office()or self.is_boys_deputy_chief() or self.is_girls_deputy_chief() :
            return Announcements.objects.all()
        else:
            warden = (self.block.warden() and self.block.warden().user.id) or None
            chief = (self.block.chief_warden() and self.block.chief_warden()[0].user.id) or None
            deputy = (self.block.deputy_chief_warden() and self.block.deputy_chief_warden()[0].user.id) or None
            return Announcements.objects.filter(created_by__in=[warden, chief, deputy])

    def __str__(self):
        return str(self.emp_id)


class Block(models.Model):
    OPTION=(
          ('1S','One student per Room'),
          ('2S','Two students per Room'),
          ('4S','Four students per Room'),
     )

    GENDER=(
        ('Male','Male'),
        ('Female','Female'),
     )

    block_id = models.CharField(unique=True, max_length=20)
    name = models.CharField(max_length=50,null=False)
    room_type = models.CharField(max_length=2,choices=OPTION)
    gender = models.CharField(max_length=7,choices=GENDER)
    floor_count = models.IntegerField(null=False, verbose_name="No. of Floors")
    capacity = models.IntegerField(null=False)

    def __str__(self):
        return self.name

    def short_name(self):
        return self.name.split()[0]

    def available_floors(self):
        if self.short_name()=='Vamsadhara-I':
            return FLOOR_OPTIONS[:self.floor_count]
        elif self.short_name()=='Vamsadhara-II':
            return FLOOR_OPTIONS[3:self.floor_count+3]
        elif self.short_name()=='Nagavali-I':
            return FLOOR_OPTIONS[:self.floor_count]
        elif self.short_name()=='Nagavali-II':
            return FLOOR_OPTIONS[4:self.floor_count+4]
        return FLOOR_OPTIONS[:self.floor_count]

    def per_room_capacity(self):
        import re
        # Regex to find room_capacity from room_type
        return int(re.search(r'\d+', self.room_type).group())

    def student_capacity(self):
        if self.room_type == '4S':   return self.capacity*4
        elif self.room_type == '2S': return self.capacity*2
        elif self.room_type == '1S': return self.capacity

    def roomdetails(self):
        return self.roomdetail_set.all()

    def students(self):
        student_rooms = self.roomdetail_set.all()
        student_ids = student_rooms.values_list('student', flat=True)
        return Student.objects.filter(pk__in=student_ids)

    def officials(self):
        return self.official_set
    
    def workers(self):
        return self.worker_set

    def caretaker(self):
        return self.official_set.filter(designation='Caretaker').first()

    def warden(self):
        return self.official_set.filter(designation='Warden').first()
    
    def chief_warden(self):
        return Official.objects.filter(designation='Chief-Warden')
    
    def deputy_chief_warden(self):
        if self.gender=='Male':
            return Official.objects.filter(designation='Deputy Chief-Warden Boys')
        if self.gender == 'Female':
            return Official.objects.filter(designation='Deputy Chief-Warden Girls')

class Announcements(models.Model):

    def announcement_file_storage(instance, filename):
        extension = filename.split('.')[-1]
        name = str(instance.document.name)+'_'+str(instance.created_at.strftime("%d-%m-%Y_%H-%M-%S"))
        return 'Announcements/Year-{}/{}.{}'.format(timezone.localtime().year, name, extension)


    info = models.TextField(null=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    document = models.FileField(null=True, upload_to=announcement_file_storage)
    officials_only = models.BooleanField(null=False, default=False)

    class Meta:
        ordering = ['-id']
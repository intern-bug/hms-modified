from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.utils import timezone
from institute.constants import FLOOR_OPTIONS
from security.models import OutingInOutTimes

# Create your models here.
class RoomDetail(models.Model):
    student = models.OneToOneField('institute.Student', on_delete=models.CASCADE, null=False)
    block = models.ForeignKey('institute.Block', on_delete=models.SET_NULL, null=True, blank=True)
    room_no = models.IntegerField(null=True, blank=True)
    floor = models.CharField(max_length=10, choices=list(map(lambda floor: (floor, floor), FLOOR_OPTIONS)), null=True, blank=True)

    def __str__(self):
        if self.floor and self.room_no:
            block = self.block_id
            if self.floor == 'Fourth':
                floor = self.floor[:2]
            else:
                floor = self.floor[0]
            return "{regd_no}<{block}: {floor}-{room}>".format(
                regd_no = self.student, 
                block = block,
                floor = floor,
                room = self.room_no
            )
        else:
            return "{}-".format(self.student)

    def clean(self):
        if self.block.roomdetail_set.exclude(pk=self.pk).filter(room_no=self.room_no, floor=self.floor).count() >= self.block.per_room_capacity():
            raise ValidationError("Room filled to maximum capacity.")
        
        if self.floor not in self.block.available_floors():
            raise ValidationError("Floor not available.")

        student = self.student
        block = self.block
        def valid_gender(student, block):
            return student.gender == block.gender
        
        def valid_year(student, block):
            return  ((student.year == 1 and block.room_type == '4S') or \
                    ((student.year == 2 or student.year == 3) and block.room_type == '2S') or \
                    (student.year == 4 and block.room_type == '1S'))

        if block and not valid_gender(student, block):
            raise ValidationError("{} Student cannot be placed in {} block!".format(student.gender, block.gender))
        if block and not valid_year(student, block):
            raise ValidationError("Year: {} Student cannot be placed in {} block!".format(student.year, block.room_type))
    
    def room(self):
        if self.floor and self.room_no:
            if self.floor == 'Fourth':
                floor = self.floor[:2]
            else:
                floor = self.floor[0]
            return "{}-{}".format(floor, self.room_no)
        else:
            return "-"

class Attendance(models.Model):
    OPTIONS = (
        ('Present','Present'),
        ('Absent','Absent')
    )
    student = models.OneToOneField('institute.Student', on_delete=models.CASCADE, null=False)
    present_dates = models.TextField(null=True, blank=True)
    absent_dates = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return str(self.student)

    def mark_attendance(self, date, status):
        if status == 'present':
            absent_dates = self.absent_dates and set(self.absent_dates.split(',')) or set()
            absent_dates.discard(date)
            self.absent_dates = ','.join(absent_dates)
            if not self.present_dates: 
                self.present_dates = date
            else:
                self.present_dates = ','.join(set(self.present_dates.split(',') + [date]))
        elif status == 'absent':
            present_dates = self.present_dates and set(self.present_dates.split(',')) or set()
            present_dates.discard(date)
            self.present_dates = ','.join(present_dates)
            if not self.absent_dates: 
                self.absent_dates = date
            else:
                self.absent_dates = ','.join(set(self.absent_dates.split(',') + [date]))
        if timezone.now().date() == timezone.datetime.strptime(date, "%Y-%m-%d").date():
                self.status = status.title()

        self.save()
        
class Outing(models.Model):
    PERMIT_OPTIONS = (
        ('Pending','Pending'),
        ('Processing','Processing'),
        ('Granted', 'Granted'),
        ('Rejected', 'Rejected'),
        ('Revoked', 'Revoked'),
        ('Pending Extension', 'Pending Extension'),
        ('Processing Extension', 'Processing Extension'),
        ('Extension Granted', 'Extension Granted'),
        ('Extension Rejected', 'Extension Rejected')
    )
    STATUS_OPTIONS=(('In Outing', 'In Outing'),('Closed', 'Closed'))
    OUTING_OPTIONS = (('Local','Local'),('Non-Local', 'Non-Local'),('Emergency', 'Emergency'))
    PARENT_CONSENT= (('Accepted','Accepted'),('Denied','Denied'))
    MESS_REBATE_OPTIONS = (('Enabled', 'Enabled'), ('Disabled', 'Disabled'))

    student = models.ForeignKey('institute.Student', on_delete=models.CASCADE, null=False)
    fromDate = models.DateTimeField(null=False)
    toDate = models.DateTimeField(null=False)
    purpose = models.CharField(max_length=255, null=False)
    permission = models.CharField(max_length=20, choices=PERMIT_OPTIONS, default='Pending', null=False)
    remark_by_caretaker = models.TextField(null=True)
    remark_by_warden = models.TextField(null=True)
    type = models.CharField(max_length=9, choices=OUTING_OPTIONS, null=False)
    parent_consent = models.CharField(max_length=8, choices=PARENT_CONSENT, default='NA', null=False)
    place_of_visit = models.CharField(max_length=255,null=False)
    status = models.CharField(max_length=9, choices=STATUS_OPTIONS, default='NA', null=False)
    mess_rebate = models.CharField(max_length=9, choices=MESS_REBATE_OPTIONS, default='Disabled', null=False)
    uuid = models.UUIDField(unique=True, null=True)


    def is_upcoming(self):
        if self.in_outing():
            return True
        elif self.permission != 'Rejected' and self.status != 'Closed' and self.permission != 'Revoked':
            if self.type == 'Local':
                if self.fromDate > timezone.now():
                    return True
                elif self.fromDate.date() == timezone.now().date() and self.toDate > timezone.now() and \
                    (timezone.now().hour*100+timezone.now().minute) <= 1400:
                    return True
                else:
                    return False
            elif self.type != 'Local':
                if self.toDate > timezone.now():
                    return True
                else:
                    return False
        else:
            return False

    # def is_editable(self):
    #     return self.is_upcoming() and self.permission == 'Pending'

    def is_extendable(self):
        return self.type != 'Local' and (self.permission == 'Granted' or self.permission=='Extension Granted' or self.permission=='Extension Rejected') and self.is_upcoming()

    def can_cancel(self):
        return self.is_upcoming() and not self.in_outing()
    
    def in_outing(self):
        return self.status == 'In Outing'

    def is_qr_viewable(self):
        not_viewable = ['Pending', 'Processing', 'Rejected', 'Revoked']
        viewable = ['Granted', 'Pending Extension', 'Processing Extension', 'Extension Granted']
        if self.in_outing():
            return True
        elif self.status == 'Closed':
            return False
        elif self.permission in viewable and self.fromDate <= timezone.now():
            return True
        elif self.permission in not_viewable:
            return False
        else:
            return False

    class Meta:
        ordering = ['-fromDate']
        managed = True

class ExtendOuting(models.Model):
    PERMIT_OPTIONS = (
        ('Pending Extension', 'Pending Extension'),
        ('Processing Extension', 'Processing Extension'),
        ('Extension Granted', 'Extension Granted'),
        ('Extension Rejected', 'Extension Rejected')
    )
    PARENT_CONSENT= (('Accepted','Accepted'),('Denied','Denied'))
    outing = models.ForeignKey('students.Outing', on_delete=models.CASCADE, null=False)
    fromDate = models.DateTimeField(null=False)
    toDate = models.DateTimeField(null=False)
    purpose = models.CharField(max_length=255, null=False)
    parent_consent = models.CharField(max_length=8, choices=PARENT_CONSENT, default='NA', null=False)
    permission = models.CharField(max_length=20, choices=PERMIT_OPTIONS, default='Pending Extension', null=False)
    place_of_visit = models.CharField(max_length=255,null=False)
    class Meta:
        managed = True 

class Document(models.Model):
    student = models.OneToOneField('institute.Student', on_delete=models.CASCADE, null=False)
    application = models.FileField(null=True, blank=True)
    undertaking_form = models.FileField(null=True, blank=True)
    receipt = models.FileField(null=True, blank=True)
    day_scholar_affidavit = models.FileField(null=True, blank=True)
    aadhar_card = models.FileField(null=True, blank=True)

    def __str__(self) -> str:
        return 'Document: {} - {}'.format(self.id, self.student.regd_no)

class FeeDetail(models.Model):
    student = models.OneToOneField('institute.Student', on_delete=models.CASCADE, null=False)
    has_paid = models.BooleanField(null=True, default=False)
    amount_paid = models.FloatField(null=True, blank=True,default=0)
    bank = models.CharField(max_length=100,null=True, blank=True)
    challan_no = models.CharField(max_length=64,null=True, blank=True)
    dop = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return 'Bank Detail: {} - {}'.format(self.id, self.student.regd_no)

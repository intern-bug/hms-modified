from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from institute.constants import FLOOR_OPTIONS
from institute.validators import numeric_only

# Create your models here.
class RoomDetail(models.Model):
    student = models.OneToOneField('institute.Student', on_delete=models.CASCADE, null=False)
    block = models.ForeignKey('institute.Block', on_delete=models.SET_NULL, null=True, blank=True)
    room_no = models.IntegerField(null=True, blank=True)
    floor = models.CharField(max_length=10, choices=list(map(lambda floor: (floor, floor), FLOOR_OPTIONS)), null=True, blank=True)
    bed = models.IntegerField(null=True, blank=True)
    allotted_on = models.DateField(auto_now=True)

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
            return  ((student.year == 1 and block.room_type in ['4S', '2S', '1S']) or \
                    ((student.year == 2 or student.year == 3) and block.room_type == '2S') or \
                    (student.year == 4 and block.room_type == '1S'))

        if block and not valid_gender(student, block):
            raise ValidationError("{} Student cannot be placed in {} block!".format(student.gender, block.gender))
        if block and not valid_year(student, block):
            raise ValidationError("Year: {} Student cannot be placed in {} block!".format(student.year, block.room_type))
    
    def room(self):
        if self.floor and self.room_no:
            if self.floor == 'Fourth':
                floor = 'FT'
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
            absent_dates = self.absent_dates and self.absent_dates.split(',') or None
            if absent_dates:
                absent_dates_formatted = [absent_date.split('@')[0] for absent_date in absent_dates]
                if date in absent_dates_formatted:
                    absent_dates.pop(absent_dates_formatted.index(date))
            if absent_dates:
                absent_dates = set(absent_dates)
            else:
                absent_dates = set()
            self.absent_dates = ','.join(absent_dates)
            if not self.present_dates: 
                self.present_dates = str(date)+"@"+str(timezone.now().strftime('%d-%m-%Y %H:%M:%S'))
            else:
                present_dates_formatted = self.present_dates.split(',')
                present_dates_formatted = [present_date.split('@')[0] for present_date in present_dates_formatted]
                if date not in present_dates_formatted:
                    date_formatted = str(date)+"@"+str(timezone.now().strftime('%d-%m-%Y %H:%M:%S'))
                    self.present_dates = ','.join(set(self.present_dates.split(',') + [date_formatted]))
        elif status == 'absent':
            present_dates = self.present_dates and self.present_dates.split(',') or None
            if present_dates:
                present_dates_formatted = [present_date.split('@')[0] for present_date in present_dates]
                if date in present_dates_formatted:
                    present_dates.pop(present_dates_formatted.index(date))
            if present_dates:
                present_dates = set(present_dates)
            else:
                present_dates = set()
            self.present_dates = ','.join(present_dates)
            if not self.absent_dates: 
                self.absent_dates = str(date)+"@"+str(timezone.now().strftime('%d-%m-%Y %H:%M:%S'))
            else:
                absent_dates_formatted = self.absent_dates.split(',')
                absent_dates_formatted = [absent_date.split('@')[0] for absent_date in absent_dates_formatted]
                if date not in absent_dates_formatted:
                    date_formatted = str(date)+"@"+str(timezone.now().strftime('%d-%m-%Y %H:%M:%S'))
                    self.absent_dates = ','.join(set(self.absent_dates.split(',') + [date_formatted]))
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
    OUTING_OPTIONS = (('Local','Local'),('Non-Local', 'Non-Local'),('Emergency', 'Emergency'), ('Vacation', 'Vacation'))
    PARENT_CONSENT= (('Accepted','Accepted'),('Denied','Denied'))
    MESS_REBATE_OPTIONS = (('Enabled', 'Enabled'), ('Disabled', 'Disabled'))
    MESS_REBATE_STATUS_OPTIONS = (('Processed', 'Processed'), ('Rejected', 'Rejected'))

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
    mode_of_journey_from = models.CharField(max_length=10, default='NA')
    mode_of_journey_to = models.CharField(max_length=10, default='NA')
    emergency_contact = models.CharField(max_length=10, validators=[numeric_only], default=0)
    emergency_medical_issue = models.ForeignKey('complaints.MedicalIssue', on_delete=models.CASCADE, null=True, blank=True)
    mess_rebate = models.CharField(max_length=9, choices=MESS_REBATE_OPTIONS, default='Disabled', null=False)
    mess_rebate_status = models.CharField(max_length=9, choices=MESS_REBATE_STATUS_OPTIONS, default='NA', null=False)
    mess_rebate_days = models.IntegerField(null=False, default=0)
    mess_rebate_remarks = models.TextField(null=True, blank=True)
    uuid = models.UUIDField(unique=True, null=True)


    def is_upcoming(self):
        if self.in_outing() or (self.type=='Vacation' and self.permission!='Rejected' and self.status!='Closed'):
            return True
        elif self.permission != 'Rejected' and self.status != 'Closed' and self.permission != 'Revoked':
            if self.type == 'Local':
                if self.fromDate > timezone.now():
                    return True
                elif self.fromDate.date() == timezone.now().date() and self.toDate > timezone.now() and \
                    (timezone.now().hour*100+timezone.now().minute) <= 1430:
                    return True
                else:
                    if self.student.year == 1 or self.student.gender == 'Female':
                        return False
                    else:
                        return True
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
        return self.type not in ['Local', 'Vacation'] and (self.permission == 'Granted' or self.permission=='Extension Granted' or self.permission=='Extension Rejected') and self.is_upcoming()

    def can_cancel(self):
        return self.is_upcoming() and self.type!='Vacation' and not self.in_outing()
    
    def in_outing(self):
        return self.status == 'In Outing'

    def is_qr_viewable(self):
        not_viewable = ['Pending', 'Processing', 'Rejected', 'Revoked']
        viewable = ['Granted', 'Pending Extension', 'Processing Extension', 'Extension Granted']
        if self.in_outing():
            return True
        elif self.status == 'Closed':
            return False
        elif self.permission in viewable: # and self.fromDate <= timezone.now():
            return True
        elif self.permission in not_viewable:
            return False
        else:
            return False

    def mess_rebate_action_status(self):
        return self.mess_rebate=='Enabled' and self.mess_rebate_status=='NA'
    
    def save(self, *args, **kwargs):
        import uuid
        if self.student.gender == 'Male' and self.student.year != 1:
            if not self.id: 
                self.permission = 'Granted'
                self.uuid = uuid.uuid4()
            days = (self.toDate.date()-self.fromDate.date()).days-1
            if days >= 4:
                self.mess_rebate = 'Enabled'
        super(Outing, self).save(*args, **kwargs)

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
    mode_of_journey_from = models.CharField(max_length=10)
    mode_of_journey_to = models.CharField(max_length=10)
    emergency_contact = models.CharField(max_length=10, validators=[numeric_only])
    emergency_medical_issue = models.ForeignKey('complaints.MedicalIssue', on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.outing.student.gender == 'Male':
            outing = self.outing
            outing.permission = 'Extension Granted'
            prev_fromDate = outing.fromDate
            prev_toDate = outing.toDate
            prev_place_of_visit = outing.place_of_visit
            prev_purpose = outing.purpose
            prev_mode_of_journey_from = outing.mode_of_journey_from
            prev_mode_of_journey_to = outing.mode_of_journey_to
            prev_emergency_contact = outing.emergency_contact
            prev_emergency_missue = outing.emergency_medical_issue
            outing.fromDate = self.fromDate
            outing.toDate = self.toDate
            outing.place_of_visit = self.place_of_visit
            outing.purpose = self.purpose
            self.fromDate = prev_fromDate
            self.toDate = prev_toDate
            self.place_of_visit = prev_place_of_visit
            self.purpose = prev_purpose
            self.mode_of_journey_from = prev_mode_of_journey_from
            self.mode_of_journey_to = prev_mode_of_journey_to
            self.emergency_contact = prev_emergency_contact
            self.emergency_medical_issue = prev_emergency_missue
            self.permission = 'Extension Granted'
            outing.save()
        super(ExtendOuting, self).save(*args, **kwargs)

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
    room_detail = models.ForeignKey('students.RoomDetail', on_delete=models.CASCADE, null=False)
    has_paid = models.BooleanField(null=True, default=False)
    amount_paid = models.FloatField(null=True, blank=True,default=0)
    # bank = models.CharField(max_length=100,null=True, blank=True)
    # challan_no = models.CharField(max_length=64,null=True, blank=True)
    dop = models.DateField(null=True, blank=True)
    mode_of_payment = models.CharField(null=True, blank=True, max_length=255)

    def __str__(self) -> str:
        return 'Bank Detail: {} - {}'.format(self.id, self.student.regd_no)

class Vacation(models.Model):

    STATUS_OPTIONS = (('Functioning', 'Functioning'),('Defective', 'Defective'))

    room_detail = models.OneToOneField('students.RoomDetail', on_delete=models.CASCADE, null=False)
    vacated_on = models.DateTimeField(null=False, blank=False)
    mode_of_journey = models.CharField(max_length=255, null=False, blank=False)
    journey_destination = models.CharField(max_length=255, null=False, blank=False)
    iron_cot_status = models.CharField(max_length=11, choices=STATUS_OPTIONS, null=False)
    tube_light_status = models.CharField(max_length=11, choices=STATUS_OPTIONS, null=False)
    fan_status = models.CharField(max_length=11, choices=STATUS_OPTIONS, null=False)
    fan_regulator_status = models.CharField(max_length=11, choices=STATUS_OPTIONS, null=False)
    cupboards_status = models.CharField(max_length=11, choices=STATUS_OPTIONS, null=False)
    switches_status = models.CharField(max_length=11, choices=STATUS_OPTIONS, null=False)
    amperes_socket_15_status = models.CharField(max_length=11, choices=STATUS_OPTIONS, null=False)
    iron_cot_remarks = models.CharField(max_length=255, null=True, blank=True)
    tube_light_remarks = models.CharField(max_length=255, null=True, blank=True)
    fan_remarks = models.CharField(max_length=255, null=True, blank=True)
    fan_regulator_remarks = models.CharField(max_length=255, null=True, blank=True)
    cupboards_remarks = models.CharField(max_length=255, null=True, blank=True)
    switches_remarks = models.CharField(max_length=255, null=True, blank=True)
    amperes_socket_15_remarks = models.CharField(max_length=255, null=True, blank=True)
    submitted = models.BooleanField(default=False)
    vacation_outing_obj = models.OneToOneField('students.Outing', on_delete=models.SET_NULL, null=True)

from cProfile import label
from django import forms
from institute.models import Announcements, Student
from students.models import Vacation
from workers.models import Worker
from django.utils import timezone

class StudentForm(forms.ModelForm):
    COMMUNITY_CHOICES = (
        ( None, 'Select'),
        ('GEN', 'GEN'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('EWS', 'EWS')
    )

    BLOOD_GROUP_CHOICES = (
        ( None, 'Select'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    )

    blood_group = forms.CharField(max_length=25, required=False, widget=forms.Select(choices=BLOOD_GROUP_CHOICES))
    father_name = forms.CharField(max_length=100, required=False)
    mother_name = forms.CharField(max_length=100, required=False)
    community = forms.CharField(max_length=25, required=False, widget=forms.Select(choices=COMMUNITY_CHOICES),)

    class Meta:
        model = Student
        exclude = ['outing_rating', 'discipline_rating']

        BRANCH_CHOICES=(
            ( None,'Select'),
            ('BIO','Biotechnology'),
            ('CHE','Chemical Engineering'),
            ('CIV','Civil Engineering'),
            ('CSE','Computer Science and Engineering'),
            ('EEE','Electrical and Electronics Engineering'),
            ('ECE','Electronics and Communication Engineering'),
            ('MEC','Mechanical Engineering'),
            ('MME','Metallurgical and Materials Engineering'),
        )

        BOOLEAN_CHOICES = (
            (True, 'Yes'), 
            (False, 'No')
        )

        widgets = {
            'branch': forms.Select(choices=BRANCH_CHOICES),
            'pwd': forms.Select(choices=BOOLEAN_CHOICES),
            'is_hosteller': forms.Select(choices=BOOLEAN_CHOICES),
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 5}),
        }

        labels = {
            'pwd': 'Person with Disability',
            'regd_no': 'Registration No.',
            'is_hosteller': 'Hosteller',
            'dob': 'Date of Birth',
        }

        help_texts = {
            'is_hosteller': 'Yes for Hosteller. No for Day Scholar.',
        }

class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['staff_id', 'name', 'designation', 'account_email', 'email', 'phone', 'gender', 'block']

        DESGINATION_CHOICES = (
            (None, 'Select'),
            ('Doctor', 'Doctor'),
            ('Electrician','Electrician'), 
            ('Estate Staff','Estate Staff'), 
            ('General Servant','General Servant'),
            ('Gym Trainer','Gym Trainer'),
            ('Mess Incharge', 'Mess Incharge'),
            ('PT/Games Coach','PT/Games Coach'),
            ('Scavenger','Scavenger'),
        )

        widgets = {
            'designation': forms.Select(choices=DESGINATION_CHOICES)
        }

class VacationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(VacationForm, self).__init__(*args, **kwargs)
        fields_keyOrder = [
            'vacated_on', 'mode_of_journey', 'journey_destination', 
            'iron_cot_status', 'iron_cot_remarks',
            'tube_light_status', 'tube_light_remarks',
            'fan_status', 'fan_remarks',
            'fan_regulator_status', 'fan_regulator_remarks',
            'cupboards_status', 'cupboards_remarks',
            'switches_status', 'switches_remarks',
            'amperes_socket_15_status', 'amperes_socket_15_remarks'
        ]
        self.fields['vacated_on'].initial = self.instance.vacated_on
        self.fields = {key:self.fields[key] for key in fields_keyOrder}
    class Meta:
        model = Vacation
        fields = '__all__'
        exclude = ['room_detail']
        labels = {
            'vacated_on': 'Vacation Date',
            'mode_of_journey': 'Mode of Journey',
            'journey_destination': 'Journey to',
            'iron_cot_status': 'Iron-cot',
            'tube_light_status': 'Tube Light',
            'fan_status': 'Fan',
            'fan_regulator_status': 'Fan regulator',
            'cupboards_status': 'Cupboards',
            'switches_status': 'Switches',
            'amperes_socket_15_status': 'Socket',
            'amperes_socket_15_remarks': 'Socket Remarks'
        }
    
    def clean_vacated_on(self):
        vacated_on = self.cleaned_data.get('vacated_on')
        if vacated_on <= timezone.now():
            raise forms.ValidationError("Date should be later than the moment!")
        return vacated_on

class AnnouncementCreationForm(forms.ModelForm):
    class Meta:
        model = Announcements
        fields = ['info', 'document', 'officials_only']

        labels = {
            'info': 'About',
            'document': 'Upload related document',
            'officials_only': 'Officials',
        }

        widgets = {
            'info': forms.Textarea(attrs={'rows':4})
        }
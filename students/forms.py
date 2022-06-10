from django import forms
from django.utils import timezone
from .models import Outing
from django_auth.models import User
from institute.models import Student
from django.db.models import Q

class OutingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs.keys():
            self.request = kwargs.pop('request')
        super(OutingForm, self).__init__(*args, **kwargs)
    class Meta:
        model = Outing
        fields = ['type', 'fromDate', 'toDate', 'place_of_visit', 'purpose']

        labels = {
            'type': 'Outing Mode',
            'fromDate': 'From Date & Time',
            'toDate': 'To Date & Time',
            'place_of_visit': 'Place of Visit',
        }
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('fromDate')
        to_date = cleaned_data.get('toDate')
        type = cleaned_data.get('type')
        user = User.objects.get(email=self.request.user)
        student = Student.objects.get(user_id=user.id)
        outings = Outing.objects.filter(~Q(permission='Revoked'),student_id=student.id)
        if from_date and to_date and (from_date >= to_date):
            raise forms.ValidationError("To Date and Time should be later than From Date and Time")
        if type == 'Local' and from_date and to_date and from_date.date() != to_date.date():
            raise forms.ValidationError("From date and To date should be same for local outing")
        for out in outings:
            out_from_date = out.fromDate.date()
            out_to_date = out.toDate.date()
            if from_date and to_date and out_from_date <= from_date.date() <= out_to_date and (from_date > out.fromDate or to_date > out.toDate):
                raise forms.ValidationError("You already have an outing request in process for the same time period")
        return cleaned_data

    def clean_fromDate(self):
        from_date = self.cleaned_data.get('fromDate')
        type = self.cleaned_data.get('type')
        if from_date <= timezone.now():
            raise forms.ValidationError("From Date should be later than the moment!")
        from_time = (from_date.hour*100)+from_date.minute
        if type == 'Local' and from_time < 700:
            raise forms.ValidationError("Local Outing is allowed only after 06:30 hrs")
        if type != 'Emergency' and from_date.date() == timezone.now().date() and (timezone.now().hour*100 + timezone.now().minute) >= 1030:
            raise forms.ValidationError("Can't apply for outing for the current day after 16:00 hrs")
        return from_date
    
    def clean_toDate(self):
        type = self.cleaned_data.get('type')
        to_date = self.cleaned_data.get('toDate')
        user = User.objects.get(email=self.request.user)
        to_time = (to_date.hour*100)+to_date.minute
        if type == 'Local':
            student = Student.objects.get(user_id=user.id)
            gender = student.gender
            if gender == 'Male' and to_time > 2100:
                raise forms.ValidationError("Local Outing is allowed only until 21:00 hrs")
            elif gender == 'Female' and to_time > 2030:
                raise forms.ValidationError("Local Outing is allowed only until 20:30 hrs")
        return to_date
    
    

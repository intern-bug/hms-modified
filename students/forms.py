from django import forms
from django.utils import timezone
from .models import ExtendOuting, Outing
from django_auth.models import User
from institute.models import Student
from django.db.models import Q
from institute.validators import numeric_only
from complaints.models import MedicalIssue


class OutingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs.keys():
                self.request = kwargs.pop('request')
        if self.request.user.student.year==1:
            
            super(OutingForm, self).__init__(*args, **kwargs)
            self.fields['type'] = forms.ChoiceField(choices=[('','-----------'), ('Local','Local'), ('Non-Local', 'Non-Local'), ('Emergency', 'Emergency')])
            self.fields['emergency_medical_issue'] = forms.CharField(label='Medical Issue Id', validators=[numeric_only], widget=forms.TextInput(attrs={'size':5}))
            self.fields['emergency_medical_issue'].required = False
            # self.fields['initial'] = 0
        else:
            # if 'request' in kwargs.keys():
            #     self.request = kwargs.pop('request')
            super(OutingForm, self).__init__(*args, **kwargs)
            OUTING_CHOICES = [('','-----------'), ('Local','Local'), ('Non-Local', 'Non-Local'), ('Emergency', 'Emergency')]
            if self.request.user.student.gender == 'Male':
                OUTING_CHOICES = [('','-----------'), ('Local','Local'), ('Non-Local', 'Non-Local')]
            self.fields['type'] = forms.ChoiceField(choices=OUTING_CHOICES)
            if self.request.user.student.gender == 'Female':
                self.fields['emergency_medical_issue'] = forms.CharField(label='Medical Issue Id', validators=[numeric_only], widget=forms.TextInput(attrs={'size':5}))
                self.fields['emergency_medical_issue'].required = False
            else:
                self.fields.pop('emergency_medical_issue')
            # self.fields['initial'] = 0
    class Meta:
        model = Outing
        fields = ['type', 'fromDate', 'mode_of_journey_from', 'toDate', 'mode_of_journey_to', 'place_of_visit', 'purpose', 'emergency_medical_issue', 'emergency_contact']

        labels = {
            'type': 'Outing Mode',
            'fromDate': 'From Date & Time',
            'toDate': 'To Date & Time',
            'place_of_visit': 'Place of Visit',
            'mode_of_journey_from': 'Mode of Journey From College',
            'mode_of_journey_to': 'Mode of Journey To College',
            'emergency_contact': 'Emergency Conatct Number',
            'emergency_medical_issue': 'Medical Issue Id',
        }
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('fromDate')
        to_date = cleaned_data.get('toDate')
        type = cleaned_data.get('type')
        user = User.objects.get(email=self.request.user)
        student = Student.objects.get(user_id=user.id)
        outings = Outing.objects.filter(~Q(permission__in=['Revoked', 'Rejected']),student_id=student.id).exclude(status='Closed')
        if from_date and to_date and (from_date >= to_date):
            raise forms.ValidationError("To Date and Time should be later than From Date and Time")
        if type == 'Local' and from_date and to_date and from_date.date() != to_date.date():
            raise forms.ValidationError("From date and To date should be same for local outing")
        for out in outings:
            if (out.type == 'Vacation' and to_date and to_date >= out.fromDate) or self.instance!=None and out.id != self.instance.id and from_date and to_date and out.fromDate <= from_date <= out.toDate:
                raise forms.ValidationError("You already have an outing request in process for the same time period")    
        return cleaned_data

    def clean_fromDate(self):
        if self.request.user.student.year==1:
            from_date = self.cleaned_data.get('fromDate')
            type = self.cleaned_data.get('type')
            if from_date <= timezone.now():
                raise forms.ValidationError("From Date should be later than the moment!")
            from_time = (from_date.hour*100)+from_date.minute
            if type == 'Local' and from_time < 630:
                raise forms.ValidationError("Local Outing is allowed only after 06:30 hrs")
            if type == 'Local' and from_time > 1930:
                raise forms.ValidationError("Local Outing from_time should not be after 19:30 hrs")
            if type == 'Local' and from_date.date() == timezone.now().date() and (timezone.now().hour*100 + timezone.now().minute) >= 1400:
                raise forms.ValidationError("Can't apply for local outing for the current day after 19:30 hrs")
            elif type == 'Non-Local' and from_date.date() == timezone.now().date() and (timezone.now().hour*100 + timezone.now().minute) >= 1130:
                raise forms.ValidationError("Can't apply for non-local outing for the current day after 17:00 hrs")

            return from_date
        else:
            from_date = self.cleaned_data.get('fromDate')
            type = self.cleaned_data.get('type')
            if from_date <= timezone.now():
                raise forms.ValidationError("From Date should be later than the moment!")
            from_time = (from_date.hour*100)+from_date.minute
            if self.request.user.student.gender == 'Female': 
                if type == 'Local' and from_time < 630:
                    raise forms.ValidationError("Local Outing is allowed only after 06:30 hrs")
                if type == 'Local' and from_time > 1930:
                    raise forms.ValidationError("Local Outing from_time should not be after 19:30 hrs")
                if type == 'Local' and from_date.date() == timezone.now().date() and (timezone.now().hour*100 + timezone.now().minute) >= 1400:
                    raise forms.ValidationError("Can't apply for local outing for the current day after 19:30 hrs")
                elif type == 'Non-Local' and from_date.date() == timezone.now().date() and (timezone.now().hour*100 + timezone.now().minute) >= 1130:
                    raise forms.ValidationError("Can't apply for non-local outing for the current day after 17:00 hrs")

            return from_date
    
    def clean_toDate(self):
        if self.request.user.student.year==1:
            type = self.cleaned_data.get('type')
            to_date = self.cleaned_data.get('toDate')
            user = User.objects.get(email=self.request.user)
            to_time = (to_date.hour*100)+to_date.minute
            if type == 'Local':
                student = Student.objects.get(user_id=user.id)
                gender = student.gender
                if gender == 'Male' and to_time > 2100:
                    raise forms.ValidationError("Local Outing is allowed only until 21:00 hrs")
                elif gender == 'Female' and to_time > 2100:
                    raise forms.ValidationError("Local Outing is allowed only until 21:00 hrs")
            return to_date
        else:
            type = self.cleaned_data.get('type')
            to_date = self.cleaned_data.get('toDate')
            user = User.objects.get(email=self.request.user)
            to_time = (to_date.hour*100)+to_date.minute
            if type == 'Local':
                student = Student.objects.get(user_id=user.id)
                gender = student.gender
                # if gender == 'Male' and to_time > 2100:
                #     raise forms.ValidationError("Local Outing is allowed only until 21:00 hrs")
                if gender == 'Female' and to_time > 2130:
                    raise forms.ValidationError("Local Outing is allowed only until 21:30 hrs")
            return to_date

    def clean_emergency_medical_issue(self):
        type = self.cleaned_data.get('type')
        missue_id = self.cleaned_data.get('emergency_medical_issue')
        if missue_id:
            missue_object = MedicalIssue.objects.filter(id=missue_id).first()
            if not missue_object:
                raise forms.ValidationError("Inavlid Medical Issue Id")
            if missue_object.user != self.request.user:
                raise forms.ValidationError("Invalid Medical Issue Id")
            return missue_object

class OutingExtendForm(forms.ModelForm):
    def __init__(self, initial=None, *args, **kwargs):
        if 'request' in kwargs.keys():
                self.request = kwargs.pop('request')
                self.outing = kwargs.pop('object')
        if self.request.user.student.year==1:
            super(OutingExtendForm, self).__init__(*args, **kwargs)
            self.fields['type'] = forms.CharField(label='Mode of Outing', widget=forms.Select(choices=Outing.OUTING_OPTIONS))
            self.fields['type'].initial = self.outing.type
            self.fields['type'].disabled = True
            self.fields['fromDate'].initial = self.outing.fromDate
            self.fields['mode_of_journey_from'].initial = self.outing.mode_of_journey_from
            if self.outing.status == 'In Outing':
                self.fields['fromDate'].disabled = True
                self.fields['mode_of_journey_from'].disabled = True
            self.fields['toDate'].initial = self.outing.toDate
            self.fields['mode_of_journey_to'].initial = self.outing.mode_of_journey_to
            self.fields['place_of_visit'] = forms.CharField(label='Place of Visit', initial=self.outing.place_of_visit)
            self.fields['purpose'] = forms.CharField(label='Purpose', initial=self.outing.purpose)
            self.fields['emergency_contact'].initial = self.outing.emergency_contact
            self.fields['emergency_medical_issue'] = forms.CharField(label='Medical Issue Id', validators=[numeric_only], widget=forms.TextInput(attrs={'size':5}))
            self.fields['emergency_medical_issue'].required = False
            if self.outing.emergency_medical_issue:
                self.fields['emergency_medical_issue'].initial = self.outing.emergency_medical_issue.id
            fields_keyOrder = ['type', 'fromDate', 'mode_of_journey_from', 'toDate', 'mode_of_journey_to', 'place_of_visit', 'purpose', 'emergency_medical_issue', 'emergency_contact']
            self.fields = {key:self.fields[key] for key in fields_keyOrder}
        else:
            from datetime import datetime
            from django.utils import timezone
            # if 'request' in kwargs.keys():
            #     self.request = kwargs.pop('request')
            #     self.outing = kwargs.pop('object')
            super(OutingExtendForm, self).__init__(*args, **kwargs)
            self.fields['type'] = forms.CharField(label='Mode of Outing', widget=forms.Select(choices=Outing.OUTING_OPTIONS))
            self.fields['type'].initial = self.outing.type
            self.fields['type'].disabled = True
            if self.outing.fromDate > timezone.now() or self.outing.status == 'In Outing':
                self.fields['fromDate'].initial = self.outing.fromDate
            self.fields['mode_of_journey_from'].initial = self.outing.mode_of_journey_from
            if self.outing.status == 'In Outing':
                self.fields['fromDate'].disabled = True
                self.fields['mode_of_journey_from'].disabled = True
            self.fields['toDate'].initial = self.outing.toDate
            self.fields['mode_of_journey_to'].initial = self.outing.mode_of_journey_to
            self.fields['place_of_visit'] = forms.CharField(label='Place of Visit', initial=self.outing.place_of_visit)
            self.fields['purpose'] = forms.CharField(label='Purpose', initial=self.outing.purpose)
            self.fields['emergency_contact'].initial = self.outing.emergency_contact
            if self.request.user.student.gender == 'Female':
                self.fields['emergency_medical_issue'] = forms.CharField(label='Medical Issue Id', validators=[numeric_only], widget=forms.TextInput(attrs={'size':5}))
                self.fields['emergency_medical_issue'].required = False
                if self.outing.emergency_medical_issue:
                    self.fields['emergency_medical_issue'].initial = self.outing.emergency_medical_issue.id
                fields_keyOrder = ['type', 'fromDate', 'mode_of_journey_from', 'toDate', 'mode_of_journey_to', 'place_of_visit', 'purpose', 'emergency_medical_issue', 'emergency_contact']
            else:
                fields_keyOrder = ['type', 'fromDate', 'mode_of_journey_from', 'toDate', 'mode_of_journey_to', 'place_of_visit', 'purpose', 'emergency_contact']
                self.fields.pop('emergency_medical_issue')
            self.fields = {key:self.fields[key] for key in fields_keyOrder}
        
    class Meta:
        model = ExtendOuting
        fields = ['fromDate', 'mode_of_journey_from', 'toDate', 'mode_of_journey_to', 'place_of_visit', 'purpose', 'emergency_medical_issue', 'emergency_contact']

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('fromDate')
        to_date = cleaned_data.get('toDate')
        place_of_visit = cleaned_data.get('place_of_visit')
        purpose = cleaned_data.get('purpose')
        user = User.objects.get(email=self.request.user)
        student = Student.objects.get(user_id=user.id)
        outings = Outing.objects.filter(~Q(permission__in=['Revoked', 'Rejected']),student_id=student.id).exclude(status='Closed')

        if from_date and to_date and (from_date >= to_date):
            raise forms.ValidationError("To Date and Time should be later than From Date and Time")
        if to_date == self.outing.toDate and place_of_visit==self.outing.place_of_visit and purpose==self.outing.purpose:
            raise forms.ValidationError("There should be a change in timings to apply for outing extension.") 
        for out in outings:
            if self.outing != None and self.outing.id != out.id:
                if from_date and to_date and out.fromDate <= from_date <= out.toDate:
                    raise forms.ValidationError("You already have an outing request in process for the same time period")
        return cleaned_data

    def clean_fromDate(self):
        if self.request.user.student.year==1:
            from_date = self.cleaned_data.get('fromDate')
            type = self.cleaned_data.get('type')
            if from_date <= timezone.now():
                if from_date != self.outing.fromDate:
                    raise forms.ValidationError("From Date should be later than the moment!")
            if type != 'Emergency' and from_date.date() == timezone.now().date() and (timezone.now().hour*100 + timezone.now().minute) >= 1030:
                raise forms.ValidationError("Can't apply for outing for the current day after 16:00 hrs")
            return from_date
        else:
            from_date = self.cleaned_data.get('fromDate')
            type = self.cleaned_data.get('type')
            if from_date <= timezone.now():
                if self.outing.status != 'In Outing':
                    raise forms.ValidationError("From Date should be later than the moment!")
            if self.request.user.student.gender == 'Female' and  type != 'Emergency' and from_date.date() == timezone.now().date() and (timezone.now().hour*100 + timezone.now().minute) >= 1130:
                raise forms.ValidationError("Can't apply for extension of outing for the current day after 17:00 hrs")
            return from_date
    
    def clean_toDate(self):
        to_date = self.cleaned_data.get('toDate')
        return to_date

    def clean_emergency_medical_issue(self):
        type = self.cleaned_data.get('type')
        missue_id = self.cleaned_data.get('emergency_medical_issue')
        if missue_id:
            missue_object = MedicalIssue.objects.filter(id=missue_id).first()
            if not missue_object:
                raise forms.ValidationError("Invalid Medical Issue Id")
            if missue_object.user != self.request.user:
                raise forms.ValidationError("Invalid Medical Issue Id")
            return missue_object

    
    

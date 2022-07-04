from django import forms
from institute.models import Student
from .models import Complaint, MedicalIssue

class ComplaintCreationForm(forms.ModelForm):
    complainee_id = forms.IntegerField(required=False, help_text='Only for Indisciplinary, Discrimination/Harassment or Damage to property complaints.')
    class Meta:
        model = Complaint
        fields = ['type', 'complainee_id', 'summary', 'detailed', 'file']

        TYPE = (
            ('General','General'),
            ('Food Issues', 'Food Issues'),
            ('Electrical','Electrical'),
            ('Civil', 'Civil'),
            ('Room Cleaning','Room Cleaning'),
            ('Restroom Cleaning','Restroom Cleaning'),
            ('Network Issue', 'Network Issue'),
            ('Indisciplinary','Indisciplinary'),
            ('Discrimination/ Harassment','Discrimination/ Harassment'),
            ('Damage to property','Damage to property')
        )

        labels = {
            'detailed': 'Details',
            'file': 'Upload related document'
        }
        
        widgets = {
            'detailed': forms.Textarea(attrs={'rows': 4}),
            'type': forms.Select(choices=TYPE)
        }

    def clean_complainee_id(self):
        complainee_id = self.cleaned_data.get('complainee_id')
        if complainee_id and not Student.objects.filter(regd_no=complainee_id).exists():
            raise forms.ValidationError("Invalid registration number.")
        return complainee_id

    def clean(self):
        cleaned_data = super().clean()
        type = cleaned_data.get('type')
        complainee_id = cleaned_data.get('complainee_id')

        if (type == 'Indisciplinary' or type == 'Discrimination/ Harassment' or type == 'Damage to property') and not complainee_id:
            raise forms.ValidationError("Please specify the registration no. of the person against whom the complaint has to be registered.")
        elif not (type == 'Indisciplinary' or type == 'Discrimination/ Harassment' or type == 'Damage to property') and complainee_id:
            raise forms.ValidationError("Cannot assign complainee to {} complaint.".format(type))
        
        return cleaned_data

class ComplaintUpdationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs.keys():
            self.request = kwargs.pop('request')
        super(ComplaintUpdationForm, self).__init__(*args, **kwargs)
        if 'request' in self.__dict__.keys() and self.request.user.is_official and self.request.user.official.is_caretaker():
            self.fields['status'] = forms.ChoiceField(choices = [('Registered', 'Registered'), ('Processing', 'Processing')])
        if 'request' in self.__dict__.keys() and self.request.user.is_official and self.request.user.official.is_warden():
            self.fields['status'] = forms.ChoiceField(choices = [('Processing', 'Processing'), ('Resolved', 'Resolved')])
    class Meta:
        model = Complaint
        fields = ['status', 'remark', ]

        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4})
        }

class MedicalIssueUpdationForm(forms.ModelForm):
    class Meta:
        model = MedicalIssue
        fields = ['status', 'emergency_outing_permission', 'remark', ]

        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4})
        }
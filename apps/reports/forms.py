from django import forms
from .models import ReportTemplate, ReportSchedule, GeneratedReport, ReportPermission


class ReportTemplateForm(forms.ModelForm):
    """Report template form"""
    class Meta:
        model = ReportTemplate
        fields = ['name', 'report_type', 'description', 'template_file', 'html_template', 'css_styles', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'html_template': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Enter HTML template code...'}),
            'css_styles': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter CSS styles...'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        template_file = cleaned_data.get('template_file')
        html_template = cleaned_data.get('html_template')
        
        if not template_file and not html_template:
            raise forms.ValidationError("Please provide either a template file or HTML template")
        
        return cleaned_data


class ReportScheduleForm(forms.ModelForm):
    """Report schedule form"""
    class Meta:
        model = ReportSchedule
        fields = ['template', 'name', 'frequency', 'parameters', 'recipients', 'is_active']
        widgets = {
            'parameters': forms.Textarea(attrs={'rows': 5, 'placeholder': '{"key": "value", ...}'}),
            'recipients': forms.Textarea(attrs={'rows': 3, 'placeholder': 'email1@example.com\nemail2@example.com'}),
        }
    
    def clean_recipients(self):
        recipients = self.cleaned_data.get('recipients')
        if recipients:
            if isinstance(recipients, str):
                # Split by newline or comma
                emails = [email.strip() for email in recipients.replace(',', '\n').split('\n') if email.strip()]
                # Validate email format
                from django.core.validators import validate_email
                for email in emails:
                    try:
                        validate_email(email)
                    except forms.ValidationError:
                        raise forms.ValidationError(f"Invalid email address: {email}")
                return emails
        return recipients
    
    def clean_parameters(self):
        parameters = self.cleaned_data.get('parameters')
        if parameters:
            try:
                import json
                json.loads(parameters)
            except json.JSONDecodeError:
                raise forms.ValidationError("Parameters must be valid JSON")
        return parameters


class ReportGenerationForm(forms.Form):
    """Report generation form"""
    report_type = forms.ChoiceField(choices=[])
    exam_session = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Exam Session"
    )
    allocation = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Allocation"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    venue = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Venue"
    )
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Department"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set report type choices
        from .models import ReportTemplate
        self.fields['report_type'].choices = ReportTemplate.REPORT_TYPES
        
        # Set querysets
        from apps.exams.models import ExamSession
        from apps.allocation.models import ExamAllocation
        from apps.venues.models import Venue
        from apps.academics.models import Department
        
        self.fields['exam_session'].queryset = ExamSession.objects.all()
        self.fields['allocation'].queryset = ExamAllocation.objects.select_related('exam', 'venue').all()
        self.fields['venue'].queryset = Venue.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.all()


class ReportFilterForm(forms.Form):
    """Report filter form"""
    report_type = forms.ChoiceField(
        choices=[('', 'All Types')],
        required=False
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(GeneratedReport.STATUS_CHOICES),
        required=False
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    generated_by = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Users"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set report type choices
        from .models import ReportTemplate
        self.fields['report_type'].choices = [('', 'All Types')] + ReportTemplate.REPORT_TYPES
        
        # Set generated_by queryset
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['generated_by'].queryset = User.objects.filter(
            Q(role='admin') | Q(role='exam_officer')
        )


class EmailReportForm(forms.Form):
    """Email report form"""
    recipients = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Enter email addresses (one per line or separated by commas)'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Enter email subject'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Enter email message (optional)'
        }),
        required=False
    )
    
    def clean_recipients(self):
        recipients = self.cleaned_data.get('recipients')
        if recipients:
            # Split by newline or comma
            emails = [email.strip() for email in recipients.replace(',', '\n').split('\n') if email.strip()]
            # Validate email format
            from django.core.validators import validate_email
            for email in emails:
                try:
                    validate_email(email)
                except forms.ValidationError:
                    raise forms.ValidationError(f"Invalid email address: {email}")
            return emails
        return recipients


class ReportPermissionForm(forms.ModelForm):
    """Report permission form"""
    class Meta:
        model = ReportPermission
        fields = ['user', 'report_type', 'permission_type', 'expires_at']
        widgets = {
            'expires_at': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set user queryset
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['user'].queryset = User.objects.all()
        
        # Set report type choices
        from .models import ReportTemplate
        self.fields['report_type'].choices = ReportTemplate.REPORT_TYPES

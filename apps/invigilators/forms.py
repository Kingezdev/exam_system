from django import forms
from django.contrib.auth import get_user_model
from .models import (
    InvigilatorProfile, InvigilatorAvailability, InvigilatorPerformance,
    InvigilatorTraining, InvigilatorLeave
)
from apps.venues.models import Venue
from apps.academics.models import Department

User = get_user_model()


class InvigilatorProfileForm(forms.ModelForm):
    """Invigilator profile form"""
    class Meta:
        model = InvigilatorProfile
        fields = [
            'staff_id', 'department', 'phone_number', 'email_address',
            'qualification', 'experience_years', 'max_exams_per_day',
            'preferred_venues', 'is_available', 'emergency_contact',
            'emergency_phone', 'notes'
        ]
        widgets = {
            'preferred_venues': forms.CheckboxSelectMultiple(),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_venues'].queryset = Venue.objects.filter(
            is_active=True,
            is_available_for_exams=True
        )


class InvigilatorAvailabilityForm(forms.ModelForm):
    """Invigilator availability form"""
    class Meta:
        model = InvigilatorAvailability
        fields = ['date', 'start_time', 'end_time', 'is_available', 'reason', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.TextInput(attrs={'placeholder': 'Reason for availability/unavailability'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time")
        
        return cleaned_data


class InvigilatorPerformanceForm(forms.ModelForm):
    """Invigilator performance evaluation form"""
    class Meta:
        model = InvigilatorPerformance
        fields = [
            'invigilator', 'exam', 'rating', 'punctuality',
            'professionalism', 'exam_conduct', 'feedback'
        ]
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter invigilators
        self.fields['invigilator'].queryset = InvigilatorProfile.objects.all()
        
        # Filter exams that have completed
        from apps.exams.models import Exam
        from django.utils import timezone
        self.fields['exam'].queryset = Exam.objects.filter(
            date__lt=timezone.now().date()
        ).order_by('-date')


class InvigilatorTrainingForm(forms.ModelForm):
    """Invigilator training form"""
    class Meta:
        model = InvigilatorTraining
        fields = [
            'invigilator', 'training_name', 'training_type',
            'training_date', 'duration_hours', 'trainer',
            'certificate_number', 'certificate_file', 'notes'
        ]
        widgets = {
            'training_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invigilator'].queryset = InvigilatorProfile.objects.all()


class InvigilatorLeaveForm(forms.ModelForm):
    """Invigilator leave request form"""
    class Meta:
        model = InvigilatorLeave
        fields = [
            'invigilator', 'leave_type', 'start_date', 'end_date', 'reason'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invigilator'].queryset = InvigilatorProfile.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Start date must be before or equal to end date")
            
            # Check if start date is in the past
            from django.utils import timezone
            if start_date < timezone.now().date():
                raise forms.ValidationError("Start date cannot be in the past")
        
        return cleaned_data


class InvigilatorFilterForm(forms.Form):
    """Invigilator filter form"""
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments"
    )
    is_available = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Available'),
            ('false', 'Unavailable')
        ],
        required=False
    )
    min_experience = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Min years'})
    )
    max_experience = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Max years'})
    )


class PerformanceFilterForm(forms.Form):
    """Performance filter form"""
    invigilator = forms.ModelChoiceField(
        queryset=InvigilatorProfile.objects.all(),
        required=False,
        empty_label="All Invigilators"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    min_rating = forms.ChoiceField(
        choices=[('', 'All')] + [(i, f'{i}+ Stars') for i in range(1, 6)],
        required=False
    )


class LeaveManagementForm(forms.ModelForm):
    """Leave management form for admin approval"""
    class Meta:
        model = InvigilatorLeave
        fields = ['status', 'rejection_reason']
        widgets = {
            'rejection_reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if status == 'rejected' and not rejection_reason:
            raise forms.ValidationError("Rejection reason is required when rejecting leave request")
        
        return cleaned_data

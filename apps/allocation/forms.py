from django import forms
from .models import ExamAllocation, InvigilatorAssignment, AllocationRule
from apps.exams.models import Exam, ExamSession
from apps.venues.models import Venue, VenueLayout
from django.contrib.auth import get_user_model

User = get_user_model()


class ExamAllocationForm(forms.ModelForm):
    """Exam allocation form"""
    class Meta:
        model = ExamAllocation
        fields = ['venue', 'venue_layout', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter venues that are available for exams
        self.fields['venue'].queryset = Venue.objects.filter(
            is_active=True,
            is_available_for_exams=True
        )
        
        # Initialize venue_layout queryset
        self.fields['venue_layout'].queryset = VenueLayout.objects.none()
        
        if 'venue' in self.data:
            try:
                venue_id = int(self.data.get('venue'))
                self.fields['venue_layout'].queryset = VenueLayout.objects.filter(
                    venue_id=venue_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk and self.instance.venue:
            self.fields['venue_layout'].queryset = VenueLayout.objects.filter(
                venue=self.instance.venue,
                is_active=True
            )


class InvigilatorAssignmentForm(forms.ModelForm):
    """Invigilator assignment form"""
    class Meta:
        model = InvigilatorAssignment
        fields = ['invigilator', 'assignment_type', 'is_primary', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users with invigilator role
        self.fields['invigilator'].queryset = User.objects.filter(role='invigilator')


class AllocationRuleForm(forms.ModelForm):
    """Allocation rule form"""
    class Meta:
        model = AllocationRule
        fields = ['name', 'rule_type', 'description', 'condition', 'action', 'priority', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'condition': forms.Textarea(attrs={'rows': 5, 'placeholder': '{"field": "value", ...}'}),
            'action': forms.Textarea(attrs={'rows': 5, 'placeholder': '{"action": "value", ...}'}),
        }
    
    def clean_condition(self):
        condition = self.cleaned_data.get('condition')
        if condition:
            try:
                import json
                json.loads(condition)
            except json.JSONDecodeError:
                raise forms.ValidationError("Condition must be valid JSON")
        return condition
    
    def clean_action(self):
        action = self.cleaned_data.get('action')
        if action:
            try:
                import json
                json.loads(action)
            except json.JSONDecodeError:
                raise forms.ValidationError("Action must be valid JSON")
        return action


class ExamFilterForm(forms.Form):
    """Exam filter form for allocation"""
    exam_session = forms.ModelChoiceField(
        queryset=ExamSession.objects.all(),
        required=False,
        empty_label="All Sessions"
    )
    is_allocated = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('yes', 'Allocated'),
            ('no', 'Not Allocated')
        ],
        required=False
    )
    is_confirmed = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('yes', 'Confirmed'),
            ('no', 'Not Confirmed')
        ],
        required=False
    )
    venue = forms.ModelChoiceField(
        queryset=Venue.objects.filter(is_active=True),
        required=False,
        empty_label="All Venues"
    )


class SeatingPlanFilterForm(forms.Form):
    """Seating plan filter form"""
    venue = forms.ModelChoiceField(
        queryset=Venue.objects.filter(is_active=True),
        required=False,
        empty_label="All Venues"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )


class ConflictResolutionForm(forms.Form):
    """Conflict resolution form"""
    resolution_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=True
    )

from django import forms
from .models import Venue, VenueImage, VenueBlock, VenueLayout


class VenueForm(forms.ModelForm):
    """Venue form"""
    class Meta:
        model = Venue
        fields = [
            'name', 'code', 'venue_type', 'building', 'floor', 
            'capacity', 'exam_capacity', 'area_sqm',
            'has_projector', 'has_air_conditioning', 'has_whiteboard',
            'has_computers', 'has_power_outlets', 'is_wheelchair_accessible',
            'campus_location', 'gps_coordinates', 'description',
            'is_active', 'is_available_for_exams'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'gps_coordinates': forms.TextInput(attrs={'placeholder': 'e.g., 9.9335, 8.8865'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        capacity = cleaned_data.get('capacity')
        exam_capacity = cleaned_data.get('exam_capacity')
        
        if capacity and exam_capacity:
            if exam_capacity > capacity:
                raise forms.ValidationError("Exam capacity cannot exceed total capacity")
            
            if capacity <= 0:
                raise forms.ValidationError("Capacity must be greater than 0")
            
            if exam_capacity <= 0:
                raise forms.ValidationError("Exam capacity must be greater than 0")
        
        return cleaned_data


class VenueImageForm(forms.ModelForm):
    """Venue image form"""
    class Meta:
        model = VenueImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Enter image caption'}),
        }


class VenueBlockForm(forms.ModelForm):
    """Venue block form"""
    class Meta:
        model = VenueBlock
        fields = ['start_datetime', 'end_datetime', 'reason', 'is_maintenance']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reason': forms.TextInput(attrs={'placeholder': 'Reason for blocking the venue'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise forms.ValidationError("Start time must be before end time")
        
        return cleaned_data


class VenueLayoutForm(forms.ModelForm):
    """Venue layout form"""
    class Meta:
        model = VenueLayout
        fields = ['name', 'description', 'layout_image', 'rows', 'columns', 'spacing_type', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        rows = cleaned_data.get('rows')
        columns = cleaned_data.get('columns')
        
        if rows and columns:
            if rows <= 0 or columns <= 0:
                raise forms.ValidationError("Rows and columns must be greater than 0")
        
        return cleaned_data


class VenueFilterForm(forms.Form):
    """Venue filter form"""
    venue_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Venue.VENUE_TYPES),
        required=False
    )
    campus_location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Campus location'})
    )
    min_capacity = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': 'Min capacity'})
    )
    max_capacity = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': 'Max capacity'})
    )
    has_projector = forms.BooleanField(required=False)
    has_air_conditioning = forms.BooleanField(required=False)
    is_wheelchair_accessible = forms.BooleanField(required=False)

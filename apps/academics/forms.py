from django import forms
from django.db.models import Q
from .models import Faculty, Department, Course, StudentEnrollment, Program
from django.contrib.auth import get_user_model

User = get_user_model()


class FacultyForm(forms.ModelForm):
    """Faculty form"""
    class Meta:
        model = Faculty
        fields = ['name', 'code', 'description', 'dean']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dean'].queryset = User.objects.filter(
            Q(role='admin') | Q(role='exam_officer')
        )


class DepartmentForm(forms.ModelForm):
    """Department form"""
    class Meta:
        model = Department
        fields = ['name', 'code', 'faculty', 'head', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head'].queryset = User.objects.filter(
            Q(role='admin') | Q(role='exam_officer')
        )


class CourseForm(forms.ModelForm):
    """Course form"""
    class Meta:
        model = Course
        fields = ['name', 'code', 'department', 'credit_hours', 'level', 'semester', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProgramForm(forms.ModelForm):
    """Program form"""
    class Meta:
        model = Program
        fields = ['name', 'code', 'department', 'duration_years', 'degree_type', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class StudentEnrollmentForm(forms.ModelForm):
    """Student enrollment form"""
    class Meta:
        model = StudentEnrollment
        fields = ['student', 'course', 'academic_session', 'semester', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(role='student')
        self.fields['course'].queryset = Course.objects.filter(is_active=True)


class CourseFilterForm(forms.Form):
    """Course filter form"""
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments"
    )
    level = forms.ChoiceField(
        choices=[('', 'All Levels')] + [(i, f'Level {i}') for i in range(100, 600, 100)],
        required=False
    )
    semester = forms.ChoiceField(
        choices=[('', 'All Semesters'), ('first', 'First'), ('second', 'Second')],
        required=False
    )

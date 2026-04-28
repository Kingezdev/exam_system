from django import forms
from .models import Exam, ExamSession, QuestionPaper, ExamResult
from apps.academics.models import Course


class ExamSessionForm(forms.ModelForm):
    """Exam session form"""
    class Meta:
        model = ExamSession
        fields = ['name', 'academic_session', 'semester', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ExamForm(forms.ModelForm):
    """Exam form"""
    class Meta:
        model = Exam
        fields = [
            'course', 'exam_session', 'exam_type', 'date', 
            'start_time', 'end_time', 'duration_minutes',
            'total_marks', 'passing_marks', 'instructions', 'is_published'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.filter(is_active=True)


class QuestionPaperForm(forms.ModelForm):
    """Question paper form"""
    class Meta:
        model = QuestionPaper
        fields = ['title', 'description', 'file', 'text_content', 'is_secure']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'text_content': forms.Textarea(attrs={'rows': 10}),
        }


class ExamResultForm(forms.ModelForm):
    """Exam result form"""
    class Meta:
        model = ExamResult
        fields = ['student', 'marks_obtained', 'remarks', 'is_published']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        exam = kwargs.pop('exam', None)
        super().__init__(*args, **kwargs)
        
        if exam:
            # Filter students enrolled in the course
            from apps.academics.models import StudentEnrollment
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            enrolled_students = StudentEnrollment.objects.filter(
                course=exam.course,
                is_active=True
            ).values_list('student_id', flat=True)
            
            self.fields['student'].queryset = User.objects.filter(
                id__in=enrolled_students,
                role='student'
            )


class ExamFilterForm(forms.Form):
    """Exam filter form"""
    exam_session = forms.ModelChoiceField(
        queryset=ExamSession.objects.all(),
        required=False,
        empty_label="All Sessions"
    )
    exam_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Exam.EXAM_TYPES),
        required=False
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

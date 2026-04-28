from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


class ExamSession(models.Model):
    """Exam session model (e.g., 2023/2024 First Semester)"""
    name = models.CharField(max_length=100, unique=True)
    academic_session = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    semester = models.CharField(
        max_length=10,
        choices=[('first', 'First Semester'), ('second', 'Second Semester')],
        default='first'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-academic_session', 'semester']
        unique_together = ['academic_session', 'semester']
    
    def __str__(self):
        return f"{self.name} ({self.academic_session} {self.get_semester_display()})"
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date")


class Exam(models.Model):
    """Exam model"""
    EXAM_TYPES = (
        ('continuous', 'Continuous Assessment'),
        ('mid_semester', 'Mid-Semester Exam'),
        ('final', 'Final Exam'),
        ('supplementary', 'Supplementary Exam'),
    )
    
    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE, related_name='exams')
    exam_session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='exams')
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='final')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=40)
    instructions = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exams'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['course', 'exam_session', 'exam_type']
    
    def __str__(self):
        return f"{self.course.code} - {self.get_exam_type_display()} ({self.date})"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        # Calculate duration if not provided
        if not self.duration_minutes:
            start = datetime.combine(self.date, self.start_time)
            end = datetime.combine(self.date, self.end_time)
            self.duration_minutes = (end - start).seconds // 60


class QuestionPaper(models.Model):
    """Question paper model"""
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='question_paper')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='question_papers/', null=True, blank=True)
    text_content = models.TextField(blank=True, help_text="Text content of the question paper")
    is_secure = models.BooleanField(default=True, help_text="Restrict access to authorized users only")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Question Paper - {self.exam.course.code}"


class ExamConflict(models.Model):
    """Exam conflict detection and resolution"""
    exam1 = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='conflicts_as_exam1')
    exam2 = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='conflicts_as_exam2')
    conflict_type = models.CharField(
        max_length=20,
        choices=[
            ('time_overlap', 'Time Overlap'),
            ('same_students', 'Same Students'),
            ('same_venue', 'Same Venue'),
            ('invigilator_conflict', 'Invigilator Conflict'),
        ]
    )
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ['exam1', 'exam2', 'conflict_type']
    
    def __str__(self):
        return f"Conflict: {self.exam1} vs {self.exam2} ({self.conflict_type})"


class ExamAttendance(models.Model):
    """Exam attendance tracking"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_attendances'
    )
    is_present = models.BooleanField(default=False)
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_attendances'
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['exam', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.course.code} ({'Present' if self.is_present else 'Absent'})"


class ExamResult(models.Model):
    """Exam results model"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_results'
    )
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=5, blank=True)
    remarks = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    entered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['exam', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.course.code}: {self.marks_obtained}/{self.exam.total_marks}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate grade based on marks
        percentage = (self.marks_obtained / self.exam.total_marks) * 100
        if percentage >= 70:
            self.grade = 'A'
        elif percentage >= 60:
            self.grade = 'B'
        elif percentage >= 50:
            self.grade = 'C'
        elif percentage >= 45:
            self.grade = 'D'
        elif percentage >= 40:
            self.grade = 'E'
        else:
            self.grade = 'F'
        super().save(*args, **kwargs)

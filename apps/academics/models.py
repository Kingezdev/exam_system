from django.db import models
from django.conf import settings


class Faculty(models.Model):
    """Faculty model"""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    dean = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dean_of_faculty'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Department(models.Model):
    """Department model"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='head_of_department'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['faculty', 'name']
        unique_together = ['name', 'code', 'faculty']
    
    def __str__(self):
        return f"{self.name} ({self.code}) - {self.faculty.name}"


class Course(models.Model):
    """Course model"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    credit_hours = models.PositiveIntegerField(default=3)
    level = models.PositiveIntegerField(help_text="Academic level (100, 200, 300, 400, 500)")
    semester = models.CharField(
        max_length=10,
        choices=[('first', 'First Semester'), ('second', 'Second Semester')],
        default='first'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['department', 'level', 'code']
        unique_together = ['code', 'department']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class StudentEnrollment(models.Model):
    """Student enrollment model"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    academic_session = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    semester = models.CharField(
        max_length=10,
        choices=[('first', 'First Semester'), ('second', 'Second Semester')]
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['student', 'course', 'academic_session', 'semester']
        ordering = ['-academic_session', 'semester', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code} ({self.academic_session})"


class Program(models.Model):
    """Academic program model"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')
    duration_years = models.PositiveIntegerField(default=4)
    degree_type = models.CharField(
        max_length=50,
        choices=[
            ('bachelors', 'Bachelor\'s Degree'),
            ('masters', 'Master\'s Degree'),
            ('phd', 'Doctor of Philosophy'),
            ('diploma', 'Diploma'),
            ('certificate', 'Certificate')
        ],
        default='bachelors'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['department', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

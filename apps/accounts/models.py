from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with additional fields"""
    USER_ROLES = (
        ('admin', 'Administrator'),
        ('exam_officer', 'Exam Officer'),
        ('invigilator', 'Invigilator'),
        ('student', 'Student'),
    )
    
    role = models.CharField(max_length=20, choices=USER_ROLES, default='student')
    phone_number = models.CharField(max_length=20, blank=True)
    staff_id = models.CharField(max_length=20, blank=True, null=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True
    )
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

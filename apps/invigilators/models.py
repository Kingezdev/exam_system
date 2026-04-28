from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class InvigilatorProfile(models.Model):
    """Extended profile for invigilators"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invigilator_profile'
    )
    staff_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    email_address = models.EmailField()
    qualification = models.CharField(max_length=200, help_text="Highest qualification")
    experience_years = models.PositiveIntegerField(default=0, help_text="Years of invigilation experience")
    max_exams_per_day = models.PositiveIntegerField(default=3, help_text="Maximum exams per day")
    preferred_venues = models.ManyToManyField('venues.Venue', blank=True)
    is_available = models.BooleanField(default=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.staff_id}"
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def current_workload(self):
        """Get current workload for today"""
        today = timezone.now().date()
        from apps.allocation.models import InvigilatorAssignment
        
        return InvigilatorAssignment.objects.filter(
            invigilator=self.user,
            exam_allocation__exam__date=today
        ).count()


class InvigilatorAvailability(models.Model):
    """Invigilator availability schedule"""
    invigilator = models.ForeignKey(
        InvigilatorProfile,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['invigilator', 'date', 'start_time', 'end_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.invigilator.full_name} - {self.date} ({self.start_time}-{self.end_time})"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")


class InvigilatorPerformance(models.Model):
    """Performance tracking for invigilators"""
    invigilator = models.ForeignKey(
        InvigilatorProfile,
        on_delete=models.CASCADE,
        related_name='performance_records'
    )
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='invigilator_performances')
    rating = models.PositiveIntegerField(
        choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)],
        help_text="Performance rating (1-5 stars)"
    )
    punctuality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('poor', 'Poor'),
        ],
        default='good'
    )
    professionalism = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('poor', 'Poor'),
        ],
        default='good'
    )
    exam_conduct = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('poor', 'Poor'),
        ],
        default='good'
    )
    feedback = models.TextField(blank=True)
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invigilator_evaluations'
    )
    evaluation_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['invigilator', 'exam']
        ordering = ['-evaluation_date']
    
    def __str__(self):
        return f"{self.invigilator.full_name} - {self.exam.course.code}: {self.rating}/5"
    
    @property
    def average_score(self):
        """Calculate average performance score"""
        scores = {
            'excellent': 5,
            'good': 4,
            'average': 3,
            'poor': 2,
        }
        
        total = self.rating + scores.get(self.punctuality, 3) + scores.get(self.professionalism, 3) + scores.get(self.exam_conduct, 3)
        return round(total / 4, 2)


class InvigilatorTraining(models.Model):
    """Training records for invigilators"""
    invigilator = models.ForeignKey(
        InvigilatorProfile,
        on_delete=models.CASCADE,
        related_name='training_records'
    )
    training_name = models.CharField(max_length=200)
    training_type = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic Invigilation'),
            ('advanced', 'Advanced Techniques'),
            ('technology', 'Technology Systems'),
            ('emergency', 'Emergency Procedures'),
            ('other', 'Other'),
        ],
        default='basic'
    )
    training_date = models.DateField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2)
    trainer = models.CharField(max_length=200)
    certificate_number = models.CharField(max_length=100, blank=True)
    certificate_file = models.FileField(upload_to='invigilator_certificates/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-training_date']
    
    def __str__(self):
        return f"{self.invigilator.full_name} - {self.training_name} ({self.training_date})"


class InvigilatorLeave(models.Model):
    """Leave requests for invigilators"""
    LEAVE_TYPES = (
        ('sick', 'Sick Leave'),
        ('annual', 'Annual Leave'),
        ('personal', 'Personal Leave'),
        ('emergency', 'Emergency Leave'),
        ('training', 'Training Leave'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    invigilator = models.ForeignKey(
        InvigilatorProfile,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invigilator.full_name} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    def approve(self, user):
        """Approve the leave request"""
        self.status = 'approved'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, user, reason):
        """Reject the leave request"""
        self.status = 'rejected'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class InvigilatorNotification(models.Model):
    """Notifications for invigilators"""
    NOTIFICATION_TYPES = (
        ('assignment', 'New Assignment'),
        ('reminder', 'Assignment Reminder'),
        ('cancellation', 'Assignment Cancellation'),
        ('update', 'Schedule Update'),
        ('general', 'General Notice'),
    )
    
    invigilator = models.ForeignKey(
        InvigilatorProfile,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invigilator.full_name} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

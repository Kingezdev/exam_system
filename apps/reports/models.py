from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
import os


class ReportTemplate(models.Model):
    """Report templates for different types of reports"""
    REPORT_TYPES = (
        ('exam_timetable', 'Exam Timetable'),
        ('seating_plan', 'Seating Plan'),
        ('invigilator_schedule', 'Invigilator Schedule'),
        ('attendance_report', 'Attendance Report'),
        ('venue_utilization', 'Venue Utilization'),
        ('exam_statistics', 'Exam Statistics'),
        ('student_results', 'Student Results'),
        ('invigilator_performance', 'Invigilator Performance'),
    )
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    template_file = models.FileField(upload_to='report_templates/', null=True, blank=True)
    html_template = models.TextField(blank=True, help_text="HTML template for the report")
    css_styles = models.TextField(blank=True, help_text="CSS styles for the report")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['report_type', 'name']
        unique_together = ['name', 'report_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class GeneratedReport(models.Model):
    """Generated reports tracking"""
    STATUS_CHOICES = (
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('archived', 'Archived'),
    )
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='generated_reports')
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=ReportTemplate.REPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    parameters = models.JSONField(default=dict, help_text="Parameters used to generate the report")
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def file_url(self):
        """Get the file URL if file exists"""
        if self.file_path and default_storage.exists(self.file_path):
            return default_storage.url(self.file_path)
        return None
    
    @property
    def file_name(self):
        """Get the file name"""
        if self.file_path:
            return os.path.basename(self.file_path)
        return None
    
    def mark_completed(self, file_path, file_size=None):
        """Mark report as completed"""
        self.status = 'completed'
        self.file_path = file_path
        self.file_size = file_size
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        """Mark report as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    def increment_download(self):
        """Increment download count"""
        self.download_count += 1
        self.save()


class ReportSchedule(models.Model):
    """Scheduled reports"""
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    parameters = models.JSONField(default=dict)
    recipients = models.JSONField(default=list, help_text="List of email addresses")
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


class ReportLog(models.Model):
    """Log of report generation activities"""
    ACTION_TYPES = (
        ('generated', 'Report Generated'),
        ('downloaded', 'Report Downloaded'),
        ('scheduled', 'Report Scheduled'),
        ('failed', 'Report Failed'),
        ('archived', 'Report Archived'),
    )
    
    report = models.ForeignKey(GeneratedReport, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    schedule = models.ForeignKey(ReportSchedule, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.timestamp}"


class ReportPermission(models.Model):
    """Report access permissions"""
    PERMISSION_TYPES = (
        ('view', 'View'),
        ('generate', 'Generate'),
        ('download', 'Download'),
        ('schedule', 'Schedule'),
        ('delete', 'Delete'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_permissions'
    )
    report_type = models.CharField(max_length=30, choices=ReportTemplate.REPORT_TYPES)
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'report_type', 'permission_type']
        ordering = ['user', 'report_type', 'permission_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_report_type_display()} - {self.get_permission_type_display()}"

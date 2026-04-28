from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import random


class ExamAllocation(models.Model):
    """Main allocation model for exam venue and invigilator assignments"""
    exam = models.OneToOneField('exams.Exam', on_delete=models.CASCADE, related_name='allocation')
    venue = models.ForeignKey('venues.Venue', on_delete=models.CASCADE, related_name='exam_allocations')
    venue_layout = models.ForeignKey('venues.VenueLayout', on_delete=models.SET_NULL, null=True, blank=True)
    allocated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='exam_allocations'
    )
    allocation_date = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_allocations'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-allocation_date']
    
    def __str__(self):
        return f"{self.exam.course.code} - {self.venue.name}"
    
    def confirm_allocation(self, user):
        """Confirm the allocation"""
        self.is_confirmed = True
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.save()
    
    @property
    def total_allocated_students(self):
        """Get total number of allocated students"""
        return self.student_allocations.count()
    
    @property
    def total_assigned_invigilators(self):
        """Get total number of assigned invigilators"""
        return self.invigilator_assignments.count()


class StudentAllocation(models.Model):
    """Individual student seat allocation"""
    exam_allocation = models.ForeignKey(
        ExamAllocation, 
        on_delete=models.CASCADE, 
        related_name='student_allocations'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_seat_allocations'
    )
    seat_number = models.PositiveIntegerField()
    row_number = models.PositiveIntegerField()
    column_number = models.PositiveIntegerField()
    allocated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['exam_allocation', 'student']
        ordering = ['exam_allocation', 'row_number', 'column_number']
    
    def __str__(self):
        return f"{self.student.username} - Seat {self.seat_number} (R{self.row_number}, C{self.column_number})"


class InvigilatorAssignment(models.Model):
    """Invigilator assignment to exam venues"""
    ASSIGNMENT_TYPES = (
        ('chief', 'Chief Invigilator'),
        ('assistant', 'Assistant Invigilator'),
        ('support', 'Support Staff'),
    )
    
    exam_allocation = models.ForeignKey(
        ExamAllocation,
        on_delete=models.CASCADE,
        related_name='invigilator_assignments'
    )
    invigilator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invigilator_assignments'
    )
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='assistant')
    is_primary = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invigilator_assignments_made'
    )
    has_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['exam_allocation', 'invigilator']
        ordering = ['exam_allocation', '-is_primary', 'assignment_type']
    
    def __str__(self):
        return f"{self.invigilator.username} - {self.get_assignment_type_display()} - {self.exam_allocation.exam.course.code}"
    
    def accept_assignment(self):
        """Accept the invigilator assignment"""
        self.has_accepted = True
        self.accepted_at = timezone.now()
        self.save()


class AllocationRule(models.Model):
    """Rules for smart allocation engine"""
    RULE_TYPES = (
        ('seating', 'Seating Arrangement'),
        ('spacing', 'Student Spacing'),
        ('department_separation', 'Department Separation'),
        ('invigilator_workload', 'Invigilator Workload'),
        ('venue_preference', 'Venue Preference'),
    )
    
    name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    description = models.TextField()
    condition = models.JSONField(help_text="JSON condition for the rule")
    action = models.JSONField(help_text="JSON action to apply when condition is met")
    priority = models.PositiveIntegerField(default=0, help_text="Higher priority rules are applied first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class AllocationLog(models.Model):
    """Log of all allocation activities"""
    ACTION_TYPES = (
        ('auto_allocate', 'Auto Allocation'),
        ('manual_allocate', 'Manual Allocation'),
        ('modify_allocation', 'Modify Allocation'),
        ('cancel_allocation', 'Cancel Allocation'),
        ('reallocate', 'Reallocate'),
    )
    
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='allocation_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    old_data = models.JSONField(null=True, blank=True, help_text="Previous allocation data")
    new_data = models.JSONField(null=True, blank=True, help_text="New allocation data")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.exam.course.code} - {self.get_action_type_display()} - {self.timestamp}"


class SeatingPlan(models.Model):
    """Generated seating plan for exams"""
    exam_allocation = models.OneToOneField(
        ExamAllocation,
        on_delete=models.CASCADE,
        related_name='seating_plan'
    )
    plan_data = models.JSONField(help_text="Complete seating plan data")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Seating Plan - {self.exam_allocation.exam.course.code}"
    
    def publish_plan(self):
        """Publish the seating plan"""
        self.is_published = True
        self.published_at = timezone.now()
        self.save()
    
    def get_student_position(self, student_id):
        """Get seat position for a specific student"""
        for seat_info in self.plan_data.get('seats', []):
            if seat_info.get('student_id') == student_id:
                return seat_info
        return None
    
    def get_seats_by_row(self, row_number):
        """Get all seats in a specific row"""
        return [
            seat for seat in self.plan_data.get('seats', [])
            if seat.get('row') == row_number
        ]


class AllocationConflict(models.Model):
    """Conflicts detected during allocation"""
    CONFLICT_TYPES = (
        ('venue_overcapacity', 'Venue Overcapacity'),
        ('invigilator_double_booking', 'Invigilator Double Booking'),
        ('student_conflict', 'Student Conflict'),
        ('venue_unavailable', 'Venue Unavailable'),
        ('insufficient_invigilators', 'Insufficient Invigilators'),
    )
    
    exam_allocation = models.ForeignKey(
        ExamAllocation,
        on_delete=models.CASCADE,
        related_name='conflicts'
    )
    conflict_type = models.CharField(max_length=30, choices=CONFLICT_TYPES)
    description = models.TextField()
    severity = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-severity', '-detected_at']
    
    def __str__(self):
        return f"{self.exam_allocation.exam.course.code} - {self.conflict_type} ({self.severity})"

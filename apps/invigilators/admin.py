from django.contrib import admin
from .models import (
    InvigilatorProfile, InvigilatorAvailability, InvigilatorPerformance,
    InvigilatorTraining, InvigilatorLeave, InvigilatorNotification
)


class InvigilatorAvailabilityInline(admin.TabularInline):
    model = InvigilatorAvailability
    extra = 1


class InvigilatorPerformanceInline(admin.TabularInline):
    model = InvigilatorPerformance
    extra = 0
    readonly_fields = ('evaluation_date',)


class InvigilatorTrainingInline(admin.TabularInline):
    model = InvigilatorTraining
    extra = 1


@admin.register(InvigilatorProfile)
class InvigilatorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'staff_id', 'department', 'phone_number', 
        'is_available', 'experience_years', 'max_exams_per_day'
    )
    list_filter = (
        'is_available', 'department', 'experience_years', 
        'max_exams_per_day', 'created_at'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'staff_id', 'phone_number'
    )
    ordering = ('user__last_name', 'user__first_name')
    inlines = [
        InvigilatorAvailabilityInline, 
        InvigilatorPerformanceInline, 
        InvigilatorTrainingInline
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'staff_id', 'department', 'phone_number', 'email_address')
        }),
        ('Professional Details', {
            'fields': ('qualification', 'experience_years', 'max_exams_per_day', 'is_available')
        }),
        ('Preferences', {
            'fields': ('preferred_venues',)
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Additional', {
            'fields': ('notes',)
        }),
    )


@admin.register(InvigilatorAvailability)
class InvigilatorAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        'invigilator', 'date', 'start_time', 'end_time', 
        'is_available', 'reason'
    )
    list_filter = ('is_available', 'date', 'created_at')
    search_fields = (
        'invigilator__user__username', 'invigilator__user__first_name',
        'invigilator__user__last_name', 'reason'
    )
    ordering = ('-date', 'start_time')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InvigilatorPerformance)
class InvigilatorPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'invigilator', 'exam', 'rating', 'punctuality', 
        'professionalism', 'exam_conduct', 'average_score', 'evaluation_date'
    )
    list_filter = (
        'rating', 'punctuality', 'professionalism', 
        'exam_conduct', 'evaluation_date'
    )
    search_fields = (
        'invigilator__user__username', 'invigilator__user__first_name',
        'invigilator__user__last_name', 'exam__course__code', 'exam__course__name'
    )
    ordering = ('-evaluation_date',)
    readonly_fields = ('evaluation_date',)
    
    def average_score(self, obj):
        return obj.average_score
    average_score.short_description = 'Avg Score'


@admin.register(InvigilatorTraining)
class InvigilatorTrainingAdmin(admin.ModelAdmin):
    list_display = (
        'invigilator', 'training_name', 'training_type', 
        'training_date', 'duration_hours', 'trainer'
    )
    list_filter = ('training_type', 'training_date', 'created_at')
    search_fields = (
        'invigilator__user__username', 'invigilator__user__first_name',
        'invigilator__user__last_name', 'training_name', 'trainer'
    )
    ordering = ('-training_date',)
    readonly_fields = ('created_at',)


@admin.register(InvigilatorLeave)
class InvigilatorLeaveAdmin(admin.ModelAdmin):
    list_display = (
        'invigilator', 'leave_type', 'start_date', 'end_date', 
        'status', 'approved_by', 'created_at'
    )
    list_filter = ('leave_type', 'status', 'start_date', 'created_at')
    search_fields = (
        'invigilator__user__username', 'invigilator__user__first_name',
        'invigilator__user__last_name', 'reason'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'approved_at')
    
    actions = ['approve_leave', 'reject_leave']
    
    def approve_leave(self, request, queryset):
        for leave in queryset.filter(status='pending'):
            leave.approve(request.user)
        self.message_user(request, f'{queryset.count()} leave requests approved.')
    approve_leave.short_description = 'Approve selected leave requests'
    
    def reject_leave(self, request, queryset):
        for leave in queryset.filter(status='pending'):
            leave.reject(request.user, 'Rejected by admin')
        self.message_user(request, f'{queryset.count()} leave requests rejected.')
    reject_leave.short_description = 'Reject selected leave requests'


@admin.register(InvigilatorNotification)
class InvigilatorNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'invigilator', 'notification_type', 'title', 'is_read', 
        'sent_via_email', 'sent_via_sms', 'created_at'
    )
    list_filter = (
        'notification_type', 'is_read', 'sent_via_email', 
        'sent_via_sms', 'created_at'
    )
    search_fields = (
        'invigilator__user__username', 'invigilator__user__first_name',
        'invigilator__user__last_name', 'title', 'message'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'read_at')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{queryset.count()} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'

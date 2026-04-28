from django.contrib import admin
from .models import ReportTemplate, GeneratedReport, ReportSchedule, ReportLog, ReportPermission


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'is_active', 'created_at')
    list_filter = ('report_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('report_type', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'report_type', 'description', 'is_active')
        }),
        ('Template Files', {
            'fields': ('template_file', 'html_template', 'css_styles')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'report_type', 'status', 'generated_by', 
        'generated_at', 'completed_at', 'download_count'
    )
    list_filter = ('report_type', 'status', 'generated_at', 'completed_at')
    search_fields = ('title', 'template__name', 'generated_by__username')
    ordering = ('-generated_at',)
    readonly_fields = ('generated_at', 'completed_at', 'download_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('template', 'title', 'report_type', 'status')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size', 'download_count')
        }),
        ('Parameters', {
            'fields': ('parameters',)
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at', 'completed_at', 'expires_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_completed', 'mark_failed', 'delete_files']
    
    def mark_completed(self, request, queryset):
        for report in queryset.filter(status='generating'):
            report.status = 'completed'
            report.completed_at = timezone.now()
            report.save()
        self.message_user(request, f'{queryset.count()} reports marked as completed.')
    mark_completed.short_description = 'Mark selected reports as completed'
    
    def mark_failed(self, request, queryset):
        for report in queryset.filter(status='generating'):
            report.status = 'failed'
            report.error_message = 'Manually marked as failed'
            report.completed_at = timezone.now()
            report.save()
        self.message_user(request, f'{queryset.count()} reports marked as failed.')
    mark_failed.short_description = 'Mark selected reports as failed'
    
    def delete_files(self, request, queryset):
        deleted_count = 0
        for report in queryset:
            if report.file_path and default_storage.exists(report.file_path):
                default_storage.delete(report.file_path)
                deleted_count += 1
        self.message_user(request, f'{deleted_count} files deleted.')
    delete_files.short_description = 'Delete report files'


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'template', 'frequency', 'is_active', 
        'last_run', 'next_run', 'created_by'
    )
    list_filter = ('frequency', 'is_active', 'created_at', 'last_run')
    search_fields = ('name', 'template__name', 'created_by__username')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'last_run', 'next_run')
    
    actions = ['run_now', 'activate_schedules', 'deactivate_schedules']
    
    def run_now(self, request, queryset):
        for schedule in queryset:
            # Trigger report generation
            from .tasks import generate_scheduled_report
            generate_scheduled_report.delay(schedule.id)
        self.message_user(request, f'{queryset.count()} schedules queued for execution.')
    run_now.short_description = 'Run selected schedules now'
    
    def activate_schedules(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} schedules activated.')
    activate_schedules.short_description = 'Activate selected schedules'
    
    def deactivate_schedules(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} schedules deactivated.')
    deactivate_schedules.short_description = 'Deactivate selected schedules'


@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'report', 'schedule', 'performed_by', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    search_fields = (
        'description', 'performed_by__username', 
        'report__title', 'schedule__name'
    )
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically


@admin.register(ReportPermission)
class ReportPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'report_type', 'permission_type', 'granted_by', 'granted_at', 'expires_at')
    list_filter = ('report_type', 'permission_type', 'granted_at', 'expires_at')
    search_fields = ('user__username', 'granted_by__username')
    ordering = ('user', 'report_type', 'permission_type')
    readonly_fields = ('granted_at',)
    
    actions = ['delete_expired', 'extend_permissions']
    
    def delete_expired(self, request, queryset):
        from django.utils import timezone
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f'{count} expired permissions deleted.')
    delete_expired.short_description = 'Delete expired permissions'
    
    def extend_permissions(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        extended = queryset.filter(expires_at__lt=timezone.now() + timedelta(days=30))
        count = extended.count()
        extended.update(expires_at=timezone.now() + timedelta(days=365))
        self.message_user(request, f'{count} permissions extended by 1 year.')
    extend_permissions.short_description = 'Extend permissions by 1 year'

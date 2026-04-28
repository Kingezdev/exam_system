from django.contrib import admin
from .models import (
    ExamAllocation, StudentAllocation, InvigilatorAssignment,
    AllocationRule, AllocationLog, SeatingPlan, AllocationConflict
)


class StudentAllocationInline(admin.TabularInline):
    model = StudentAllocation
    extra = 0
    readonly_fields = ('allocated_at',)


class InvigilatorAssignmentInline(admin.TabularInline):
    model = InvigilatorAssignment
    extra = 0
    readonly_fields = ('assigned_at', 'accepted_at')


@admin.register(ExamAllocation)
class ExamAllocationAdmin(admin.ModelAdmin):
    list_display = (
        'exam', 'venue', 'venue_layout', 'is_confirmed', 
        'allocated_by', 'allocation_date'
    )
    list_filter = ('is_confirmed', 'allocation_date', 'venue')
    search_fields = ('exam__course__code', 'exam__course__name', 'venue__name')
    ordering = ('-allocation_date',)
    inlines = [StudentAllocationInline, InvigilatorAssignmentInline]
    readonly_fields = ('allocation_date', 'confirmed_at')


@admin.register(StudentAllocation)
class StudentAllocationAdmin(admin.ModelAdmin):
    list_display = (
        'exam_allocation', 'student', 'seat_number', 
        'row_number', 'column_number', 'allocated_at'
    )
    list_filter = ('allocated_at', 'row_number')
    search_fields = (
        'student__username', 'student__email', 
        'exam_allocation__exam__course__code'
    )
    ordering = ('exam_allocation', 'row_number', 'column_number')
    readonly_fields = ('allocated_at',)


@admin.register(InvigilatorAssignment)
class InvigilatorAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'exam_allocation', 'invigilator', 'assignment_type', 
        'is_primary', 'has_accepted', 'assigned_at'
    )
    list_filter = ('assignment_type', 'is_primary', 'has_accepted', 'assigned_at')
    search_fields = (
        'invigilator__username', 'invigilator__email',
        'exam_allocation__exam__course__code'
    )
    ordering = ('-assigned_at',)
    readonly_fields = ('assigned_at', 'accepted_at')


@admin.register(AllocationRule)
class AllocationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'priority', 'is_active', 'created_at')
    list_filter = ('rule_type', 'is_active', 'priority')
    search_fields = ('name', 'description')
    ordering = ('-priority', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AllocationLog)
class AllocationLogAdmin(admin.ModelAdmin):
    list_display = ('exam', 'action_type', 'performed_by', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    search_fields = (
        'exam__course__code', 'exam__course__name',
        'performed_by__username', 'description'
    )
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(SeatingPlan)
class SeatingPlanAdmin(admin.ModelAdmin):
    list_display = (
        'exam_allocation', 'generated_by', 'is_published', 
        'published_at', 'generated_at'
    )
    list_filter = ('is_published', 'generated_at', 'published_at')
    search_fields = (
        'exam_allocation__exam__course__code',
        'generated_by__username'
    )
    ordering = ('-generated_at',)
    readonly_fields = ('generated_at', 'published_at')


@admin.register(AllocationConflict)
class AllocationConflictAdmin(admin.ModelAdmin):
    list_display = (
        'exam_allocation', 'conflict_type', 'severity', 
        'is_resolved', 'detected_at'
    )
    list_filter = ('conflict_type', 'severity', 'is_resolved', 'detected_at')
    search_fields = (
        'exam_allocation__exam__course__code',
        'conflict_type', 'description'
    )
    ordering = ('-severity', '-detected_at')
    readonly_fields = ('detected_at', 'resolved_at')

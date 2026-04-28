from django.contrib import admin
from .models import Faculty, Department, Course, StudentEnrollment, Program


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'dean', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code', 'dean__username')
    ordering = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'faculty', 'head', 'created_at')
    list_filter = ('faculty', 'created_at')
    search_fields = ('name', 'code', 'faculty__name', 'head__username')
    ordering = ('faculty', 'name')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'level', 'semester', 'credit_hours', 'is_active')
    list_filter = ('department', 'level', 'semester', 'is_active', 'created_at')
    search_fields = ('code', 'name', 'department__name')
    ordering = ('department', 'level', 'code')


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'academic_session', 'semester', 'enrollment_date', 'is_active')
    list_filter = ('academic_session', 'semester', 'is_active', 'enrollment_date')
    search_fields = ('student__username', 'student__email', 'course__code', 'course__name')
    ordering = ('-academic_session', 'semester', 'student')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'degree_type', 'duration_years', 'is_active')
    list_filter = ('department', 'degree_type', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'department__name')
    ordering = ('department', 'name')

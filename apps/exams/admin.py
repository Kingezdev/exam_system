from django.contrib import admin
from .models import Exam, ExamSession, QuestionPaper, ExamConflict, ExamAttendance, ExamResult


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_session', 'semester', 'start_date', 'end_date', 'is_active')
    list_filter = ('semester', 'is_active', 'start_date')
    search_fields = ('name', 'academic_session')
    ordering = ('-academic_session', 'semester')


class QuestionPaperInline(admin.StackedInline):
    model = QuestionPaper
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('course', 'exam_session', 'exam_type', 'date', 'start_time', 'end_time', 'is_published')
    list_filter = ('exam_session', 'exam_type', 'date', 'is_published')
    search_fields = ('course__code', 'course__name', 'exam_session__name')
    ordering = ('date', 'start_time')
    inlines = [QuestionPaperInline]


@admin.register(QuestionPaper)
class QuestionPaperAdmin(admin.ModelAdmin):
    list_display = ('exam', 'title', 'is_secure', 'uploaded_by', 'uploaded_at')
    list_filter = ('is_secure', 'uploaded_at')
    search_fields = ('title', 'exam__course__code', 'exam__course__name')
    ordering = ('-uploaded_at',)


@admin.register(ExamConflict)
class ExamConflictAdmin(admin.ModelAdmin):
    list_display = ('exam1', 'exam2', 'conflict_type', 'is_resolved', 'detected_at')
    list_filter = ('conflict_type', 'is_resolved', 'detected_at')
    search_fields = ('exam1__course__code', 'exam2__course__code')
    ordering = ('-detected_at',)


@admin.register(ExamAttendance)
class ExamAttendanceAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'is_present', 'arrival_time', 'marked_by', 'marked_at')
    list_filter = ('is_present', 'marked_at')
    search_fields = ('exam__course__code', 'student__username', 'student__email')
    ordering = ('-marked_at',)


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'marks_obtained', 'grade', 'is_published', 'entered_at')
    list_filter = ('grade', 'is_published', 'entered_at')
    search_fields = ('exam__course__code', 'student__username', 'student__email')
    ordering = ('-entered_at',)

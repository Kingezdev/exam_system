from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from datetime import datetime, time
from .models import Exam, ExamSession, QuestionPaper, ExamConflict, ExamAttendance, ExamResult
from .forms import ExamForm, ExamSessionForm, QuestionPaperForm, ExamResultForm
from apps.academics.models import StudentEnrollment


@login_required
def exam_dashboard(request):
    """Exam dashboard for exam officers and admins"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    context = {
        'total_exams': Exam.objects.count(),
        'upcoming_exams': Exam.objects.filter(date__gte=datetime.now().date()).count(),
        'conflicts': ExamConflict.objects.filter(is_resolved=False).count(),
        'recent_exams': Exam.objects.order_by('-created_at')[:5],
    }
    return render(request, 'exams/exam_dashboard.html', context)


@login_required
def exam_session_list(request):
    """List all exam sessions"""
    sessions = ExamSession.objects.all()
    return render(request, 'exams/exam_session_list.html', {'sessions': sessions})


@login_required
def exam_session_create(request):
    """Create a new exam session"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = ExamSessionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam session created successfully!')
            return redirect('exams:exam_session_list')
    else:
        form = ExamSessionForm()
    return render(request, 'exams/exam_session_form.html', {'form': form, 'title': 'Create Exam Session'})


@login_required
def exam_session_update(request, pk):
    """Update exam session"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    session = get_object_or_404(ExamSession, pk=pk)
    
    if request.method == 'POST':
        form = ExamSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam session updated successfully!')
            return redirect('exams:exam_session_list')
    else:
        form = ExamSessionForm(instance=session)
    
    return render(request, 'exams/exam_session_form.html', {'form': form, 'title': 'Update Exam Session'})


@login_required
def exam_session_delete(request, pk):
    """Delete exam session"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    session = get_object_or_404(ExamSession, pk=pk)
    
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Exam session deleted successfully!')
        return redirect('exams:exam_session_list')
    
    return render(request, 'exams/exam_session_confirm_delete.html', {'session': session})


@login_required
def exam_list(request):
    """List all exams"""
    exams = Exam.objects.select_related('course', 'course__department', 'exam_session').all()
    
    # Filter by session if provided
    session_id = request.GET.get('session')
    if session_id:
        exams = exams.filter(exam_session_id=session_id)
    
    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        exams = exams.filter(date__gte=start_date)
    if end_date:
        exams = exams.filter(date__lte=end_date)
    
    sessions = ExamSession.objects.all()
    return render(request, 'exams/exam_list.html', {
        'exams': exams,
        'sessions': sessions,
        'selected_session': session_id,
        'start_date': start_date,
        'end_date': end_date
    })


@login_required
def exam_create(request):
    """Create a new exam"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            
            # Check for conflicts
            check_exam_conflicts(exam)
            
            messages.success(request, 'Exam created successfully!')
            return redirect('exams:exam_list')
    else:
        form = ExamForm()
    return render(request, 'exams/exam_form.html', {'form': form, 'title': 'Create Exam'})


@login_required
def exam_update(request, pk):
    """Update exam"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.updated_by = request.user
            exam.save()
            
            # Check for conflicts after update
            check_exam_conflicts(exam)
            
            messages.success(request, 'Exam updated successfully!')
            return redirect('exams:exam_detail', exam_id=exam.id)
    else:
        form = ExamForm(instance=exam)
    
    return render(request, 'exams/exam_form.html', {'form': form, 'title': 'Update Exam'})


@login_required
def exam_delete(request, pk):
    """Delete exam"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted successfully!')
        return redirect('exams:exam_list')
    
    return render(request, 'exams/exam_confirm_delete.html', {'exam': exam})


@login_required
def exam_detail(request, exam_id):
    """View exam details"""
    exam = get_object_or_404(Exam, id=exam_id)
    enrollments = StudentEnrollment.objects.filter(course=exam.course, is_active=True)
    
    # Create attendance lookup dictionary for template
    attendances = {}
    for attendance in ExamAttendance.objects.filter(exam=exam):
        attendances[attendance.student_id] = attendance
    
    # Create seat allocation lookup dictionary for template
    seat_allocations = {}
    try:
        allocation = exam.allocation
        for student_allocation in allocation.student_allocations.all():
            seat_allocations[student_allocation.student_id] = student_allocation.seat_number
    except Exam.allocation.RelatedObjectDoesNotExist:
        # Exam has no allocation, seat_allocations remains empty
        pass
    
    # Add attendance and seat info to each enrollment
    enrollment_data = []
    for enrollment in enrollments:
        attendance = attendances.get(enrollment.student_id)
        seat_number = seat_allocations.get(enrollment.student_id)
        enrollment_data.append({
            'enrollment': enrollment,
            'attendance': attendance,
            'has_attendance': attendance is not None,
            'is_present': attendance.is_present if attendance else False,
            'has_seat': seat_number is not None,
            'seat_number': seat_number
        })
    
    context = {
        'exam': exam,
        'enrollment_data': enrollment_data,
        'attendance_count': ExamAttendance.objects.filter(exam=exam, is_present=True).count(),
        'total_students': enrollments.count(),
    }
    return render(request, 'exams/exam_detail.html', context)


@login_required
def upload_question_paper(request, exam_id):
    """Upload question paper for an exam"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    try:
        question_paper = exam.question_paper
    except QuestionPaper.DoesNotExist:
        question_paper = None
    
    if request.method == 'POST':
        form = QuestionPaperForm(request.POST, request.FILES, instance=question_paper)
        if form.is_valid():
            paper = form.save(commit=False)
            paper.exam = exam
            paper.uploaded_by = request.user
            paper.save()
            messages.success(request, 'Question paper uploaded successfully!')
            return redirect('exams:exam_detail', exam_id=exam.id)
    else:
        form = QuestionPaperForm(instance=question_paper)
    
    return render(request, 'exams/upload_question_paper.html', {
        'form': form,
        'exam': exam,
        'title': 'Upload Question Paper'
    })


@login_required
def conflict_list(request):
    """List exam conflicts"""
    conflicts = ExamConflict.objects.select_related(
        'exam1', 'exam2', 'exam1__course', 'exam2__course'
    ).all()
    
    return render(request, 'exams/conflict_list.html', {'conflicts': conflicts})


@login_required
def resolve_conflict(request, conflict_id):
    """Resolve an exam conflict"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    conflict = get_object_or_404(ExamConflict, id=conflict_id)
    
    if request.method == 'POST':
        resolution_notes = request.POST.get('resolution_notes')
        if resolution_notes:
            conflict.is_resolved = True
            conflict.resolution_notes = resolution_notes
            conflict.resolved_by = request.user
            conflict.resolved_at = datetime.now()
            conflict.save()
            messages.success(request, 'Conflict resolved successfully!')
            return redirect('exams:conflict_list')
    
    return render(request, 'exams/resolve_conflict.html', {'conflict': conflict})


@login_required
def exam_attendance(request, exam_id):
    """Manage exam attendance"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    enrollments = StudentEnrollment.objects.filter(course=exam.course, is_active=True)
    attendances = {}
    
    for enrollment in enrollments:
        attendance, created = ExamAttendance.objects.get_or_create(
            exam=exam,
            student=enrollment.student,
            defaults={'marked_by': request.user}
        )
        attendances[enrollment.student.id] = attendance
    
    # Create seat allocation lookup dictionary for template
    seat_allocations = {}
    try:
        allocation = exam.allocation
        for student_allocation in allocation.student_allocations.all():
            seat_allocations[student_allocation.student_id] = student_allocation.seat_number
    except Exam.allocation.RelatedObjectDoesNotExist:
        # Exam has no allocation, seat_allocations remains empty
        pass
    
    # Create enrollment data structure for template
    enrollment_data = []
    for enrollment in enrollments:
        attendance = attendances.get(enrollment.student.id)
        seat_number = seat_allocations.get(enrollment.student.id)
        enrollment_data.append({
            'enrollment': enrollment,
            'attendance': attendance,
            'is_present': attendance.is_present if attendance else False,
            'arrival_time': attendance.arrival_time if attendance else None,
            'remarks': attendance.remarks if attendance else '',
            'has_seat': seat_number is not None,
            'seat_number': seat_number
        })
    
    if request.method == 'POST':
        for student_id, is_present in request.POST.items():
            if student_id.startswith('student_'):
                student_id = student_id.split('_')[1]
                attendance = attendances.get(int(student_id))
                if attendance:
                    attendance.is_present = is_present == 'on'
                    attendance.marked_by = request.user
                    attendance.save()
        
        messages.success(request, 'Attendance updated successfully!')
        return redirect('exams:exam_detail', exam_id=exam.id)
    
    return render(request, 'exams/attendance.html', {
        'exam': exam,
        'enrollment_data': enrollment_data,
        'attendances': attendances  # Keep for POST handling
    })


@login_required
def student_exam_schedule(request):
    """View exam schedule for current student"""
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('accounts:dashboard')
    
    # Get enrolled courses for current session
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('course')
    
    # Get exams for enrolled courses
    course_ids = enrollments.values_list('course_id', flat=True)
    exams = Exam.objects.filter(
        course_id__in=course_ids,
        is_published=True
    ).select_related('course', 'exam_session').order_by('date', 'start_time')
    
    return render(request, 'exams/student_schedule.html', {'exams': exams})


def check_exam_conflicts(exam):
    """Check for exam conflicts and create conflict records"""
    # Check for time overlaps
    overlapping_exams = Exam.objects.filter(
        date=exam.date,
        start_time__lt=exam.end_time,
        end_time__gt=exam.start_time
    ).exclude(id=exam.id)
    
    for other_exam in overlapping_exams:
        # Check for same students
        exam1_students = set(StudentEnrollment.objects.filter(
            course=exam.course, is_active=True
        ).values_list('student_id', flat=True))
        
        exam2_students = set(StudentEnrollment.objects.filter(
            course=other_exam.course, is_active=True
        ).values_list('student_id', flat=True))
        
        common_students = exam1_students.intersection(exam2_students)
        
        if common_students:
            ExamConflict.objects.get_or_create(
                exam1=exam,
                exam2=other_exam,
                conflict_type='same_students',
                defaults={
                    'description': f'{len(common_students)} students have both exams scheduled at the same time'
                }
            )

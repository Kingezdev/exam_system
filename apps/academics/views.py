from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Faculty, Department, Course, StudentEnrollment, Program
from .forms import FacultyForm, DepartmentForm, CourseForm, ProgramForm, StudentEnrollmentForm


@login_required
def faculty_list(request):
    """List all faculties"""
    faculties = Faculty.objects.all()
    return render(request, 'academics/faculty_list.html', {'faculties': faculties})


@login_required
def faculty_create(request):
    """Create a new faculty"""
    if request.method == 'POST':
        form = FacultyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Faculty created successfully!')
            return redirect('academics:faculty_list')
    else:
        form = FacultyForm()
    return render(request, 'academics/faculty_form.html', {'form': form, 'title': 'Create Faculty'})


@login_required
def faculty_update(request, pk):
    """Update faculty"""
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if request.method == 'POST':
        form = FacultyForm(request.POST, instance=faculty)
        if form.is_valid():
            form.save()
            messages.success(request, 'Faculty updated successfully!')
            return redirect('academics:faculty_list')
    else:
        form = FacultyForm(instance=faculty)
    
    return render(request, 'academics/faculty_form.html', {'form': form, 'title': 'Update Faculty'})


@login_required
def faculty_delete(request, pk):
    """Delete faculty"""
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if request.method == 'POST':
        faculty.delete()
        messages.success(request, 'Faculty deleted successfully!')
        return redirect('academics:faculty_list')
    
    return render(request, 'academics/faculty_confirm_delete.html', {'faculty': faculty})


@login_required
def department_list(request):
    """List all departments"""
    departments = Department.objects.select_related('faculty').all()
    return render(request, 'academics/department_list.html', {'departments': departments})


@login_required
def department_create(request):
    """Create a new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created successfully!')
            return redirect('academics:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'academics/department_form.html', {'form': form, 'title': 'Create Department'})


@login_required
def department_update(request, pk):
    """Update department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully!')
            return redirect('academics:department_list')
    else:
        form = DepartmentForm(instance=department)
    
    return render(request, 'academics/department_form.html', {'form': form, 'title': 'Update Department'})


@login_required
def department_delete(request, pk):
    """Delete department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully!')
        return redirect('academics:department_list')
    
    return render(request, 'academics/department_confirm_delete.html', {'department': department})


@login_required
def course_list(request):
    """List all courses"""
    courses = Course.objects.select_related('department', 'department__faculty').all()
    
    # Filter by department if provided
    dept_id = request.GET.get('department')
    if dept_id:
        courses = courses.filter(department_id=dept_id)
    
    # Filter by level if provided
    level = request.GET.get('level')
    if level:
        courses = courses.filter(level=level)
    
    departments = Department.objects.all()
    return render(request, 'academics/course_list.html', {
        'courses': courses,
        'departments': departments,
        'selected_dept': dept_id,
        'selected_level': level
    })


@login_required
def course_create(request):
    """Create a new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course created successfully!')
            return redirect('academics:course_list')
    else:
        form = CourseForm()
    return render(request, 'academics/course_form.html', {'form': form, 'title': 'Create Course'})


@login_required
def course_update(request, pk):
    """Update course"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('academics:course_list')
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'academics/course_form.html', {'form': form, 'title': 'Update Course'})


@login_required
def course_delete(request, pk):
    """Delete course"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('academics:course_list')
    
    return render(request, 'academics/course_confirm_delete.html', {'course': course})


@login_required
def program_list(request):
    """List all programs"""
    programs = Program.objects.select_related('department', 'department__faculty').all()
    
    # Apply filters
    dept_id = request.GET.get('department')
    faculty_id = request.GET.get('faculty')
    
    if dept_id:
        programs = programs.filter(department_id=dept_id)
    if faculty_id:
        programs = programs.filter(department__faculty_id=faculty_id)
    
    # Get statistics
    active_programs = programs.filter(is_active=True).count()
    total_students = sum(p.student_count for p in programs if hasattr(p, 'student_count'))
    
    # Get filter options
    departments = Department.objects.all()
    faculties = Faculty.objects.all()
    
    # Get chart data
    faculty_stats = {}
    for program in programs:
        faculty_name = program.department.faculty.name
        faculty_stats[faculty_name] = faculty_stats.get(faculty_name, 0) + 1
    
    duration_stats = {}
    for program in programs:
        duration = str(program.duration_years)
        duration_stats[duration] = duration_stats.get(duration, 0) + 1
    
    context = {
        'programs': programs,
        'active_programs': active_programs,
        'total_students': total_students,
        'total_departments': departments.count(),
        'departments': departments,
        'faculties': faculties,
        'faculty_stats': [{'name': k, 'count': v} for k, v in faculty_stats.items()],
        'duration_stats': [{'duration': k, 'count': v} for k, v in duration_stats.items()],
    }
    
    return render(request, 'academics/program_list.html', context)


@login_required
def program_create(request):
    """Create a new program"""
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program created successfully!')
            return redirect('academics:program_list')
    else:
        form = ProgramForm()
    return render(request, 'academics/program_form.html', {'form': form, 'title': 'Create Program'})


@login_required
def program_update(request, pk):
    """Update program"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program updated successfully!')
            return redirect('academics:program_list')
    else:
        form = ProgramForm(instance=program)
    
    return render(request, 'academics/program_form.html', {'form': form, 'title': 'Update Program'})


@login_required
def program_delete(request, pk):
    """Delete program"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        program.delete()
        messages.success(request, 'Program deleted successfully!')
        return redirect('academics:program_list')
    
    return render(request, 'academics/program_confirm_delete.html', {'program': program})


@login_required
def enrollment_list(request):
    """List student enrollments"""
    enrollments = StudentEnrollment.objects.select_related(
        'student', 'course', 'course__department'
    ).all()
    
    # Filter by student if provided
    student_id = request.GET.get('student')
    if student_id:
        enrollments = enrollments.filter(student_id=student_id)
    
    # Filter by academic session if provided
    session = request.GET.get('session')
    if session:
        enrollments = enrollments.filter(academic_session=session)
    
    return render(request, 'academics/enrollment_list.html', {
        'enrollments': enrollments,
        'selected_student': student_id,
        'selected_session': session
    })


@login_required
def enrollment_create(request):
    """Create a new student enrollment"""
    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save()
            messages.success(request, f'Student enrolled in {enrollment.course.code} successfully!')
            return redirect('academics:enrollment_list')
    else:
        form = StudentEnrollmentForm()
    return render(request, 'academics/enrollment_form.html', {'form': form, 'title': 'Enroll Student'})


@login_required
def enrollment_update(request, pk):
    """Update enrollment"""
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)
    
    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Enrollment updated successfully!')
            return redirect('academics:enrollment_list')
    else:
        form = StudentEnrollmentForm(instance=enrollment)
    
    return render(request, 'academics/enrollment_form.html', {'form': form, 'title': 'Update Enrollment'})


@login_required
def enrollment_delete(request, pk):
    """Delete enrollment"""
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)
    
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment deleted successfully!')
        return redirect('academics:enrollment_list')
    
    return render(request, 'academics/enrollment_confirm_delete.html', {'enrollment': enrollment})


@login_required
def student_courses(request):
    """View courses for current student"""
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('accounts:dashboard')
    
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('course', 'course__department')
    
    return render(request, 'academics/student_courses.html', {'enrollments': enrollments})

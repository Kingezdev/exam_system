from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
import csv
import io

from .models import (
    InvigilatorProfile, InvigilatorAvailability, InvigilatorPerformance,
    InvigilatorTraining, InvigilatorLeave, InvigilatorNotification
)
from .forms import (
    InvigilatorProfileForm, InvigilatorAvailabilityForm, InvigilatorPerformanceForm,
    InvigilatorTrainingForm, InvigilatorLeaveForm
)
from apps.allocation.models import InvigilatorAssignment


@login_required
def invigilator_dashboard(request):
    """Dashboard for invigilators"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        profile = request.user.invigilator_profile
    except InvigilatorProfile.DoesNotExist:
        messages.error(request, 'Please complete your invigilator profile first.')
        return redirect('invigilators:profile_create')
    
    # Get upcoming assignments
    upcoming_assignments = InvigilatorAssignment.objects.filter(
        invigilator=request.user,
        exam_allocation__exam__date__gte=timezone.now().date(),
        has_accepted=True
    ).select_related('exam_allocation', 'exam_allocation__exam', 'exam_allocation__venue').order_by('exam_allocation__exam__date')
    
    # Get unread notifications
    unread_notifications = InvigilatorNotification.objects.filter(
        invigilator=profile,
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Get current workload
    today = timezone.now().date()
    today_assignments = InvigilatorAssignment.objects.filter(
        invigilator=request.user,
        exam_allocation__exam__date=today,
        has_accepted=True
    ).count()
    
    context = {
        'profile': profile,
        'upcoming_assignments': upcoming_assignments,
        'unread_notifications': unread_notifications,
        'today_assignments': today_assignments,
        'total_assignments': InvigilatorAssignment.objects.filter(invigilator=request.user, has_accepted=True).count(),
    }
    return render(request, 'invigilators/dashboard.html', context)


@login_required
def invigilator_list(request):
    """List all invigilators (for admin/exam officers)"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    invigilators = InvigilatorProfile.objects.select_related('user', 'department').all()
    
    # Filter by availability if provided
    is_available = request.GET.get('available')
    if is_available:
        invigilators = invigilators.filter(is_available=is_available == 'true')
    
    # Filter by department if provided
    dept_id = request.GET.get('department')
    if dept_id:
        invigilators = invigilators.filter(department_id=dept_id)
    
    # Add performance rating
    for invigilator in invigilators:
        avg_rating = invigilator.performance_records.aggregate(avg=Avg('rating'))['avg']
        invigilator.avg_rating = round(avg_rating, 1) if avg_rating else None
    
    return render(request, 'invigilators/invigilator_list.html', {
        'invigilators': invigilators,
        'departments': get_departments(),
        'selected_dept': dept_id,
        'selected_available': is_available,
    })


@login_required
def profile_create(request):
    """Create invigilator profile"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        profile = request.user.invigilator_profile
        return redirect('profile_update')
    except InvigilatorProfile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = InvigilatorProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile created successfully!')
            return redirect('invigilators:dashboard')
    else:
        form = InvigilatorProfileForm()
    
    return render(request, 'invigilators/profile_form.html', {
        'form': form,
        'title': 'Create Invigilator Profile'
    })


@login_required
def profile_update(request):
    """Update invigilator profile"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        profile = request.user.invigilator_profile
    except InvigilatorProfile.DoesNotExist:
        return redirect('invigilators:profile_create')
    
    if request.method == 'POST':
        form = InvigilatorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('invigilators:dashboard')
    else:
        form = InvigilatorProfileForm(instance=profile)
    
    return render(request, 'invigilators/profile_form.html', {
        'form': form,
        'profile': profile,
        'title': 'Update Profile'
    })


@login_required
def manage_availability(request):
    """Manage invigilator availability"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        profile = request.user.invigilator_profile
    except InvigilatorProfile.DoesNotExist:
        return redirect('invigilators:profile_create')
    
    if request.method == 'POST':
        form = InvigilatorAvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.invigilator = profile
            availability.save()
            messages.success(request, 'Availability updated successfully!')
            return redirect('invigilators:manage_availability')
    else:
        form = InvigilatorAvailabilityForm()
    
    # Get existing availabilities
    availabilities = profile.availabilities.filter(
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')
    
    return render(request, 'invigilators/manage_availability.html', {
        'form': form,
        'availabilities': availabilities,
        'profile': profile
    })


@login_required
def my_assignments(request):
    """View invigilator's assignments"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    assignments = InvigilatorAssignment.objects.filter(
        invigilator=request.user
    ).select_related(
        'exam_allocation', 'exam_allocation__exam', 
        'exam_allocation__venue', 'exam_allocation__exam__course'
    ).order_by('-exam_allocation__exam__date')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        if status == 'accepted':
            assignments = assignments.filter(has_accepted=True)
        elif status == 'pending':
            assignments = assignments.filter(has_accepted=False)
    
    # Calculate assignment counts
    total_count = assignments.count()
    accepted_count = assignments.filter(has_accepted=True).count()
    pending_count = assignments.filter(has_accepted=False).count()
    
    return render(request, 'invigilators/my_assignments.html', {
        'assignments': assignments,
        'selected_status': status,
        'total_count': total_count,
        'accepted_count': accepted_count,
        'pending_count': pending_count
    })


@login_required
def accept_assignment(request, assignment_id):
    """Accept an invigilator assignment"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    assignment = get_object_or_404(InvigilatorAssignment, id=assignment_id, invigilator=request.user)
    
    if request.method == 'POST':
        assignment.accept_assignment()
        
        # Create notification
        try:
            profile = request.user.invigilator_profile
            InvigilatorNotification.objects.create(
                invigilator=profile,
                notification_type='assignment',
                title='Assignment Accepted',
                message=f'You have accepted the assignment for {assignment.exam_allocation.exam.course.code}',
                sent_via_email=True
            )
        except InvigilatorProfile.DoesNotExist:
            pass
        
        messages.success(request, 'Assignment accepted successfully!')
        return redirect('my_assignments')
    
    return render(request, 'invigilators/accept_assignment.html', {'assignment': assignment})


@login_required
def performance_records(request):
    """View performance records"""
    if request.user.role == 'invigilator':
        # Invigilators can only see their own performance
        try:
            profile = request.user.invigilator_profile
            performances = profile.performance_records.select_related('exam', 'exam__course').order_by('-evaluation_date')
        except InvigilatorProfile.DoesNotExist:
            performances = []
    else:
        # Admin/exam officers can see all performances
        if request.user.role not in ['admin', 'exam_officer']:
            messages.error(request, 'Access denied.')
            return redirect('accounts:dashboard')
        
        performances = InvigilatorPerformance.objects.select_related(
            'invigilator', 'invigilator__user', 'exam', 'exam__course'
        ).order_by('-evaluation_date')
        
        # Filter by invigilator if provided
        invigilator_id = request.GET.get('invigilator')
        if invigilator_id:
            performances = performances.filter(invigilator_id=invigilator_id)
    
    return render(request, 'invigilators/performance_records.html', {
        'performances': performances,
        'can_add': request.user.role in ['admin', 'exam_officer']
    })


@login_required
def add_performance(request):
    """Add performance record (admin/exam officer only)"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = InvigilatorPerformanceForm(request.POST)
        if form.is_valid():
            performance = form.save(commit=False)
            performance.evaluated_by = request.user
            performance.save()
            
            # Create notification for invigilator
            InvigilatorNotification.objects.create(
                invigilator=performance.invigilator,
                notification_type='update',
                title='Performance Evaluation',
                message=f'Your performance for {performance.exam.course.code} has been evaluated: {performance.rating}/5',
                sent_via_email=True
            )
            
            messages.success(request, 'Performance record added successfully!')
            return redirect('performance_records')
    else:
        form = InvigilatorPerformanceForm()
    
    return render(request, 'invigilators/performance_form.html', {
        'form': form,
        'title': 'Add Performance Record'
    })


@login_required
def notifications(request):
    """View notifications"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    try:
        profile = request.user.invigilator_profile
        notifications = profile.notifications.order_by('-created_at')
        
        # Mark all as read
        notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        
    except InvigilatorProfile.DoesNotExist:
        notifications = []
    
    # Calculate notification counts
    total_count = len(notifications)
    read_count = sum(1 for n in notifications if n.is_read)
    unread_count = total_count - read_count
    
    return render(request, 'invigilators/notifications.html', {
        'notifications': notifications,
        'total_count': total_count,
        'read_count': read_count,
        'unread_count': unread_count
    })


@login_required
def available_invigilators(request):
    """Get available invigilators for specific date/time (AJAX endpoint)"""
    if request.user.role not in ['admin', 'exam_officer']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'GET':
        date = request.GET.get('date')
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        
        if not all([date, start_time, end_time]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        try:
            exam_date = datetime.strptime(date, '%Y-%m-%d').date()
            exam_start = datetime.strptime(start_time, '%H:%M').time()
            exam_end = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid date/time format'}, status=400)
        
        # Get available invigilators
        available_invigilators = []
        
        for profile in InvigilatorProfile.objects.filter(is_available=True):
            # Check workload limit
            current_assignments = InvigilatorAssignment.objects.filter(
                invigilator=profile.user,
                exam_allocation__exam__date=exam_date
            ).count()
            
            if current_assignments >= profile.max_exams_per_day:
                continue
            
            # Check availability conflicts
            has_conflict = InvigilatorAvailability.objects.filter(
                invigilator=profile,
                date=exam_date,
                start_time__lte=exam_end,
                end_time__gte=exam_start,
                is_available=False
            ).exists()
            
            if has_conflict:
                continue
            
            # Check leave conflicts
            on_leave = InvigilatorLeave.objects.filter(
                invigilator=profile,
                start_date__lte=exam_date,
                end_date__gte=exam_date,
                status='approved'
            ).exists()
            
            if on_leave:
                continue
            
            available_invigilators.append({
                'id': profile.user.id,
                'name': profile.full_name,
                'staff_id': profile.staff_id,
                'department': profile.department.name if profile.department else 'N/A',
                'experience_years': profile.experience_years,
                'current_assignments': current_assignments,
                'max_assignments': profile.max_exams_per_day,
            })
        
        return JsonResponse({'invigilators': available_invigilators})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def export_invigilators(request):
    """Export invigilator list to CSV"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    # Get the same filtered queryset as invigilator_list
    invigilators = InvigilatorProfile.objects.select_related('user', 'department').all()
    
    # Apply same filters
    is_available = request.GET.get('available')
    if is_available:
        invigilators = invigilators.filter(is_available=is_available == 'true')
    
    dept_id = request.GET.get('department')
    if dept_id:
        invigilators = invigilators.filter(department_id=dept_id)
    
    # Add performance rating
    for invigilator in invigilators:
        avg_rating = invigilator.performance_records.aggregate(avg=Avg('rating'))['avg']
        invigilator.avg_rating = round(avg_rating, 1) if avg_rating else None
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="invigilators_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Staff ID',
        'Name',
        'Email',
        'Phone Number',
        'Department',
        'Qualification',
        'Experience Years',
        'Max Exams Per Day',
        'Available',
        'Average Rating',
        'Emergency Contact',
        'Emergency Phone',
        'Preferred Venues',
        'Notes'
    ])
    
    # Write data
    for invigilator in invigilators:
        preferred_venues = ', '.join([venue.name for venue in invigilator.preferred_venues.all()])
        writer.writerow([
            invigilator.staff_id,
            f"{invigilator.user.first_name} {invigilator.user.last_name}",
            invigilator.email_address,
            invigilator.phone_number,
            invigilator.department.name if invigilator.department else '',
            invigilator.qualification,
            invigilator.experience_years,
            invigilator.max_exams_per_day,
            'Yes' if invigilator.is_available else 'No',
            invigilator.avg_rating or 'N/A',
            invigilator.emergency_contact,
            invigilator.emergency_phone,
            preferred_venues,
            invigilator.notes or ''
        ])
    
    return response


def get_departments():
    """Helper function to get departments"""
    from apps.academics.models import Department
    return Department.objects.all()

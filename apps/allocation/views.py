from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    ExamAllocation, StudentAllocation, InvigilatorAssignment, 
    AllocationRule, AllocationLog, SeatingPlan, AllocationConflict
)
from .forms import (
    ExamAllocationForm, InvigilatorAssignmentForm, AllocationRuleForm
)
from apps.exams.models import Exam
from apps.venues.models import Venue, VenueLayout
from apps.academics.models import StudentEnrollment
from apps.invigilators.models import InvigilatorProfile


@login_required
def allocation_dashboard(request):
    """Allocation dashboard for exam officers"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    context = {
        'total_allocations': ExamAllocation.objects.count(),
        'pending_allocations': ExamAllocation.objects.filter(is_confirmed=False).count(),
        'conflicts': AllocationConflict.objects.filter(is_resolved=False).count(),
        'recent_allocations': ExamAllocation.objects.select_related(
            'exam', 'venue', 'exam__course'
        ).order_by('-allocation_date')[:5],
    }
    return render(request, 'allocation/allocation_dashboard.html', context)


@login_required
def allocate_exam(request, exam_id):
    """Allocate venue and invigilators for an exam"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    try:
        allocation = exam.allocation
    except ExamAllocation.DoesNotExist:
        allocation = None
    
    if request.method == 'POST':
        form = ExamAllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            allocation = form.save(commit=False)
            allocation.exam = exam
            allocation.allocated_by = request.user
            
            if not allocation.pk:  # New allocation
                allocation.save()
                # Log the allocation
                AllocationLog.objects.create(
                    exam=exam,
                    action_type='manual_allocate',
                    description=f"Manual allocation created for {exam.course.code}",
                    performed_by=request.user,
                    new_data={
                        'venue': allocation.venue.id,
                        'venue_layout': allocation.venue_layout.id if allocation.venue_layout else None
                    }
                )
                messages.success(request, 'Exam allocated successfully!')
            else:
                allocation.save()
                AllocationLog.objects.create(
                    exam=exam,
                    action_type='modify_allocation',
                    description=f"Allocation modified for {exam.course.code}",
                    performed_by=request.user,
                    old_data={'venue': allocation.venue.id},
                    new_data={'venue': allocation.venue.id}
                )
                messages.success(request, 'Allocation updated successfully!')
            
            return redirect('allocation_detail', allocation_id=allocation.id)
    else:
        form = ExamAllocationForm(instance=allocation)
    
    return render(request, 'allocation/allocate_exam.html', {
        'form': form,
        'exam': exam,
        'allocation': allocation,
        'title': 'Allocate Exam' if not allocation else 'Update Allocation'
    })


@login_required
def allocation_detail(request, allocation_id):
    """View allocation details"""
    allocation = get_object_or_404(
        ExamAllocation.objects.select_related(
            'exam', 'venue', 'venue_layout', 'allocated_by'
        ),
        id=allocation_id
    )
    
    student_allocations = allocation.student_allocations.select_related('student')
    invigilator_assignments = allocation.invigilator_assignments.select_related('invigilator')
    conflicts = allocation.conflicts.filter(is_resolved=False)
    
    try:
        seating_plan = allocation.seating_plan
    except SeatingPlan.DoesNotExist:
        seating_plan = None
    
    context = {
        'allocation': allocation,
        'student_allocations': student_allocations,
        'invigilator_assignments': invigilator_assignments,
        'conflicts': conflicts,
        'seating_plan': seating_plan,
    }
    return render(request, 'allocation/allocation_detail.html', context)


@login_required
def auto_allocate_students(request, allocation_id):
    """Automatically allocate students to seats"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    allocation = get_object_or_404(ExamAllocation, id=allocation_id)
    
    if request.method == 'POST':
        # Clear existing allocations
        allocation.student_allocations.all().delete()
        
        # Get enrolled students
        enrollments = StudentEnrollment.objects.filter(
            course=allocation.exam.course,
            is_active=True
        ).select_related('student')
        
        layout = allocation.venue_layout
        if not layout:
            messages.error(request, 'No venue layout selected. Please select a layout first.')
            return redirect('allocation_detail', allocation_id=allocation.id)
        
        # Generate seating plan
        seating_data = generate_seating_plan(enrollments, layout, allocation)
        
        # Create student allocations
        for seat_info in seating_data['seats']:
            StudentAllocation.objects.create(
                exam_allocation=allocation,
                student_id=seat_info['student_id'],
                seat_number=seat_info['seat_number'],
                row_number=seat_info['row'],
                column_number=seat_info['column']
            )
        
        # Create seating plan record
        SeatingPlan.objects.update_or_create(
            exam_allocation=allocation,
            defaults={
                'plan_data': seating_data,
                'generated_by': request.user
            }
        )
        
        # Log the allocation
        AllocationLog.objects.create(
            exam=allocation.exam,
            action_type='auto_allocate',
            description=f"Auto-allocated {len(enrollments)} students for {allocation.exam.course.code}",
            performed_by=request.user,
            new_data={'total_students': len(enrollments)}
        )
        
        messages.success(request, f'Successfully allocated {len(enrollments)} students!')
        return redirect('allocation_detail', allocation_id=allocation.id)
    
    return render(request, 'allocation/auto_allocate_students.html', {
        'allocation': allocation,
        'total_students': StudentEnrollment.objects.filter(
            course=allocation.exam.course,
            is_active=True
        ).count()
    })


@login_required
def assign_invigilator(request, allocation_id):
    """Assign invigilators to exam"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    allocation = get_object_or_404(ExamAllocation, id=allocation_id)
    
    if request.method == 'POST':
        form = InvigilatorAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.exam_allocation = allocation
            assignment.assigned_by = request.user
            assignment.save()
            
            messages.success(request, f'Invigilator {assignment.invigilator.username} assigned successfully!')
            return redirect('allocation_detail', allocation_id=allocation.id)
    else:
        form = InvigilatorAssignmentForm()
    
    return render(request, 'allocation/assign_invigilator.html', {
        'form': form,
        'allocation': allocation,
        'title': 'Assign Invigilator'
    })


@login_required
def confirm_allocation(request, allocation_id):
    """Confirm an allocation"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    allocation = get_object_or_404(ExamAllocation, id=allocation_id)
    
    if request.method == 'POST':
        allocation.confirm_allocation(request.user)
        
        # Log the confirmation
        AllocationLog.objects.create(
            exam=allocation.exam,
            action_type='modify_allocation',
            description=f"Allocation confirmed for {allocation.exam.course.code}",
            performed_by=request.user
        )
        
        messages.success(request, 'Allocation confirmed successfully!')
        return redirect('allocation_detail', allocation_id=allocation.id)
    
    return render(request, 'allocation/confirm_allocation.html', {'allocation': allocation})


@login_required
def seating_plan_view(request, allocation_id):
    """View seating plan"""
    allocation = get_object_or_404(ExamAllocation, id=allocation_id)
    
    try:
        seating_plan = allocation.seating_plan
    except SeatingPlan.DoesNotExist:
        messages.error(request, 'No seating plan generated yet.')
        return redirect('allocation_detail', allocation_id=allocation.id)
    
    return render(request, 'allocation/seating_plan.html', {
        'allocation': allocation,
        'seating_plan': seating_plan
    })


@login_required
def allocation_conflicts(request):
    """View all allocation conflicts"""
    conflicts = AllocationConflict.objects.select_related(
        'exam_allocation', 'exam_allocation__exam', 'exam_allocation__exam__course'
    ).filter(is_resolved=False).order_by('-severity', '-detected_at')
    
    # Calculate severity counts
    high_severity_count = conflicts.filter(severity='high').count()
    medium_severity_count = conflicts.filter(severity='medium').count()
    low_severity_count = conflicts.filter(severity='low').count()
    
    context = {
        'conflicts': conflicts,
        'high_severity_count': high_severity_count,
        'medium_severity_count': medium_severity_count,
        'low_severity_count': low_severity_count,
    }
    
    return render(request, 'allocation/conflicts.html', context)


@login_required
def resolve_conflict(request, conflict_id):
    """Resolve an allocation conflict"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    conflict = get_object_or_404(AllocationConflict, id=conflict_id)
    
    if request.method == 'POST':
        resolution_notes = request.POST.get('resolution_notes')
        if resolution_notes:
            conflict.is_resolved = True
            conflict.resolution_notes = resolution_notes
            conflict.resolved_by = request.user
            conflict.resolved_at = timezone.now()
            conflict.save()
            
            messages.success(request, 'Conflict resolved successfully!')
            return redirect('allocation_conflicts')
    
    return render(request, 'allocation/resolve_conflict.html', {'conflict': conflict})


def generate_seating_plan(enrollments, layout, allocation):
    """Generate intelligent seating plan"""
    seats = []
    students = list(enrollments)
    
    # Sort students by department to separate them
    students.sort(key=lambda x: x.student.department.id if x.student.department else 0)
    
    # Create seat assignments with department separation logic
    seat_number = 1
    current_row = 1
    current_col = 1
    
    for enrollment in students:
        # Find next available seat
        while True:
            if current_row > layout.rows:
                raise Exception("Not enough seats for all students")
            
            # Check if this position should be skipped for department separation
            if should_skip_seat(current_row, current_col, layout, students, seat_number):
                current_col += 1
                if current_col > layout.columns:
                    current_col = 1
                    current_row += 1
                continue
            
            seat_info = {
                'student_id': enrollment.student.id,
                'student_name': enrollment.student.get_full_name() or enrollment.student.username,
                'student_number': enrollment.student.username,
                'department': enrollment.student.department.name if enrollment.student.department else 'Unknown',
                'seat_number': seat_number,
                'row': current_row,
                'column': current_col,
            }
            seats.append(seat_info)
            
            # Move to next seat
            seat_number += 1
            current_col += 1
            if current_col > layout.columns:
                current_col = 1
                current_row += 1
            break
    
    return {
        'exam_id': allocation.exam.id,
        'course_code': allocation.exam.course.code,
        'venue': allocation.venue.name,
        'layout_name': layout.name,
        'total_seats': layout.total_seats,
        'allocated_seats': len(students),
        'rows': layout.rows,
        'columns': layout.columns,
        'seats': seats,
        'generated_at': timezone.now().isoformat()
    }


def should_skip_seat(row, col, layout, students, current_seat):
    """Determine if a seat should be skipped for department separation"""
    # Simple logic: skip every 3rd seat to create spacing between departments
    # This can be enhanced with more sophisticated algorithms
    if layout.spacing_type == 'social_distancing':
        # Skip seats to maintain social distancing
        return (row % 2 == 0 and col % 2 == 0)
    elif layout.spacing_type == 'wide':
        # Skip every other seat in each row
        return col % 2 == 0
    
    return False


# API Endpoints for Quick Actions
@login_required
@require_http_methods(["GET"])
def api_pending_allocations(request):
    """API endpoint to get pending allocations for confirmation"""
    if request.user.role not in ['admin', 'exam_officer']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        pending_allocations = ExamAllocation.objects.filter(
            is_confirmed=False
        ).select_related('exam', 'exam__course', 'venue').order_by('-allocation_date')
        
        allocations_data = []
        for allocation in pending_allocations:
            student_count = StudentAllocation.objects.filter(allocation=allocation).count()
            
            allocations_data.append({
                'id': allocation.id,
                'exam_id': allocation.exam.id,
                'exam_title': allocation.exam.title,
                'course_code': allocation.exam.course.code,
                'venue_name': allocation.venue.name,
                'allocation_date': allocation.allocation_date.isoformat(),
                'student_count': student_count,
                'created_at': allocation.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'allocations': allocations_data,
            'total_count': len(allocations_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_confirm_allocations(request):
    """API endpoint to confirm multiple allocations"""
    if request.user.role not in ['admin', 'exam_officer']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        allocation_ids = data.get('allocation_ids', [])
        
        if not allocation_ids:
            return JsonResponse({
                'success': False,
                'error': 'No allocation IDs provided'
            }, status=400)
        
        # Get allocations to confirm
        allocations = ExamAllocation.objects.filter(
            id__in=allocation_ids,
            is_confirmed=False
        )
        
        confirmed_count = 0
        for allocation in allocations:
            allocation.is_confirmed = True
            allocation.confirmed_by = request.user
            allocation.confirmed_at = timezone.now()
            allocation.save()
            
            # Create allocation log
            AllocationLog.objects.create(
                allocation=allocation,
                action='confirmed',
                user=request.user,
                details=f'Allocation confirmed via bulk confirmation'
            )
            
            confirmed_count += 1
        
        return JsonResponse({
            'success': True,
            'confirmed_count': confirmed_count,
            'message': f'Successfully confirmed {confirmed_count} allocation(s)'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def export_allocation_report(request):
    """Export allocation report in various formats"""
    if request.user.role not in ['admin', 'exam_officer']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        export_format = request.GET.get('format', 'xlsx')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Build queryset
        allocations = ExamAllocation.objects.select_related(
            'exam', 'exam__course', 'venue', 'confirmed_by'
        ).order_by('-allocation_date')
        
        # Apply date filters if provided
        if start_date:
            allocations = allocations.filter(allocation_date__gte=start_date)
        if end_date:
            allocations = allocations.filter(allocation_date__lte=end_date)
        
        if export_format == 'xlsx':
            # Export to Excel
            import pandas as pd
            import io
            
            # Prepare data
            data = []
            for allocation in allocations:
                student_count = StudentAllocation.objects.filter(allocation=allocation).count()
                invigilator_count = InvigilatorAssignment.objects.filter(allocation=allocation).count()
                
                data.append({
                    'Exam Title': allocation.exam.title,
                    'Course Code': allocation.exam.course.code,
                    'Course Name': allocation.exam.course.name,
                    'Venue': allocation.venue.name,
                    'Venue Code': allocation.venue.code,
                    'Allocation Date': allocation.allocation_date.strftime('%Y-%m-%d'),
                    'Exam Date': allocation.exam.exam_date.strftime('%Y-%m-%d'),
                    'Student Count': student_count,
                    'Invigilator Count': invigilator_count,
                    'Status': 'Confirmed' if allocation.is_confirmed else 'Pending',
                    'Confirmed By': allocation.confirmed_by.get_full_name() if allocation.confirmed_by else 'N/A',
                    'Confirmed At': allocation.confirmed_at.strftime('%Y-%m-%d %H:%M') if allocation.confirmed_at else 'N/A',
                    'Created At': allocation.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            # Create DataFrame and export
            df = pd.DataFrame(data)
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Allocations', index=False)
                
                # Get the workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Allocations']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename=allocation_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return response
            
        elif export_format == 'pdf':
            # Export to PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=allocation_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            
            doc = SimpleDocTemplate(response, pagesize=landscape(letter))
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("Allocation Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Table data
            table_data = [['Exam', 'Course', 'Venue', 'Date', 'Students', 'Status']]
            
            for allocation in allocations:
                student_count = StudentAllocation.objects.filter(allocation=allocation).count()
                table_data.append([
                    allocation.exam.title,
                    allocation.exam.course.code,
                    allocation.venue.name,
                    allocation.allocation_date.strftime('%Y-%m-%d'),
                    str(student_count),
                    'Confirmed' if allocation.is_confirmed else 'Pending'
                ])
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            doc.build(story)
            return response
            
        elif export_format == 'csv':
            # Export to CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Exam Title', 'Course Code', 'Course Name', 'Venue', 'Venue Code',
                'Allocation Date', 'Exam Date', 'Student Count', 'Invigilator Count',
                'Status', 'Confirmed By', 'Confirmed At', 'Created At'
            ])
            
            # Data
            for allocation in allocations:
                student_count = StudentAllocation.objects.filter(allocation=allocation).count()
                invigilator_count = InvigilatorAssignment.objects.filter(allocation=allocation).count()
                
                writer.writerow([
                    allocation.exam.title,
                    allocation.exam.course.code,
                    allocation.exam.course.name,
                    allocation.venue.name,
                    allocation.venue.code,
                    allocation.allocation_date.strftime('%Y-%m-%d'),
                    allocation.exam.exam_date.strftime('%Y-%m-%d'),
                    student_count,
                    invigilator_count,
                    'Confirmed' if allocation.is_confirmed else 'Pending',
                    allocation.confirmed_by.get_full_name() if allocation.confirmed_by else 'N/A',
                    allocation.confirmed_at.strftime('%Y-%m-%d %H:%M') if allocation.confirmed_at else 'N/A',
                    allocation.created_at.strftime('%Y-%m-%d %H:%M')
                ])
            
            response = HttpResponse(
                output.getvalue(),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename=allocation_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return response
            
        else:
            return JsonResponse({'error': 'Unsupported format'}, status=400)
            
    except ImportError as e:
        return JsonResponse({
            'success': False,
            'error': f'Missing required library: {str(e)}. Please install pandas, openpyxl, or reportlab.'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db.models import Count, Avg, Sum, Q
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import os
import json
from datetime import datetime, timedelta

from .models import ReportTemplate, GeneratedReport, ReportSchedule, ReportLog, ReportPermission
from .forms import ReportTemplateForm, ReportScheduleForm
from apps.exams.models import Exam, ExamSession
from apps.allocation.models import ExamAllocation, StudentAllocation, InvigilatorAssignment
from apps.venues.models import Venue
from apps.invigilators.models import InvigilatorProfile
from apps.academics.models import StudentEnrollment


@login_required
def reports_dashboard(request):
    """Reports dashboard"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    context = {
        'total_reports': GeneratedReport.objects.count(),
        'recent_reports': GeneratedReport.objects.order_by('-generated_at')[:5],
        'scheduled_reports': ReportSchedule.objects.filter(is_active=True).count(),
        'active_templates': ReportTemplate.objects.filter(is_active=True).count(),
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def report_templates(request):
    """Manage report templates"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    templates = ReportTemplate.objects.all()
    return render(request, 'reports/templates.html', {'templates': templates})


@login_required
def create_template(request):
    """Create a new report template"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = ReportTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Report template "{template.name}" created successfully!')
            return redirect('report_templates')
    else:
        form = ReportTemplateForm()
    
    return render(request, 'reports/template_form.html', {'form': form, 'title': 'Create Report Template'})


@login_required
def generate_report(request):
    """Generate a new report"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        parameters = {}
        
        # Collect parameters based on report type
        if report_type == 'exam_timetable':
            exam_session_id = request.POST.get('exam_session')
            if exam_session_id:
                parameters['exam_session_id'] = exam_session_id
        
        elif report_type == 'seating_plan':
            allocation_id = request.POST.get('allocation')
            if allocation_id:
                parameters['allocation_id'] = allocation_id
        
        elif report_type == 'invigilator_schedule':
            date_from = request.POST.get('date_from')
            date_to = request.POST.get('date_to')
            if date_from:
                parameters['date_from'] = date_from
            if date_to:
                parameters['date_to'] = date_to
        
        # Create report generation record
        try:
            template = ReportTemplate.objects.get(report_type=report_type, is_active=True)
            template_name = template.name
        except ReportTemplate.DoesNotExist:
            # Create a default template for this report type
            template_name = dict(ReportTemplate.REPORT_TYPES).get(report_type, report_type.replace('_', ' ').title())
            template = ReportTemplate.objects.create(
                name=template_name,
                report_type=report_type,
                description=f"Auto-generated template for {template_name}",
                is_active=True
            )
        
        report = GeneratedReport.objects.create(
            template=template,
            title=f"{template_name} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            report_type=report_type,
            parameters=parameters,
            generated_by=request.user
        )
        
        # Log the generation
        ReportLog.objects.create(
            report=report,
            action_type='generated',
            description=f"Started generating {template_name}",
            performed_by=request.user
        )
        
        try:
            # Generate the report
            if report_type == 'exam_timetable':
                file_path = generate_exam_timetable_pdf(report, parameters)
            elif report_type == 'seating_plan':
                file_path = generate_seating_plan_pdf(report, parameters)
            elif report_type == 'invigilator_schedule':
                file_path = generate_invigilator_schedule_pdf(report, parameters)
            elif report_type == 'attendance_report':
                file_path = generate_attendance_report_pdf(report, parameters)
            elif report_type == 'venue_utilization':
                file_path = generate_venue_utilization_pdf(report, parameters)
            elif report_type == 'exam_statistics':
                file_path = generate_exam_statistics_pdf(report, parameters)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
            
            # Get file size
            if default_storage.exists(file_path):
                file_size = default_storage.size(file_path)
            else:
                file_size = 0
            
            report.mark_completed(file_path, file_size)
            
            # Log completion
            ReportLog.objects.create(
                report=report,
                action_type='generated',
                description=f"Successfully generated {template_name}",
                performed_by=request.user
            )
            
            messages.success(request, 'Report generated successfully!')
            return redirect('reports:report_detail', report_id=report.id)
            
        except Exception as e:
            report.mark_failed(str(e))
            ReportLog.objects.create(
                report=report,
                action_type='failed',
                description=f"Failed to generate {template_name}: {str(e)}",
                performed_by=request.user
            )
            messages.error(request, f'Failed to generate report: {str(e)}')
            return redirect('reports:generate_report')
    
    # Get data for form
    exam_sessions = ExamSession.objects.all()
    allocations = ExamAllocation.objects.select_related('exam', 'venue').all()
    
    return render(request, 'reports/generate.html', {
        'exam_sessions': exam_sessions,
        'allocations': allocations,
        'report_types': ReportTemplate.REPORT_TYPES
    })


@login_required
def report_list(request):
    """List generated reports"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    reports = GeneratedReport.objects.select_related('template', 'generated_by').all()
    
    # Filter by report type if provided
    report_type = request.GET.get('type')
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        reports = reports.filter(status=status)
    
    # Calculate report counts
    total_count = reports.count()
    completed_count = reports.filter(status='completed').count()
    generating_count = reports.filter(status='generating').count()
    failed_count = reports.filter(status='failed').count()
    
    # Add formatted file sizes to reports
    for report in reports:
        report.formatted_file_size = format_file_size(report.file_size)
    
    return render(request, 'reports/list.html', {
        'reports': reports,
        'report_types': ReportTemplate.REPORT_TYPES,
        'selected_type': report_type,
        'selected_status': status,
        'total_count': total_count,
        'completed_count': completed_count,
        'generating_count': generating_count,
        'failed_count': failed_count
    })


@login_required
def report_detail(request, report_id):
    """View report details"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    report = get_object_or_404(GeneratedReport, id=report_id)
    logs = report.logs.order_by('-timestamp')
    
    return render(request, 'reports/detail.html', {
        'report': report,
        'logs': logs
    })


@login_required
def download_report(request, report_id):
    """Download a generated report"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    report = get_object_or_404(GeneratedReport, id=report_id)
    
    if not report.file_path or not default_storage.exists(report.file_path):
        raise Http404("Report file not found")
    
    # Increment download count
    report.increment_download()
    
    # Log download
    ReportLog.objects.create(
        report=report,
        action_type='downloaded',
        description=f"Report downloaded by {request.user.username}",
        performed_by=request.user
    )
    
    # Serve the file
    file_content = default_storage.open(report.file_path).read()
    response = HttpResponse(file_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report.file_name}"'
    response['Content-Length'] = len(file_content)
    
    return response


@login_required
def scheduled_reports(request):
    """Manage scheduled reports"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    schedules = ReportSchedule.objects.select_related('template', 'created_by').all()
    
    # Calculate schedule counts
    total_count = schedules.count()
    active_count = schedules.filter(is_active=True).count()
    # Note: ReportSchedule model doesn't have a 'status' field, so we'll use is_active for inactive count
    inactive_count = schedules.filter(is_active=False).count()
    
    return render(request, 'reports/scheduled.html', {
        'schedules': schedules,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count
    })


@login_required
def create_schedule(request):
    """Create a new report schedule"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = ReportScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            
            messages.success(request, f'Report schedule "{schedule.name}" created successfully!')
            return redirect('scheduled_reports')
    else:
        form = ReportScheduleForm()
    
    return render(request, 'reports/schedule_form.html', {'form': form, 'title': 'Create Report Schedule'})


@login_required
def generate_timetable(request):
    """Generate exam timetable PDF"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        exam_session_id = request.POST.get('exam_session')
        
        if not exam_session_id:
            messages.error(request, 'Please select an exam session.')
            return redirect('reports:generate_timetable')
        
        try:
            exam_session = ExamSession.objects.get(id=exam_session_id)
            
            # Create a generated report record
            try:
                template = ReportTemplate.objects.get(report_type='exam_timetable', is_active=True)
                template_name = template.name
            except ReportTemplate.DoesNotExist:
                # Create a default template for this report type
                template_name = dict(ReportTemplate.REPORT_TYPES).get('exam_timetable', 'Exam Timetable')
                template = ReportTemplate.objects.create(
                    name=template_name,
                    report_type='exam_timetable',
                    description=f"Auto-generated template for {template_name}",
                    is_active=True
                )
            
            report = GeneratedReport.objects.create(
                template=template,
                title=f"{template_name} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                report_type='exam_timetable',
                parameters={'exam_session_id': exam_session_id},
                generated_by=request.user,
                status='generating'
            )
            
            # Generate the PDF (simplified version for now)
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.units import inch
                from django.http import HttpResponse
                import io
                
                # Create PDF
                buffer = io.BytesIO()
                p = canvas.Canvas(buffer, pagesize=A4)
                
                # Add title
                p.setFont("Helvetica-Bold", 16)
                p.drawString(100, 750, f"Exam Timetable - {exam_session.name}")
                p.setFont("Helvetica", 12)
                p.drawString(100, 730, f"Session: {exam_session.start_date} to {exam_session.end_date}")
                
                # Add some basic content
                y_position = 700
                p.drawString(100, y_position, "Generated on: " + str(timezone.now().strftime("%Y-%m-%d %H:%M")))
                
                # Save PDF
                p.save()
                
                # Update report record
                report.status = 'completed'
                report.file_path = f"timetables/timetable_{report.id}.pdf"
                report.save()
                
                # Return PDF response
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="exam_timetable_{exam_session.name}.pdf"'
                
                messages.success(request, 'Exam timetable generated successfully!')
                return response
                
            except Exception as e:
                report.status = 'failed'
                report.error_message = str(e)
                report.save()
                messages.error(request, f'Error generating timetable: {str(e)}')
                
        except ExamSession.DoesNotExist:
            messages.error(request, 'Exam session not found.')
    
    # Get available exam sessions
    exam_sessions = ExamSession.objects.all().order_by('-start_date')
    
    context = {
        'exam_sessions': exam_sessions,
    }
    
    return render(request, 'reports/generate_timetable.html', context)


@login_required
def generate_seating(request):
    """Generate seating plan PDF"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        exam_id = request.POST.get('exam')
        
        if not exam_id:
            messages.error(request, 'Please select an exam.')
            return redirect('reports:generate_seating')
        
        try:
            exam = Exam.objects.get(id=exam_id)
            
            # Check if allocation exists
            try:
                allocation = exam.allocation
                if not allocation.student_allocations.exists():
                    messages.error(request, 'No seating allocations found for this exam.')
                    return redirect('reports:generate_seating')
            except ExamAllocation.DoesNotExist:
                messages.error(request, 'No allocation found for this exam.')
                return redirect('reports:generate_seating')
            
            # Create a generated report record
            report = GeneratedReport.objects.create(
                template=None,  # We'll create a basic template or use None
                report_type='seating_plan',
                parameters={'exam_id': exam_id},
                generated_by=request.user,
                status='generating'
            )
            
            # Generate the PDF (simplified version for now)
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.units import inch
                from django.http import HttpResponse
                import io
                
                # Create PDF
                buffer = io.BytesIO()
                p = canvas.Canvas(buffer, pagesize=A4)
                
                # Add title
                p.setFont("Helvetica-Bold", 16)
                p.drawString(100, 750, f"Seating Plan - {exam.course.code}")
                p.setFont("Helvetica", 12)
                p.drawString(100, 730, f"Exam: {exam.course.title}")
                p.drawString(100, 715, f"Date: {exam.date}")
                p.drawString(100, 700, f"Venue: {allocation.venue.name}")
                
                # Add seating information
                y_position = 670
                p.setFont("Helvetica-Bold", 12)
                p.drawString(100, y_position, "Student Seating Arrangement:")
                y_position -= 20
                
                p.setFont("Helvetica", 10)
                student_allocations = allocation.student_allocations.select_related('student').order_by('seat_number')
                
                for student_alloc in student_allocations:
                    if y_position < 50:  # Start new page if needed
                        p.showPage()
                        y_position = 750
                    
                    seat_info = f"Seat {student_alloc.seat_number}: {student_alloc.student.get_full_name() or student_alloc.student.username}"
                    p.drawString(120, y_position, seat_info)
                    y_position -= 15
                
                # Save PDF
                p.save()
                
                # Update report record
                report.status = 'completed'
                report.file_path = f"seating/seating_plan_{report.id}.pdf"
                report.save()
                
                # Return PDF response
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="seating_plan_{exam.course.code}.pdf"'
                
                messages.success(request, 'Seating plan generated successfully!')
                return response
                
            except Exception as e:
                report.status = 'failed'
                report.error_message = str(e)
                report.save()
                messages.error(request, f'Error generating seating plan: {str(e)}')
                
        except Exam.DoesNotExist:
            messages.error(request, 'Exam not found.')
    
    # Get available exams with allocations
    exams = Exam.objects.filter(allocation__isnull=False).select_related('course', 'allocation').order_by('date')
    
    context = {
        'exams': exams,
    }
    
    return render(request, 'reports/generate_seating.html', context)


@login_required
def generate_invigilator(request):
    """Generate invigilator schedule PDF"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        exam_session_id = request.POST.get('exam_session')
        
        if not exam_session_id:
            messages.error(request, 'Please select an exam session.')
            return redirect('reports:generate_invigilator')
        
        try:
            exam_session = ExamSession.objects.get(id=exam_session_id)
            
            # Get all invigilator assignments for this session
            assignments = InvigilatorAssignment.objects.filter(
                exam_allocation__exam__exam_session=exam_session
            ).select_related('invigilator', 'exam_allocation__exam', 'exam_allocation__venue')
            
            if not assignments.exists():
                messages.error(request, 'No invigilator assignments found for this exam session.')
                return redirect('reports:generate_invigilator')
            
            # Create a generated report record
            report = GeneratedReport.objects.create(
                template=None,  # We'll create a basic template or use None
                report_type='invigilator_schedule',
                parameters={'exam_session_id': exam_session_id},
                generated_by=request.user,
                status='generating'
            )
            
            # Generate the PDF (simplified version for now)
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.units import inch
                from django.http import HttpResponse
                import io
                
                # Create PDF
                buffer = io.BytesIO()
                p = canvas.Canvas(buffer, pagesize=A4)
                
                # Add title
                p.setFont("Helvetica-Bold", 16)
                p.drawString(100, 750, f"Invigilator Schedule - {exam_session.name}")
                p.setFont("Helvetica", 12)
                p.drawString(100, 730, f"Session: {exam_session.start_date} to {exam_session.end_date}")
                
                # Add invigilator assignments
                y_position = 700
                p.setFont("Helvetica-Bold", 12)
                p.drawString(100, y_position, "Invigilator Assignments:")
                y_position -= 20
                
                p.setFont("Helvetica", 10)
                
                # Group assignments by invigilator
                invigilators = {}
                for assignment in assignments:
                    if assignment.invigilator not in invigilators:
                        invigilators[assignment.invigilator] = []
                    invigilators[assignment.invigilator].append(assignment)
                
                for invigilator, invigilator_assignments in invigilators.items():
                    if y_position < 100:  # Start new page if needed
                        p.showPage()
                        y_position = 750
                    
                    # Invigilator info
                    p.setFont("Helvetica-Bold", 11)
                    invigilator_name = invigilator.user.get_full_name() or invigilator.user.username
                    p.drawString(120, y_position, f"Invigilator: {invigilator_name}")
                    y_position -= 15
                    
                    p.setFont("Helvetica", 9)
                    p.drawString(140, y_position, f"Phone: {invigilator.phone_number or 'N/A'}")
                    y_position -= 12
                    
                    # List assignments
                    p.drawString(140, y_position, "Assignments:")
                    y_position -= 12
                    
                    for assignment in invigilator_assignments:
                        if y_position < 50:  # Start new page if needed
                            p.showPage()
                            y_position = 750
                        
                        exam = assignment.exam_allocation.exam
                        venue = assignment.exam_allocation.venue
                        assignment_info = f"  • {exam.course.code} - {exam.date} at {exam.start_time} - {venue.name}"
                        p.drawString(160, y_position, assignment_info)
                        y_position -= 10
                    
                    y_position -= 10  # Space between invigilators
                
                # Save PDF
                p.save()
                
                # Update report record
                report.status = 'completed'
                report.file_path = f"invigilators/invigilator_schedule_{report.id}.pdf"
                report.save()
                
                # Return PDF response
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="invigilator_schedule_{exam_session.name}.pdf"'
                
                messages.success(request, 'Invigilator schedule generated successfully!')
                return response
                
            except Exception as e:
                report.status = 'failed'
                report.error_message = str(e)
                report.save()
                messages.error(request, f'Error generating invigilator schedule: {str(e)}')
                
        except ExamSession.DoesNotExist:
            messages.error(request, 'Exam session not found.')
    
    # Get available exam sessions
    exam_sessions = ExamSession.objects.all().order_by('-start_date')
    
    context = {
        'exam_sessions': exam_sessions,
    }
    
    return render(request, 'reports/generate_invigilator.html', context)


@login_required
def analytics(request):
    """System analytics dashboard"""
    if request.user.role not in ['admin', 'exam_officer', 'invigilator']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    # Get basic statistics
    context = {
        'total_exams': Exam.objects.count(),
        'total_venues': Venue.objects.count(),
        'total_invigilators': InvigilatorProfile.objects.count(),
        'total_students': User.objects.filter(role='student').count(),
        'upcoming_exams': Exam.objects.filter(date__gte=timezone.now().date()).count(),
        'completed_exams': Exam.objects.filter(date__lt=timezone.now().date()).count(),
        'total_reports': GeneratedReport.objects.count(),
        'pending_reports': GeneratedReport.objects.filter(status='pending').count(),
    }
    
    return render(request, 'reports/analytics.html', context)


@login_required
def schedule_report(request):
    """Schedule a new report (alias for create_schedule)"""
    # This is an alias to the existing create_schedule view
    return create_schedule(request)


@login_required
def template_list(request):
    """List all report templates (alias for report_templates)"""
    # This is an alias to the existing report_templates view
    return report_templates(request)


@login_required
def template_create(request):
    """Create a new report template (alias for create_template)"""
    # This is an alias to the existing create_template view
    return create_template(request)


# PDF Generation Functions

def generate_exam_timetable_pdf(report, parameters):
    """Generate exam timetable PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    story.append(Paragraph("EXAMINATION TIMETABLE", title_style))
    
    # Get exam session
    exam_session_id = parameters.get('exam_session_id')
    if exam_session_id:
        exam_session = ExamSession.objects.get(id=exam_session_id)
        story.append(Paragraph(f"Session: {exam_session.name}", styles['Heading2']))
        story.append(Paragraph(f"Academic Session: {exam_session.academic_session}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Get exams for this session
        exams = Exam.objects.filter(
            exam_session=exam_session
        ).select_related('course', 'course__department').order_by('date', 'start_time')
        
        # Create table
        data = [['Date', 'Time', 'Course Code', 'Course Name', 'Venue', 'Type']]
        
        for exam in exams:
            try:
                venue = exam.allocation.venue.name if exam.allocation else 'Not Assigned'
            except:
                venue = 'Not Assigned'
            
            data.append([
                exam.date.strftime('%Y-%m-%d'),
                f"{exam.start_time.strftime('%H:%M')} - {exam.end_time.strftime('%H:%M')}",
                exam.course.code,
                exam.course.name,
                venue,
                exam.get_exam_type_display()
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    
    # Save to storage
    filename = f"exam_timetable_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = f"reports/{filename}"
    default_storage.save(file_path, ContentFile(buffer.getvalue()))
    
    buffer.close()
    return file_path


def generate_seating_plan_pdf(report, parameters):
    """Generate seating plan PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    story.append(Paragraph("SEATING PLAN", title_style))
    
    # Get allocation
    allocation_id = parameters.get('allocation_id')
    if allocation_id:
        allocation = ExamAllocation.objects.get(id=allocation_id)
        story.append(Paragraph(f"Exam: {allocation.exam.course.code} - {allocation.exam.course.name}", styles['Heading2']))
        story.append(Paragraph(f"Venue: {allocation.venue.name}", styles['Normal']))
        story.append(Paragraph(f"Date: {allocation.exam.date}", styles['Normal']))
        story.append(Paragraph(f"Time: {allocation.exam.start_time} - {allocation.exam.end_time}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Get seating plan
        try:
            seating_plan = allocation.seating_plan
            if seating_plan:
                # Create seating table
                layout = seating_plan.plan_data
                rows = layout.get('rows', 0)
                columns = layout.get('columns', 0)
                
                # Create header row
                header = ['Seat'] + [f'Col {i+1}' for i in range(columns)]
                data = [header]
                
                # Group seats by row
                seats_by_row = {}
                for seat in layout.get('seats', []):
                    row = seat.get('row', 0)
                    if row not in seats_by_row:
                        seats_by_row[row] = {}
                    seats_by_row[row][seat.get('column', 0)] = seat
                
                # Create table rows
                for row in range(1, rows + 1):
                    row_data = [f'Row {row}']
                    for col in range(1, columns + 1):
                        if row in seats_by_row and col in seats_by_row[row]:
                            seat = seats_by_row[row][col]
                            student_info = f"{seat.get('student_number', '')}"
                        else:
                            student_info = ""
                        row_data.append(student_info)
                    data.append(row_data)
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
        except:
            story.append(Paragraph("No seating plan available", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    # Save to storage
    filename = f"seating_plan_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = f"reports/{filename}"
    default_storage.save(file_path, ContentFile(buffer.getvalue()))
    
    buffer.close()
    return file_path


def generate_invigilator_schedule_pdf(report, parameters):
    """Generate invigilator schedule PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    story.append(Paragraph("INVIGILATOR SCHEDULE", title_style))
    
    # Get date range
    date_from = parameters.get('date_from')
    date_to = parameters.get('date_to')
    
    if date_from:
        story.append(Paragraph(f"From: {date_from}", styles['Normal']))
    if date_to:
        story.append(Paragraph(f"To: {date_to}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Get assignments
    assignments = InvigilatorAssignment.objects.select_related(
        'invigilator', 'exam_allocation', 'exam_allocation__exam', 'exam_allocation__venue'
    ).all()
    
    if date_from:
        assignments = assignments.filter(exam_allocation__exam__date__gte=date_from)
    if date_to:
        assignments = assignments.filter(exam_allocation__exam__date__lte=date_to)
    
    assignments = assignments.order_by('exam_allocation__exam__date', 'exam_allocation__exam__start_time')
    
    # Create table
    data = [['Date', 'Time', 'Invigilator', 'Exam', 'Venue', 'Type']]
    
    for assignment in assignments:
        data.append([
            assignment.exam_allocation.exam.date.strftime('%Y-%m-%d'),
            f"{assignment.exam_allocation.exam.start_time.strftime('%H:%M')} - {assignment.exam_allocation.exam.end_time.strftime('%H:%M')}",
            assignment.invigilator.get_full_name() or assignment.invigilator.username,
            f"{assignment.exam_allocation.exam.course.code} - {assignment.exam_allocation.exam.course.name}",
            assignment.exam_allocation.venue.name,
            assignment.get_assignment_type_display()
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    
    # Save to storage
    filename = f"invigilator_schedule_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = f"reports/{filename}"
    default_storage.save(file_path, ContentFile(buffer.getvalue()))
    
    buffer.close()
    return file_path


def generate_attendance_report_pdf(report, parameters):
    """Generate attendance report PDF"""
    # Similar implementation for attendance reports
    pass


def generate_venue_utilization_pdf(report, parameters):
    """Generate venue utilization PDF"""
    # Similar implementation for venue utilization reports
    pass


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if not size_bytes:
        return '-'
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1048576:  # 1024 * 1024
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / 1048576:.1f} MB"


def generate_exam_statistics_pdf(report, parameters):
    """Generate exam statistics PDF"""
    # Similar implementation for exam statistics
    pass

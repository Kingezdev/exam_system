from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.reports_dashboard, name='dashboard'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytics'),
    
    # Report Templates
    path('templates/', views.report_templates, name='report_templates'),
    path('templates/list/', views.template_list, name='template_list'),
    path('templates/create/', views.create_template, name='create_template'),
    path('templates/new/', views.template_create, name='template_create'),
    
    # Report Generation
    path('generate/', views.generate_report, name='generate_report'),
    path('generate/timetable/', views.generate_timetable, name='generate_timetable'),
    path('generate/seating/', views.generate_seating, name='generate_seating'),
    path('generate/invigilator/', views.generate_invigilator, name='generate_invigilator'),
    path('', views.report_list, name='report_list'),
    path('<int:report_id>/', views.report_detail, name='report_detail'),
    path('<int:report_id>/download/', views.download_report, name='download_report'),
    
    # Scheduled Reports
    path('scheduled/', views.scheduled_reports, name='scheduled_reports'),
    path('scheduled/create/', views.create_schedule, name='create_schedule'),
    path('schedule/', views.schedule_report, name='schedule_report'),
]

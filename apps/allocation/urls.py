from django.urls import path
from . import views

app_name = 'allocation'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.allocation_dashboard, name='dashboard'),
    
    # Exam Allocation
    path('exam/<int:exam_id>/', views.allocate_exam, name='allocate_exam'),
    path('detail/<int:allocation_id>/', views.allocation_detail, name='allocation_detail'),
    path('confirm/<int:allocation_id>/', views.confirm_allocation, name='confirm_allocation'),
    
    # Student Allocation
    path('auto-allocate-students/<int:allocation_id>/', views.auto_allocate_students, name='auto_allocate_students'),
    
    # Invigilator Assignment
    path('assign-invigilator/<int:allocation_id>/', views.assign_invigilator, name='assign_invigilator'),
    
    # Seating Plan
    path('seating-plan/<int:allocation_id>/', views.seating_plan_view, name='seating_plan'),
    
    # Conflicts
    path('conflicts/', views.allocation_conflicts, name='conflicts'),
    path('resolve-conflict/<int:conflict_id>/', views.resolve_conflict, name='resolve_conflict'),
    
    # API Endpoints
    path('api/pending-allocations/', views.api_pending_allocations, name='api_pending_allocations'),
    path('api/confirm-allocations/', views.api_confirm_allocations, name='api_confirm_allocations'),
    path('export-report/', views.export_allocation_report, name='export_report'),
]

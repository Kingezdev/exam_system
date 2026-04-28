from django.urls import path
from . import views

app_name = 'invigilators'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.invigilator_dashboard, name='dashboard'),
    
    # Profile Management
    path('profile/create/', views.profile_create, name='profile_create'),
    path('profile/update/', views.profile_update, name='profile_update'),
    
    # Availability Management
    path('availability/', views.manage_availability, name='manage_availability'),
    
    # Assignments
    path('assignments/', views.my_assignments, name='my_assignments'),
    path('assignments/<int:assignment_id>/accept/', views.accept_assignment, name='accept_assignment'),
    
    # Performance Records
    path('performance/', views.performance_records, name='performance_records'),
    path('performance/add/', views.add_performance, name='add_performance'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # Admin Views
    path('', views.invigilator_list, name='invigilator_list'),
    path('available/', views.available_invigilators, name='available_invigilators'),
    path('export/', views.export_invigilators, name='export_invigilators'),
]

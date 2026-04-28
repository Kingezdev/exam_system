from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.exam_dashboard, name='dashboard'),
    
    # Exam Sessions
    path('sessions/', views.exam_session_list, name='exam_session_list'),
    path('sessions/create/', views.exam_session_create, name='exam_session_create'),
    path('sessions/<int:pk>/edit/', views.exam_session_update, name='exam_session_update'),
    path('sessions/<int:pk>/delete/', views.exam_session_delete, name='exam_session_delete'),
    
    # Exams
    path('', views.exam_list, name='exam_list'),
    path('create/', views.exam_create, name='exam_create'),
    path('<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('<int:pk>/edit/', views.exam_update, name='exam_update'),
    path('<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    
    # Question Papers
    path('<int:exam_id>/upload-paper/', views.upload_question_paper, name='upload_question_paper'),
    
    # Conflicts
    path('conflicts/', views.conflict_list, name='conflict_list'),
    path('conflicts/<int:conflict_id>/resolve/', views.resolve_conflict, name='resolve_conflict'),
    
    # Attendance
    path('<int:exam_id>/attendance/', views.exam_attendance, name='exam_attendance'),
    
    # Student Views
    path('my-schedule/', views.student_exam_schedule, name='student_schedule'),
]

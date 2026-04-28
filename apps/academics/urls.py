from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Faculty URLs
    path('faculties/', views.faculty_list, name='faculty_list'),
    path('faculties/create/', views.faculty_create, name='faculty_create'),
    path('faculties/<int:pk>/edit/', views.faculty_update, name='faculty_update'),
    path('faculties/<int:pk>/delete/', views.faculty_delete, name='faculty_delete'),
    
    # Department URLs
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_update, name='department_update'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Course URLs
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Program URLs
    path('programs/', views.program_list, name='program_list'),
    path('programs/create/', views.program_create, name='program_create'),
    path('programs/<int:pk>/edit/', views.program_update, name='program_update'),
    path('programs/<int:pk>/delete/', views.program_delete, name='program_delete'),
    
    # Enrollment URLs
    path('enrollments/', views.enrollment_list, name='enrollment_list'),
    path('enrollments/create/', views.enrollment_create, name='enrollment_create'),
    path('enrollments/<int:pk>/edit/', views.enrollment_update, name='enrollment_update'),
    path('enrollments/<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),
    path('my-courses/', views.student_courses, name='student_courses'),
]

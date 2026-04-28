from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from . import views_home

app_name = 'accounts'

urlpatterns = [
    path('', views_home.home, name='home'),  # Homepage
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('password_change/', views.change_password, name='password_change'),
    path('backup/', views.backup_system, name='backup_system'),
    path('backup/download/<str:filename>/', views.download_backup, name='download_backup'),
]

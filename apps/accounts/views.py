from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm, UserProfileForm
from .models import User, UserProfile


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            
            # Grant staff status to admin users for Django admin access
            if user.role == 'admin':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('accounts:dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register_custom.html', {'form': form})


def login_view(request):
    """Custom login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'You are now logged in as {username}.')
                return redirect('accounts:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login_custom.html', {'form': form})


@login_required
def dashboard(request):
    """Role-based dashboard"""
    user = request.user
    context = {'user': user}
    
    if user.role == 'admin':
        return render(request, 'accounts/admin_dashboard.html', context)
    elif user.role == 'exam_officer':
        return render(request, 'accounts/exam_officer_dashboard.html', context)
    elif user.role == 'invigilator':
        return render(request, 'accounts/invigilator_dashboard.html', context)
    elif user.role == 'student':
        return render(request, 'accounts/student_dashboard.html', context)
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile(request):
    """User profile view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Your current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('accounts:login')
    
    return render(request, 'accounts/change_password.html')


@login_required
def backup_system(request):
    """System backup functionality"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        backup_type = request.POST.get('backup_type')
        
        if backup_type == 'database':
            try:
                import subprocess
                import os
                from django.conf import settings
                from django.utils import timezone
                
                # Create backup directory if it doesn't exist
                backup_dir = os.path.join(settings.BASE_DIR, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # Generate backup filename
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f'db_backup_{timestamp}.json'
                backup_path = os.path.join(backup_dir, backup_filename)
                
                # Run Django dumpdata command using current Python executable
                import sys
                cmd = [
                    sys.executable, 'manage.py', 'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--indent', '2',
                    '--output', backup_path
                ]
                
                # Set environment variables to ensure proper Django setup
                env = os.environ.copy()
                env['DJANGO_SETTINGS_MODULE'] = 'config.settings'
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=settings.BASE_DIR, env=env)
                
                if result.returncode == 0:
                    messages.success(request, f'Database backup created successfully: {backup_filename}')
                else:
                    messages.error(request, f'Backup failed: {result.stderr}')
                    
            except Exception as e:
                messages.error(request, f'Backup error: {str(e)}')
                
        elif backup_type == 'media':
            try:
                import shutil
                from django.conf import settings
                from django.utils import timezone
                
                # Create backup directory if it doesn't exist
                backup_dir = os.path.join(settings.BASE_DIR, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # Generate backup filename
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f'media_backup_{timestamp}.zip'
                backup_path = os.path.join(backup_dir, backup_filename)
                
                # Create zip file of media directory
                if os.path.exists(settings.MEDIA_ROOT):
                    shutil.make_archive(
                        backup_path.replace('.zip', ''),
                        'zip',
                        settings.MEDIA_ROOT
                    )
                    messages.success(request, f'Media files backup created successfully: {backup_filename}')
                else:
                    messages.warning(request, 'No media files found to backup.')
                    
            except Exception as e:
                messages.error(request, f'Media backup error: {str(e)}')
                
        elif backup_type == 'full':
            try:
                import subprocess
                import os
                import shutil
                from django.conf import settings
                from django.utils import timezone
                
                # Create backup directory if it doesn't exist
                backup_dir = os.path.join(settings.BASE_DIR, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # Generate backup filename
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                backup_dir_name = f'full_backup_{timestamp}'
                backup_path = os.path.join(backup_dir, backup_dir_name)
                os.makedirs(backup_path, exist_ok=True)
                
                # Database backup
                db_backup_path = os.path.join(backup_path, 'database.json')
                import sys
                cmd = [
                    sys.executable, 'manage.py', 'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--indent', '2',
                    '--output', db_backup_path
                ]
                
                # Set environment variables to ensure proper Django setup
                env = os.environ.copy()
                env['DJANGO_SETTINGS_MODULE'] = 'config.settings'
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=settings.BASE_DIR, env=env)
                
                if result.returncode == 0:
                    # Media backup
                    if os.path.exists(settings.MEDIA_ROOT):
                        media_backup_path = os.path.join(backup_path, 'media')
                        shutil.copytree(settings.MEDIA_ROOT, media_backup_path)
                    
                    # Create zip file
                    shutil.make_archive(backup_path, 'zip', backup_path)
                    shutil.rmtree(backup_path)  # Remove directory after zipping
                    
                    messages.success(request, f'Full system backup created successfully: {backup_dir_name}.zip')
                else:
                    messages.error(request, f'Backup failed: {result.stderr}')
                    
            except Exception as e:
                messages.error(request, f'Full backup error: {str(e)}')
    
    # Get backup history
    import os
    from django.conf import settings
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backup_files = []
    
    if os.path.exists(backup_dir):
        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                backup_files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'date': stat.st_mtime,
                    'type': 'Database' if filename.startswith('db_') else 'Media' if filename.startswith('media_') else 'Full'
                })
    
    backup_files.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'backup_files': backup_files,
    }
    
    return render(request, 'accounts/backup_system.html', context)


@login_required
def download_backup(request, filename):
    """Download backup file"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('accounts:dashboard')
    
    import os
    from django.conf import settings
    from django.http import HttpResponse, Http404
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        file_path = os.path.join(backup_dir, filename)
        
        logger.info(f"Attempting to download: {filename}")
        logger.info(f"Backup directory: {backup_dir}")
        logger.info(f"Full file path: {file_path}")
        
        # Security check - ensure file is in backup directory
        if not file_path.startswith(backup_dir):
            logger.error(f"Security check failed: {file_path} not in {backup_dir}")
            messages.error(request, 'Invalid file path.')
            return redirect('accounts:backup_system')
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            messages.error(request, 'Backup file not found.')
            return redirect('accounts:backup_system')
        
        # Get file info
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")
        
        # Determine content type based on file extension
        if filename.endswith('.zip'):
            content_type = 'application/zip'
        elif filename.endswith('.json'):
            content_type = 'application/json'
        else:
            content_type = 'application/octet-stream'
        
        # Read file and create response
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = file_size
            logger.info(f"Successfully created response for {filename}")
            return response
            
    except Exception as e:
        logger.error(f"Download error for {filename}: {str(e)}", exc_info=True)
        messages.error(request, f'Error downloading file: {str(e)}')
        return redirect('accounts:backup_system')

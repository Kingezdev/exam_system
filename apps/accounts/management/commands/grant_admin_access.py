from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Grant Django admin access to users with admin role'

    def handle(self, *args, **options):
        admin_users = User.objects.filter(role='admin')
        
        updated_count = 0
        for user in admin_users:
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Granted admin access to {user.username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'{user.username} already has admin access')
                )
        
        if updated_count == 0:
            self.stdout.write(
                self.style.WARNING('No admin users needed access updates')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully granted admin access to {updated_count} users')
            )

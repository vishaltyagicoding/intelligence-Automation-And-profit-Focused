"""
Django management command to grant full admin access to an existing superuser

Usage:
    python manage.py grantfulladmin <email>

Example:
    python manage.py grantfulladmin newadmin@example.com

This command will:
1. Update all admin files to include the email in permission checks
2. Grant full access to all admin modules
3. Restart is required after running this command
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import os
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Grant full admin access to an existing superuser'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the superuser to grant full access'
        )

    def handle(self, *args, **options):
        email = options['email'].strip().lower()

        # Validate email
        if not email or '@' not in email:
            raise CommandError('Invalid email address')

        # Check if user exists and is superuser
        try:
            user = User.objects.get(email=email)
            if not user.is_superuser:
                raise CommandError(f'{email} is not a superuser! Use createfulladmin to create one.')
        except User.DoesNotExist:
            raise CommandError(f'User with email {email} does not exist! Use createfulladmin to create one.')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('GRANTING FULL ADMIN ACCESS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write(f'📧 Email: {email}')
        self.stdout.write(f'👤 Username: {user.username}')
        self.stdout.write('')

        # List of admin files to update
        admin_files = [
            'users/admin.py',
            'payments/admin.py',
            'trading/admin.py',
            'security/admin.py',
            'signal_alerts/admin.py',
            'reversal_zones/admin.py',
            'market_data/admin.py',
        ]

        # Pattern to find and update
        # Look for the list of emails in permission checks
        pattern = r"(request\.user\.is_superuser and request\.user\.email in \[)([^\]]+)(\])"

        total_updates = 0
        updated_files = []

        for file_path in admin_files:
            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(f'⚠️  File not found: {file_path}'))
                continue

            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if email is already in the file
            if f"'{email}'" in content:
                self.stdout.write(f'✓ {file_path} - Already has access')
                continue

            # Find all matches
            matches = list(re.finditer(pattern, content))
            
            if not matches:
                self.stdout.write(self.style.WARNING(f'⚠️  No permission checks found in {file_path}'))
                continue

            # Update content
            def replace_func(match):
                prefix = match.group(1)
                emails = match.group(2)
                suffix = match.group(3)
                # Add the new email to the list
                return f"{prefix}{emails}, '{email}'{suffix}"

            new_content = re.sub(pattern, replace_func, content)

            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            count = len(matches)
            total_updates += count
            updated_files.append(file_path)
            self.stdout.write(self.style.SUCCESS(f'✅ {file_path} - Updated {count} permission check(s)'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ FULL ADMIN ACCESS GRANTED!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write(f'📊 Summary:')
        self.stdout.write(f'   - Files updated: {len(updated_files)}')
        self.stdout.write(f'   - Permission checks updated: {total_updates}')
        self.stdout.write('')
        self.stdout.write('Updated files:')
        for file_path in updated_files:
            self.stdout.write(f'   ✓ {file_path}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('⚠️  IMPORTANT: RESTART DJANGO SERVER'))
        self.stdout.write('')
        self.stdout.write('Run one of these commands to restart:')
        self.stdout.write('   - Docker: docker-compose restart django')
        self.stdout.write('   - Systemd: sudo systemctl restart django')
        self.stdout.write('   - Manual: Stop and start your Django server')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write(f'After restart, {email} will have FULL access to:')
        self.stdout.write('   ✅ All admin tables')
        self.stdout.write('   ✅ Add/edit/delete everything')
        self.stdout.write('   ✅ Payment Info table')
        self.stdout.write('   ✅ All trading, security, and market data')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))

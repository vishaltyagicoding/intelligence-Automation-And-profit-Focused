"""
Django management command to create a superuser with FULL admin access

Usage:
    python manage.py createfulladmin <email> [--username USERNAME] [--password PASSWORD]

Examples:
    # Interactive (will prompt for password)
    python manage.py createfulladmin newadmin@example.com

    # With username
    python manage.py createfulladmin newadmin@example.com --username newadmin

    # With password (not recommended for production - use interactive mode)
    python manage.py createfulladmin newadmin@example.com --password MySecurePass123!

    # Full command with all options
    python manage.py createfulladmin newadmin@example.com --username newadmin --password MySecurePass123!

IMPORTANT:
    After creating the superuser, you MUST add their email to the admin permission files
    to grant full access. Follow the instructions printed after user creation.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import getpass
import secrets
import string

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with full admin access (like alberttyagi123@gmail.com)'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address for the superuser'
        )
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='Username (optional, will be derived from email if not provided)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Password (optional, will prompt if not provided - RECOMMENDED for security)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='',
            help='First name (optional)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='',
            help='Last name (optional)'
        )
        parser.add_argument(
            '--auto-password',
            action='store_true',
            help='Generate a strong random password automatically'
        )

    def generate_strong_password(self, length=24):
        """Generate a very strong password"""
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        # Ensure at least one of each type
        password = [
            secrets.choice(uppercase),
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(digits),
            secrets.choice(symbols),
            secrets.choice(symbols),
        ]
        
        # Fill the rest
        all_chars = uppercase + lowercase + digits + symbols
        password += [secrets.choice(all_chars) for _ in range(length - len(password))]
        
        # Shuffle
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        username = options['username']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        auto_password = options['auto_password']

        # Validate email
        if not email or '@' not in email:
            raise CommandError('Invalid email address')

        # Generate username from email if not provided
        if not username:
            username = email.split('@')[0]
            self.stdout.write(f'Using username: {username}')

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists!')

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User with username {username} already exists!')

        # Handle password
        if auto_password:
            password = self.generate_strong_password()
            self.stdout.write(self.style.WARNING('Generated strong password (save this!):'))
            self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        elif not password:
            # Interactive password input
            password = getpass.getpass('Password: ')
            password_confirm = getpass.getpass('Password (again): ')
            
            if password != password_confirm:
                raise CommandError('Passwords do not match!')
            
            if len(password) < 8:
                raise CommandError('Password must be at least 8 characters long!')

        # Create superuser
        try:
            user = User.objects.create_superuser(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('✅ SUPERUSER CREATED SUCCESSFULLY!'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write(f'📧 Email:    {email}')
            self.stdout.write(f'👤 Username: {username}')
            if auto_password:
                self.stdout.write(f'🔑 Password: {password}')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.WARNING('⚠️  IMPORTANT: GRANT FULL ADMIN ACCESS'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write('This superuser has been created, but currently has LIMITED access.')
            self.stdout.write('To grant FULL admin access (like alberttyagi123@gmail.com), follow these steps:')
            self.stdout.write('')
            self.stdout.write('STEP 1: Update users/admin.py')
            self.stdout.write('────────────────────────────────')
            self.stdout.write('Find this line near the top:')
            self.stdout.write('')
            self.stdout.write(self.style.WARNING("    return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']"))
            self.stdout.write('')
            self.stdout.write('Change it to:')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f"    return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com', '{email}']"))
            self.stdout.write('')
            self.stdout.write('STEP 2: Run the update script')
            self.stdout.write('────────────────────────────────')
            self.stdout.write('Run this command to update ALL admin files:')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f"    python manage.py grantfulladmin {email}"))
            self.stdout.write('')
            self.stdout.write('OR manually update all admin files (7 files):')
            self.stdout.write('  - users/admin.py')
            self.stdout.write('  - payments/admin.py')
            self.stdout.write('  - trading/admin.py')
            self.stdout.write('  - security/admin.py')
            self.stdout.write('  - signal_alerts/admin.py')
            self.stdout.write('  - reversal_zones/admin.py')
            self.stdout.write('  - market_data/admin.py')
            self.stdout.write('')
            self.stdout.write('STEP 3: Restart Django')
            self.stdout.write('────────────────────────────────')
            self.stdout.write('Restart your Django server to apply changes.')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write('After completing these steps, the superuser will have FULL access to:')
            self.stdout.write('  ✅ All admin tables')
            self.stdout.write('  ✅ Add/edit/delete everything')
            self.stdout.write('  ✅ Payment Info table')
            self.stdout.write('  ✅ All trading, security, and market data')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 70))
            
        except IntegrityError as e:
            raise CommandError(f'Error creating user: {e}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')

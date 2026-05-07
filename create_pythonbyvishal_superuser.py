"""
Create pythonbyvishal@gmail.com superuser with full admin access
"""
import os
import django
import secrets
import string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Generate a very strong password
def generate_strong_password(length=20):
    """Generate a very strong password with uppercase, lowercase, numbers, and symbols"""
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
    
    # Fill the rest with random characters
    all_chars = uppercase + lowercase + digits + symbols
    password += [secrets.choice(all_chars) for _ in range(length - len(password))]
    
    # Shuffle to make it random
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)

# Create superuser
email = 'pythonbyvishal@gmail.com'
username = 'pythonbyvishal'
password = generate_strong_password(24)  # 24 character strong password

# Check if user already exists
if User.objects.filter(email=email).exists():
    print(f"❌ User with email {email} already exists!")
    user = User.objects.get(email=email)
    # Update password and ensure superuser status
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"✅ Updated existing user to superuser with new password")
else:
    # Create new superuser
    user = User.objects.create_superuser(
        email=email,
        username=username,
        password=password,
        first_name='Python',
        last_name='Vishal'
    )
    print(f"✅ Created new superuser")

print("\n" + "=" * 70)
print("FULL ACCESS SUPERUSER CREATED!")
print("=" * 70)
print(f"\n📧 Email:    {email}")
print(f"👤 Username: {username}")
print(f"🔑 Password: {password}")
print(f"\n⚠️  IMPORTANT: Save this password securely!")
print(f"⚠️  This password will NOT be shown again!")
print(f"\n🔗 Login URL: http://localhost:8000/admin/")
print("\n" + "=" * 70)
print("Access Level: FULL ADMIN ACCESS")
print("=" * 70)
print("\n✅ This superuser has the SAME permissions as alberttyagi123@gmail.com:")
print("   - Full access to ALL admin modules")
print("   - Can view, add, edit, delete everything")
print("   - Can access Payment Info table")
print("   - Can manage all users")
print("   - Can access all trading, security, and market data")
print("\n" + "=" * 70)
print("\n⚠️  COPY THIS PASSWORD NOW - IT WON'T BE SHOWN AGAIN!")
print("=" * 70)

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
sys.path.insert(0, '/app')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check for superuser with this email
email = 'alberttyagi123@gmail.com'
user = User.objects.filter(email=email).first()

if user:
    print(f"✅ User found!")
    print(f"   Email: {user.email}")
    print(f"   Username: {user.username}")
    print(f"   Is superuser: {user.is_superuser}")
    print(f"   Is staff: {user.is_staff}")
    print(f"   Is active: {user.is_active}")
    print(f"   Password hash: {user.password[:50]}...")
    
    # Test password
    password = 'NeuralTrade@Admin#2026$Secure!'
    if user.check_password(password):
        print(f"✅ Password is CORRECT")
    else:
        print(f"❌ Password is INCORRECT")
        print(f"   Resetting password to: {password}")
        user.set_password(password)
        user.save()
        print(f"✅ Password has been reset!")
    
    # Ensure superuser permissions
    if not user.is_superuser or not user.is_staff:
        print(f"⚠️  Fixing superuser permissions...")
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"✅ Superuser permissions granted!")
else:
    print(f"❌ User with email {email} NOT FOUND")
    print(f"   Creating new superuser...")
    user = User.objects.create_superuser(
        email=email,
        username='alberttyagi',
        password='NeuralTrade@Admin#2026$Secure!',
        first_name='Albert',
        last_name='Tyagi'
    )
    print(f"✅ Superuser created!")
    print(f"   Email: {user.email}")
    print(f"   Username: {user.username}")

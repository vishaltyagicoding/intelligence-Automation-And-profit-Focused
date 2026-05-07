"""
Create a test superuser to verify admin permissions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create test superuser
email = 'testsuperuser@example.com'
username = 'testsuperuser'
password = 'TestSuper123!'

# Check if user already exists
if User.objects.filter(email=email).exists():
    print(f"❌ User with email {email} already exists!")
    user = User.objects.get(email=email)
    # Update password
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"✅ Updated existing user to superuser")
else:
    # Create new superuser
    user = User.objects.create_superuser(
        email=email,
        username=username,
        password=password,
        first_name='Test',
        last_name='Superuser'
    )
    print(f"✅ Created new superuser")

print("\n" + "=" * 60)
print("Test Superuser Created Successfully!")
print("=" * 60)
print(f"\n📧 Email:    {email}")
print(f"👤 Username: {username}")
print(f"🔑 Password: {password}")
print(f"\n🔗 Login URL: http://localhost:8000/admin/")
print("\n" + "=" * 60)
print("Testing Instructions:")
print("=" * 60)
print("\n1. Go to: http://localhost:8000/admin/")
print(f"2. Login with: {email}")
print(f"3. Password: {password}")
print("4. Go to Users section")
print("5. Click on any user to edit")
print("\n✅ You should see:")
print("   - Only 2 sections: 'User Information (Read Only)' and 'Subscription Management'")
print("   - Email, username, names are READ-ONLY (grayed out)")
print("   - You can ONLY change: Activated/Deactivated subscription")
print("   - No 'Add User' button")
print("   - No 'Delete' button")
print("\n🔒 This is LIMITED ACCESS (as expected for non-albert superusers)")
print("\n" + "=" * 60)
print("\nTo test FULL ACCESS:")
print("=" * 60)
print("\n1. Logout from test superuser")
print("2. Login as: alberttyagi123@gmail.com")
print("3. You should see ALL 8 sections with full edit access")
print("\n" + "=" * 60)

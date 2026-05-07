import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
sys.path.insert(0, '/app')
django.setup()

from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

email = 'alberttyagi123@gmail.com'
password = 'NeuralTrade@Admin#2026$Secure!'

print(f"Testing authentication for: {email}")
print(f"Password: {password}")
print()

# Try to authenticate
user = authenticate(username=email, password=password)

if user:
    print(f"✅ Authentication SUCCESSFUL!")
    print(f"   User: {user.email}")
    print(f"   Is superuser: {user.is_superuser}")
    print(f"   Is staff: {user.is_staff}")
    print(f"   Is active: {user.is_active}")
else:
    print(f"❌ Authentication FAILED!")
    print()
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
        print(f"   User exists: {user.email}")
        print(f"   Is active: {user.is_active}")
        
        # Test password directly
        if user.check_password(password):
            print(f"   ✅ Password check: CORRECT")
        else:
            print(f"   ❌ Password check: INCORRECT")
            
            # Try to reset password
            print(f"\n   Resetting password...")
            user.set_password(password)
            user.save()
            print(f"   ✅ Password reset complete!")
            
            # Test again
            user = authenticate(username=email, password=password)
            if user:
                print(f"   ✅ Authentication now works!")
            else:
                print(f"   ❌ Authentication still fails!")
    except User.DoesNotExist:
        print(f"   User does not exist!")

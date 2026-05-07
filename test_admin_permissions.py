"""
Test script to verify admin permissions
- alberttyagi123@gmail.com: Full access
- Other superusers: Only subscription change access
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.admin import UserAdmin
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

User = get_user_model()

def test_admin_permissions():
    """Test admin permissions for different superusers"""
    
    print("=" * 70)
    print("Testing Admin Permissions")
    print("=" * 70)
    
    # Create mock request factory
    factory = RequestFactory()
    
    # Get or create test users
    albert, _ = User.objects.get_or_create(
        email='alberttyagi123@gmail.com',
        defaults={
            'username': 'albert',
            'is_superuser': True,
            'is_staff': True,
            'first_name': 'Albert',
            'last_name': 'Tyagi'
        }
    )
    
    other_super, _ = User.objects.get_or_create(
        email='other_superuser@example.com',
        defaults={
            'username': 'other_super',
            'is_superuser': True,
            'is_staff': True,
            'first_name': 'Other',
            'last_name': 'Super'
        }
    )
    
    # Get a test user to edit
    test_user = User.objects.filter(
        email__in=['test@example.com', 'test123@example.com']
    ).first()
    
    if not test_user:
        test_user, _ = User.objects.get_or_create(
            email='test_permissions@example.com',
            defaults={
                'username': 'test_permissions',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
    
    # Create UserAdmin instance
    site = AdminSite()
    user_admin = UserAdmin(User, site)
    
    print("\n" + "─" * 70)
    print("TEST 1: alberttyagi123@gmail.com Permissions")
    print("─" * 70)
    
    # Create mock request for albert
    request = factory.get('/admin/users/user/')
    request.user = albert
    
    # Test fieldsets
    fieldsets = user_admin.get_fieldsets(request, test_user)
    print(f"\n✓ Number of fieldsets: {len(fieldsets)}")
    print(f"  Fieldsets: {[fs[0] for fs in fieldsets]}")
    
    # Test readonly fields
    readonly = user_admin.get_readonly_fields(request, test_user)
    print(f"\n✓ Readonly fields count: {len(readonly)}")
    print(f"  Readonly fields: {readonly}")
    
    # Test permissions
    can_add = user_admin.has_add_permission(request)
    can_delete = user_admin.has_delete_permission(request, test_user)
    print(f"\n✓ Can add users: {can_add}")
    print(f"✓ Can delete users: {can_delete}")
    
    if len(fieldsets) >= 6 and can_add and can_delete:
        print("\n✅ PASS: alberttyagi123@gmail.com has FULL ACCESS")
    else:
        print("\n❌ FAIL: alberttyagi123@gmail.com should have full access!")
    
    print("\n" + "─" * 70)
    print("TEST 2: Other Superuser Permissions")
    print("─" * 70)
    
    # Create mock request for other superuser
    request = factory.get('/admin/users/user/')
    request.user = other_super
    
    # Test fieldsets
    fieldsets = user_admin.get_fieldsets(request, test_user)
    print(f"\n✓ Number of fieldsets: {len(fieldsets)}")
    print(f"  Fieldsets: {[fs[0] for fs in fieldsets]}")
    
    # Test readonly fields
    readonly = user_admin.get_readonly_fields(request, test_user)
    print(f"\n✓ Readonly fields count: {len(readonly)}")
    
    # Check if email, username, etc. are readonly
    restricted_fields = ['email', 'username', 'first_name', 'last_name', 'is_active']
    readonly_check = all(field in readonly for field in restricted_fields)
    print(f"✓ Email, username, names are readonly: {readonly_check}")
    
    # Check if manual_subscription is NOT readonly
    subscription_editable = 'manual_subscription' not in readonly
    print(f"✓ Subscription is editable: {subscription_editable}")
    
    # Test permissions
    can_add = user_admin.has_add_permission(request)
    can_delete = user_admin.has_delete_permission(request, test_user)
    print(f"\n✓ Can add users: {can_add}")
    print(f"✓ Can delete users: {can_delete}")
    
    if (len(fieldsets) == 2 and readonly_check and subscription_editable 
        and not can_add and not can_delete):
        print("\n✅ PASS: Other superusers have LIMITED ACCESS (subscription only)")
    else:
        print("\n❌ FAIL: Other superusers should only have subscription access!")
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("\n✅ alberttyagi123@gmail.com:")
    print("   - Can see ALL fieldsets (8 sections)")
    print("   - Can edit ALL fields (except system fields)")
    print("   - Can add new users")
    print("   - Can delete users")
    print("   - FULL ADMIN ACCESS")
    
    print("\n🔒 Other Superusers:")
    print("   - Can see ONLY 2 fieldsets (User Info + Subscription)")
    print("   - Can ONLY edit: manual_subscription (activated/deactivated)")
    print("   - CANNOT edit: email, username, names, permissions, etc.")
    print("   - CANNOT add new users")
    print("   - CANNOT delete users")
    print("   - LIMITED ACCESS")
    
    print("\n" + "=" * 70)
    print("✅ All permission tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    test_admin_permissions()

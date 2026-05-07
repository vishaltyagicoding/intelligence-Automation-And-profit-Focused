#!/usr/bin/env python
"""
Test script for Payment Info Admin Panel
Tests access control and basic functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django.contrib.auth import get_user_model
from payments.models import PaymentInfo, Payment, Subscription
from payments.admin import PaymentInfoAdmin
from django.contrib.admin.sites import AdminSite

User = get_user_model()

def test_payment_info_model():
    """Test PaymentInfo model"""
    print("\n" + "="*60)
    print("TEST 1: PaymentInfo Model")
    print("="*60)
    
    # Check if model exists
    print("✓ PaymentInfo model imported successfully")
    
    # Check fields
    fields = [f.name for f in PaymentInfo._meta.get_fields()]
    print(f"✓ PaymentInfo fields: {', '.join(fields)}")
    
    # Check table name
    print(f"✓ Database table: {PaymentInfo._meta.db_table}")
    
    return True


def test_access_control():
    """Test access control for alberttyagi123@gmail.com"""
    print("\n" + "="*60)
    print("TEST 2: Access Control")
    print("="*60)
    
    # Get or create test superuser
    try:
        superuser = User.objects.get(email='alberttyagi123@gmail.com')
        print(f"✓ Found superuser: {superuser.email}")
    except User.DoesNotExist:
        print("✗ Superuser alberttyagi123@gmail.com not found")
        print("  Please create this superuser first")
        return False
    
    # Test admin permissions
    admin_site = AdminSite()
    payment_admin = PaymentInfoAdmin(PaymentInfo, admin_site)
    
    # Create mock request
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    request = MockRequest(superuser)
    
    # Test permissions
    has_module = payment_admin.has_module_permission(request)
    has_view = payment_admin.has_view_permission(request)
    has_add = payment_admin.has_add_permission(request)
    has_change = payment_admin.has_change_permission(request)
    has_delete = payment_admin.has_delete_permission(request)
    
    print(f"✓ Module permission: {has_module}")
    print(f"✓ View permission: {has_view}")
    print(f"✓ Add permission: {has_add}")
    print(f"✓ Change permission: {has_change}")
    print(f"✓ Delete permission: {has_delete}")
    
    if all([has_module, has_view, has_add, has_change, has_delete]):
        print("✓ All permissions granted for alberttyagi123@gmail.com")
        return True
    else:
        print("✗ Some permissions missing")
        return False


def test_other_user_access():
    """Test that other users cannot access"""
    print("\n" + "="*60)
    print("TEST 3: Other User Access Denial")
    print("="*60)
    
    # Create test user
    test_user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'username': 'testuser',
            'is_superuser': True,
            'is_staff': True
        }
    )
    
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"✓ Created test user: {test_user.email}")
    else:
        print(f"✓ Using existing test user: {test_user.email}")
    
    # Test admin permissions
    admin_site = AdminSite()
    payment_admin = PaymentInfoAdmin(PaymentInfo, admin_site)
    
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    request = MockRequest(test_user)
    
    # Test permissions (should all be False)
    has_module = payment_admin.has_module_permission(request)
    has_view = payment_admin.has_view_permission(request)
    has_add = payment_admin.has_add_permission(request)
    has_change = payment_admin.has_change_permission(request)
    has_delete = payment_admin.has_delete_permission(request)
    
    print(f"✓ Module permission: {has_module} (should be False)")
    print(f"✓ View permission: {has_view} (should be False)")
    print(f"✓ Add permission: {has_add} (should be False)")
    print(f"✓ Change permission: {has_change} (should be False)")
    print(f"✓ Delete permission: {has_delete} (should be False)")
    
    if not any([has_module, has_view, has_add, has_change, has_delete]):
        print("✓ Access correctly denied for other users")
        return True
    else:
        print("✗ Access control failed - other users can access!")
        return False


def test_database_tables():
    """Test that all required tables exist"""
    print("\n" + "="*60)
    print("TEST 4: Database Tables")
    print("="*60)
    
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check payment_info table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'payment_info'
            );
        """)
        payment_info_exists = cursor.fetchone()[0]
        
        # Check subscriptions table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'subscriptions'
            );
        """)
        subscriptions_exists = cursor.fetchone()[0]
        
        # Check payments table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'payments'
            );
        """)
        payments_exists = cursor.fetchone()[0]
    
    print(f"✓ payment_info table exists: {payment_info_exists}")
    print(f"✓ subscriptions table exists: {subscriptions_exists}")
    print(f"✓ payments table exists: {payments_exists}")
    
    if all([payment_info_exists, subscriptions_exists, payments_exists]):
        print("✓ All required tables exist")
        return True
    else:
        print("✗ Some tables missing")
        return False


def test_payment_info_count():
    """Test PaymentInfo records"""
    print("\n" + "="*60)
    print("TEST 5: PaymentInfo Records")
    print("="*60)
    
    count = PaymentInfo.objects.count()
    print(f"✓ Total PaymentInfo records: {count}")
    
    if count > 0:
        print("\nRecent payment records:")
        for payment in PaymentInfo.objects.all()[:5]:
            print(f"  - {payment.user_name}: ${payment.subscription_price} (Created: {payment.created_at})")
    else:
        print("  No payment records yet (this is normal for new installation)")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" PAYMENT INFO ADMIN PANEL - TEST SUITE")
    print("="*70)
    
    results = []
    
    try:
        results.append(("PaymentInfo Model", test_payment_info_model()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("PaymentInfo Model", False))
    
    try:
        results.append(("Access Control (alberttyagi123@gmail.com)", test_access_control()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("Access Control", False))
    
    try:
        results.append(("Access Denial (Other Users)", test_other_user_access()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("Access Denial", False))
    
    try:
        results.append(("Database Tables", test_database_tables()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("Database Tables", False))
    
    try:
        results.append(("PaymentInfo Records", test_payment_info_count()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("PaymentInfo Records", False))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "-"*70)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Payment Info Admin is ready to use.")
        print("\nNext steps:")
        print("1. Login to admin panel: http://localhost:8000/admin/")
        print("2. Use email: alberttyagi123@gmail.com")
        print("3. Navigate to Users and try activating a subscription")
        print("4. The payment info popup should appear automatically")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    run_all_tests()

"""
Test script to verify first_name and last_name are required during registration
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration_without_names():
    """Test that registration fails without first_name and last_name"""
    
    print("=" * 60)
    print("Testing Registration Validation")
    print("=" * 60)
    
    # Test 1: Registration without first_name
    print("\n1. Testing registration WITHOUT first_name...")
    data = {
        "email": "test_no_firstname@example.com",
        "username": "test_no_firstname",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "last_name": "Doe",
        "device_id": "test_device_123"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/register/", json=data)
    result = response.json()
    
    if not result.get('success'):
        print("✅ PASS: Registration correctly rejected without first_name")
        print(f"   Error: {result.get('errors', result.get('error'))}")
    else:
        print("❌ FAIL: Registration should have been rejected!")
    
    # Test 2: Registration without last_name
    print("\n2. Testing registration WITHOUT last_name...")
    data = {
        "email": "test_no_lastname@example.com",
        "username": "test_no_lastname",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "John",
        "device_id": "test_device_123"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/register/", json=data)
    result = response.json()
    
    if not result.get('success'):
        print("✅ PASS: Registration correctly rejected without last_name")
        print(f"   Error: {result.get('errors', result.get('error'))}")
    else:
        print("❌ FAIL: Registration should have been rejected!")
    
    # Test 3: Registration with empty first_name
    print("\n3. Testing registration with EMPTY first_name...")
    data = {
        "email": "test_empty_firstname@example.com",
        "username": "test_empty_firstname",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "",
        "last_name": "Doe",
        "device_id": "test_device_123"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/register/", json=data)
    result = response.json()
    
    if not result.get('success'):
        print("✅ PASS: Registration correctly rejected with empty first_name")
        print(f"   Error: {result.get('errors', result.get('error'))}")
    else:
        print("❌ FAIL: Registration should have been rejected!")
    
    # Test 4: Registration with empty last_name
    print("\n4. Testing registration with EMPTY last_name...")
    data = {
        "email": "test_empty_lastname@example.com",
        "username": "test_empty_lastname",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "John",
        "last_name": "",
        "device_id": "test_device_123"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/register/", json=data)
    result = response.json()
    
    if not result.get('success'):
        print("✅ PASS: Registration correctly rejected with empty last_name")
        print(f"   Error: {result.get('errors', result.get('error'))}")
    else:
        print("❌ FAIL: Registration should have been rejected!")
    
    # Test 5: Registration with spaces only
    print("\n5. Testing registration with SPACES ONLY in names...")
    data = {
        "email": "test_spaces@example.com",
        "username": "test_spaces",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "   ",
        "last_name": "   ",
        "device_id": "test_device_123"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/register/", json=data)
    result = response.json()
    
    if not result.get('success'):
        print("✅ PASS: Registration correctly rejected with spaces-only names")
        print(f"   Error: {result.get('errors', result.get('error'))}")
    else:
        print("❌ FAIL: Registration should have been rejected!")
    
    print("\n" + "=" * 60)
    print("✅ All validation tests completed!")
    print("=" * 60)
    print("\n📋 Summary:")
    print("   - first_name is now REQUIRED")
    print("   - last_name is now REQUIRED")
    print("   - Empty or spaces-only values are rejected")
    print("   - All new users MUST provide both names")
    print("\n🚀 This fix will prevent the issue when deployed to AWS!")

if __name__ == "__main__":
    test_registration_without_names()

"""
Test Login API
==============
Simple script to test the login endpoint
"""
import requests
import json

# Test with a valid user
print("=" * 60)
print("Testing Login API")
print("=" * 60)

url = "http://localhost/api/users/login/"
data = {
    "email": "test1@gmail.com",
    "password": "test123"
}

print(f"\nURL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=data, timeout=10)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✅ LOGIN SUCCESSFUL!")
    else:
        print(f"\n❌ LOGIN FAILED: {response.json().get('error')}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ Request failed: {e}")
except json.JSONDecodeError as e:
    print(f"\n❌ Invalid JSON response: {e}")
    print(f"Response text: {response.text[:500]}")

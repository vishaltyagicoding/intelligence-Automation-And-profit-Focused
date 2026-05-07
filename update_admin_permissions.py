"""
Update all admin files to give pythonbyvishal@gmail.com full access
"""
import os
import re

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

# Old pattern to replace
old_pattern = r"request\.user\.is_superuser and request\.user\.email == 'alberttyagi123@gmail\.com'"

# New pattern
new_pattern = "request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']"

print("=" * 70)
print("Updating Admin Permissions")
print("=" * 70)

for file_path in admin_files:
    if not os.path.exists(file_path):
        print(f"\n❌ File not found: {file_path}")
        continue
    
    print(f"\n📝 Processing: {file_path}")
    
    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count occurrences
    count = len(re.findall(old_pattern, content))
    
    if count == 0:
        print(f"   ⚠️  No matches found - skipping")
        continue
    
    # Replace all occurrences
    new_content = re.sub(old_pattern, new_pattern, content)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"   ✅ Updated {count} permission check(s)")

print("\n" + "=" * 70)
print("✅ All admin files updated successfully!")
print("=" * 70)
print("\n📋 Summary:")
print("   - alberttyagi123@gmail.com: Full access")
print("   - pythonbyvishal@gmail.com: Full access")
print("   - All other superusers: Limited access (subscription only)")
print("\n" + "=" * 70)

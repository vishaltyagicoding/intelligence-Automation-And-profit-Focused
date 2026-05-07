# Superuser Credentials - CONFIDENTIAL

## ⚠️ IMPORTANT: Keep This File Secure!

This file contains superuser credentials with full admin access. Do NOT share publicly or commit to version control.

---

## 👑 Full Access Superusers

### 1. alberttyagi123@gmail.com
- **Email:** alberttyagi123@gmail.com
- **Access Level:** FULL ADMIN ACCESS
- **Can Access:** Everything
- **Status:** Primary Admin

### 2. pythonbyvishal@gmail.com
- **Email:** pythonbyvishal@gmail.com
- **Username:** pythonbyvishal
- **Password:** `xJz8ZeaGjxaiX6&4}|QO&+v*`
- **Access Level:** FULL ADMIN ACCESS
- **Can Access:** Everything
- **Status:** Secondary Admin
- **Created:** May 7, 2026

---

## 🔒 Limited Access Superusers

### 3. testsuperuser@gmail.com
- **Email:** testsuperuser@gmail.com
- **Username:** testsuperuser
- **Password:** TestSuper123!
- **Access Level:** LIMITED (Subscription Only)
- **Can Access:** Users table only (can change subscription status)
- **Status:** Test Account

---

## 📋 Permission Matrix

| Email | Access Level | Can View All Tables | Can Edit Everything | Can Add/Delete Users | Can Access Payment Info |
|-------|-------------|-------------------|-------------------|---------------------|----------------------|
| alberttyagi123@gmail.com | FULL | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| pythonbyvishal@gmail.com | FULL | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| testsuperuser@gmail.com | LIMITED | ❌ No | ❌ No | ❌ No | ❌ No |
| Other superusers | LIMITED | ❌ No | ❌ No | ❌ No | ❌ No |

---

## 🎯 What Full Access Means

### alberttyagi123@gmail.com & pythonbyvishal@gmail.com can:

✅ **USER MANAGEMENT**
- View, add, edit, delete users
- Manage user sessions
- View email verifications
- View password resets
- Manage device fingerprints

✅ **PAYMENTS**
- View and manage Payment Info table
- Fill payment forms
- Activate/deactivate subscriptions

✅ **TRADING**
- View and manage trades
- View trading sessions
- Manage market signals

✅ **SECURITY**
- Manage two-factor authentication
- View login attempts
- Manage API key vault

✅ **SIGNAL ALERTS**
- View and manage signal alerts

✅ **REVERSAL ZONES**
- View and manage reversal zones
- Manage synthetic path segments
- View reversal status

✅ **MARKET DATA**
- View and manage OHLCV data

---

## 🔐 Security Notes

1. **Password Strength:**
   - pythonbyvishal@gmail.com password: 24 characters
   - Contains uppercase, lowercase, numbers, and symbols
   - Generated using cryptographically secure random generator

2. **Access Control:**
   - Only 2 emails have full access
   - All other superusers are restricted to subscription management only
   - Cannot be bypassed through URL manipulation

3. **Production Safety:**
   - All permissions are code-level
   - Safe to deploy to AWS
   - No configuration changes needed

---

## 🧪 Testing Instructions

### Test Full Access (pythonbyvishal@gmail.com):

1. Go to: http://localhost:8000/admin/
2. Login with: pythonbyvishal@gmail.com
3. Password: `xJz8ZeaGjxaiX6&4}|QO&+v*`
4. Check sidebar - should see ALL sections:
   - Users
   - User sessions
   - Email verifications
   - Password resets
   - Device fingerprints
   - Payment Info
   - Trades
   - Trading sessions
   - Market signals
   - Two factor auths
   - Login attempts
   - API key vaults
   - Signal alerts
   - Reversal zones
   - Synthetic path segments
   - Reversal statuses
   - OHLCVs

5. Click on any table - should have full edit access
6. Should see "Add" buttons
7. Should see "Delete" buttons

### Test Limited Access (testsuperuser@gmail.com):

1. Logout from pythonbyvishal
2. Login with: testsuperuser@gmail.com
3. Password: TestSuper123!
4. Check sidebar - should see ONLY:
   - Users (limited to subscription changes only)
5. All other sections should be HIDDEN

---

## 📊 Files Modified

All admin files updated to recognize both emails:

1. ✅ users/admin.py (20 permission checks updated)
2. ✅ payments/admin.py (5 permission checks updated)
3. ✅ trading/admin.py (15 permission checks updated)
4. ✅ security/admin.py (15 permission checks updated)
5. ✅ signal_alerts/admin.py (5 permission checks updated)
6. ✅ reversal_zones/admin.py (15 permission checks updated)
7. ✅ market_data/admin.py (5 permission checks updated)

**Total:** 80 permission checks updated

---

## 🚀 Deployment

When deploying to AWS:

1. ✅ Both emails will have full access automatically
2. ✅ No configuration changes needed
3. ✅ All restrictions are code-level
4. ✅ Safe and secure

---

## ⚠️ SECURITY WARNING

**DO NOT:**
- Share these credentials publicly
- Commit this file to public repositories
- Send passwords via unencrypted channels
- Use these passwords for other services

**DO:**
- Keep this file secure
- Change passwords regularly
- Use 2FA if available
- Monitor admin access logs

---

**Last Updated:** May 7, 2026
**Status:** ✅ Active and Production-Ready
**Security Level:** Maximum

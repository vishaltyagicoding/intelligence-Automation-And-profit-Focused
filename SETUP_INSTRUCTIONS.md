# 🚀 Setup Instructions - Email Verification & Password Reset

## What's Been Implemented

### ✅ Backend (100% Complete)
1. **Email Verification with OTP**
   - Users must verify email before account creation
   - 6-digit OTP sent via email
   - 10-minute expiration
   - Max 5 attempts

2. **Password Reset with OTP**
   - Forgot password functionality
   - OTP sent to email
   - Secure password reset flow

3. **Email Sending**
   - Gmail SMTP configured
   - Beautiful HTML emails
   - OTP verification emails
   - Welcome emails
   - Password reset emails

### ✅ Frontend (100% Complete)
1. **Pages Created**
   - `/verify-email` - Email verification with OTP
   - `/forgot-password` - Request password reset
   - `/reset-password` - Reset password with OTP
   - Updated `/login` - Added "Forgot Password?" link

---

## 🔧 Steps to Make Everything Work

### Step 1: Run Database Migrations

```bash
# Create migrations for new models
python manage.py makemigrations users

# Apply migrations
python manage.py migrate
```

This will create:
- `email_verifications` table
- `password_resets` table

### Step 2: Rebuild Backend Container

```bash
# Stop backend
docker-compose stop django celery_worker celery_beat

# Rebuild backend (to install django-otp)
docker-compose build django

# Start backend
docker-compose up -d django celery_worker celery_beat
```

### Step 3: Rebuild Frontend Container

```bash
# Stop frontend
docker-compose stop frontend

# Rebuild frontend
docker-compose build frontend

# Start frontend
docker-compose up -d frontend
```

### Step 4: Clear Browser Cache

Press `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac) to hard refresh

---

## 📧 Email Configuration

Already configured in `.env`:
```
EMAIL_HOST_USER=alberttyagi123@gmail.com
EMAIL_HOST_PASSWORD=vjil mzto oxjg exzg
```

**Note**: This is a Gmail App Password, not your regular Gmail password.

---

## 🧪 Testing the Features

### Test Email Verification:

1. Go to `http://localhost/register`
2. Fill in the registration form
3. Click "Start 3-Day Free Trial"
4. Check email for 6-digit OTP
5. Enter OTP on verification page
6. Account created and logged in automatically

### Test Forgot Password:

1. Go to `http://localhost/login`
2. Click "Forgot Password?"
3. Enter your email
4. Check email for 6-digit OTP
5. Enter OTP and new password
6. Login with new password

---

## 🎯 User Flow

### Registration Flow:
```
Register Page
    ↓
Enter Details (email, username, password, etc.)
    ↓
Click "Start 3-Day Free Trial"
    ↓
OTP sent to email (user NOT created yet)
    ↓
Verify Email Page
    ↓
Enter 6-digit OTP
    ↓
User created in database
    ↓
Welcome email sent
    ↓
Auto-login and redirect to Dashboard
```

### Password Reset Flow:
```
Login Page
    ↓
Click "Forgot Password?"
    ↓
Enter Email
    ↓
OTP sent to email
    ↓
Reset Password Page
    ↓
Enter 6-digit OTP
    ↓
OTP verified
    ↓
Enter New Password
    ↓
Password reset successful
    ↓
Redirect to Login
```

---

## 📁 Files Modified/Created

### Backend:
- ✅ `users/models.py` - Added EmailVerification & PasswordReset models
- ✅ `users/views.py` - Added all OTP endpoints
- ✅ `users/urls.py` - Added new routes
- ✅ `users/admin.py` - Registered new models
- ✅ `users/email_utils.py` - Email sending functions
- ✅ `neuraltrade/settings.py` - Email configuration
- ✅ `.env` - Email credentials
- ✅ `requirements.txt` - Added django-otp

### Frontend:
- ✅ `app/verify-email/page.tsx` - Email verification page
- ✅ `app/forgot-password/page.tsx` - Forgot password page
- ✅ `app/reset-password/page.tsx` - Reset password page
- ✅ `app/login/page.tsx` - Added "Forgot Password?" link

---

## 🔍 Troubleshooting

### Issue: Emails not sending

**Check:**
1. Email credentials in `.env` are correct
2. Gmail App Password is valid (not regular password)
3. Backend logs: `docker-compose logs django`

**Solution:**
```bash
# Test email sending
docker-compose exec django python manage.py shell
>>> from users.email_utils import send_otp_email
>>> send_otp_email('test@example.com', '123456', 'testuser')
```

### Issue: Migration errors

**Solution:**
```bash
# Delete old migrations (if needed)
docker-compose exec django rm users/migrations/000*.py

# Create fresh migrations
docker-compose exec django python manage.py makemigrations users
docker-compose exec django python manage.py migrate
```

### Issue: Frontend not showing new pages

**Solution:**
```bash
# Clear Next.js cache
docker-compose exec frontend rm -rf .next

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Clear browser cache
# Press Ctrl + Shift + R
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Backend migrations applied successfully
- [ ] Backend container running without errors
- [ ] Frontend container running without errors
- [ ] Can access `/register` page
- [ ] Can access `/login` page
- [ ] Can see "Forgot Password?" link on login page
- [ ] Can access `/forgot-password` page
- [ ] Email sending works (check spam folder)
- [ ] OTP verification works
- [ ] User account created after email verification
- [ ] Password reset works

---

## 🎉 Success!

Once all steps are complete, you'll have:

✅ **Email Verification**
- Users must verify email before account creation
- No fake accounts in database
- Professional OTP emails

✅ **Password Reset**
- Secure forgot password flow
- OTP-based verification
- Users can reset their own passwords

✅ **Professional UX**
- Beautiful email templates
- Smooth user flows
- Clear error messages
- Auto-redirects

---

## 📞 Support

If you encounter any issues:

1. Check backend logs: `docker-compose logs django`
2. Check frontend logs: `docker-compose logs frontend`
3. Check email logs in backend
4. Verify email credentials in `.env`

---

**Ready to test! 🚀**

# Users App Documentation

## Overview
The `users` app handles user authentication, registration, email verification, password reset, subscription management, and user profiles.

## App Structure
```
users/
├── __init__.py
├── models.py              # UserProfile model
├── serializers.py         # User and profile serializers
├── views.py               # Auth API endpoints
├── urls.py                # URL routing
├── admin.py               # Django admin
└── tests.py               # Unit tests
```

## Models

### User (Django Built-in)
Extended from Django's `AbstractUser`.

```python
# Django's default User model
- id: AutoField
- username: CharField(150, unique)
- email: EmailField(unique)
- password: CharField(128, hashed)
- first_name: CharField(150)
- last_name: CharField(150)
- is_active: BooleanField
- is_staff: BooleanField
- is_superuser: BooleanField
- date_joined: DateTimeField
- last_login: DateTimeField
```

### UserProfile
Extended user information and subscription management.

```python
class UserProfile(models.Model):
    user = OneToOneField(User, on_delete=CASCADE)
    phone = CharField(20, blank=True)
    country = CharField(100, blank=True)
    trial_start = DateTimeField(auto_now_add=True)
    trial_end = DateTimeField
    manual_subscription = CharField(20, default='deactivated')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    @property
    def is_trial_active(self):
        return timezone.now() < self.trial_end

    @property
    def subscription_status(self):
        return {
            'is_active': self.manual_subscription == 'activated' or self.is_trial_active,
            'type': 'manual' if self.manual_subscription == 'activated' else 'trial',
            'trial_end': self.trial_end,
            'days_remaining': (self.trial_end - timezone.now()).days
        }
```

## API Endpoints

### 1. Register
**Endpoint**: `POST /api/auth/register/`

**Request**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response**:
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "token": "abc123...",
  "message": "Registration successful. Please verify your email."
}
```

**Process**:
1. Validate input data
2. Check if email/username already exists
3. Hash password
4. Create User and UserProfile
5. Set trial_end = now + 3 days
6. Generate auth token
7. Send verification email
8. Return user data and token

### 2. Login
**Endpoint**: `POST /api/auth/login/`

**Request**:
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response**:
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "subscription_status": {
      "is_active": true,
      "type": "trial",
      "trial_end": "2026-05-14T12:00:00Z",
      "days_remaining": 3
    }
  }
}
```

**Process**:
1. Validate email and password
2. Authenticate user
3. Generate/retrieve auth token
4. Return token and user data with subscription status

### 3. Logout
**Endpoint**: `POST /api/auth/logout/`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "message": "Logged out successfully"
}
```

**Process**:
1. Verify token
2. Delete token from database
3. Return success message

### 4. Get Current User
**Endpoint**: `GET /api/auth/user/`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "subscription_status": {
    "is_active": true,
    "type": "trial",
    "trial_end": "2026-05-14T12:00:00Z",
    "days_remaining": 3
  }
}
```

### 5. Verify Email
**Endpoint**: `POST /api/auth/verify-email/`

**Request**:
```json
{
  "token": "verification-token-here"
}
```

**Response**:
```json
{
  "message": "Email verified successfully"
}
```

### 6. Forgot Password
**Endpoint**: `POST /api/auth/forgot-password/`

**Request**:
```json
{
  "email": "john@example.com"
}
```

**Response**:
```json
{
  "message": "Password reset email sent"
}
```

**Process**:
1. Check if email exists
2. Generate reset token
3. Send reset email with link
4. Return success message

### 7. Reset Password
**Endpoint**: `POST /api/auth/reset-password/`

**Request**:
```json
{
  "token": "reset-token-here",
  "new_password": "NewSecurePass123!"
}
```

**Response**:
```json
{
  "message": "Password reset successfully"
}
```

## Subscription Management

### Trial Period
- **Duration**: 3 days
- **Starts**: Automatically on registration
- **Ends**: 3 days after registration
- **Access**: Full access to all features

### Manual Subscription
- **Activation**: Admin sets `manual_subscription = 'activated'`
- **Deactivation**: Admin sets `manual_subscription = 'deactivated'`
- **Access**: Full access when activated

### Subscription Check
```python
def is_subscription_active(user):
    profile = user.userprofile
    return (
        profile.manual_subscription == 'activated' or
        profile.is_trial_active
    )
```

### Frontend Protection
```typescript
useEffect(() => {
  if (!loading && isAuthenticated && user) {
    const sub = user.subscription_status;
    if (sub && !sub.is_active && user.manual_subscription !== 'activated') {
      router.push('/subscription');
    }
  }
}, [isAuthenticated, loading, user]);
```

## Admin Operations

### Activate User Subscription
1. Login to Django admin: `https://smartriskfx.com/admin/`
2. Navigate to Users → User profiles
3. Find user's profile
4. Set `manual_subscription` to "activated"
5. Save

### Deactivate User Subscription
1. Find user's profile in admin
2. Set `manual_subscription` to "deactivated"
3. Save

### View User Details
```bash
sudo docker-compose exec django python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(email='john@example.com')
>>> print(user.userprofile.subscription_status)
```

## Email Templates

### Verification Email
```
Subject: Verify your SmartRisk account

Hi {first_name},

Welcome to SmartRisk! Please verify your email address by clicking the link below:

{verification_link}

Your 3-day trial has started. Enjoy full access to all features!

Best regards,
SmartRisk Team
```

### Password Reset Email
```
Subject: Reset your SmartRisk password

Hi {first_name},

We received a request to reset your password. Click the link below to reset:

{reset_link}

If you didn't request this, please ignore this email.

Best regards,
SmartRisk Team
```

### Trial Ending Email
```
Subject: Your SmartRisk trial is ending soon

Hi {first_name},

Your 3-day trial will end on {trial_end_date}.

To continue using SmartRisk, please contact us at smarttriskfx@gmail.com

Best regards,
SmartRisk Team
```

## Authentication Flow

### Registration Flow
```
User submits form
    ↓
Validate data
    ↓
Create User + UserProfile
    ↓
Set trial_end = now + 3 days
    ↓
Generate auth token
    ↓
Send verification email
    ↓
Return token + user data
    ↓
Frontend stores token in localStorage
    ↓
Redirect to dashboard
```

### Login Flow
```
User submits credentials
    ↓
Authenticate user
    ↓
Check subscription status
    ↓
Generate/retrieve token
    ↓
Return token + user data
    ↓
Frontend stores token
    ↓
Check subscription status
    ↓
If inactive → redirect to /subscription
    ↓
If active → redirect to /dashboard
```

## Token Management

### Token Storage
- **Frontend**: localStorage (`access_token`)
- **Backend**: Database (DRF Token model)

### Token Usage
```typescript
// Frontend
const token = localStorage.getItem('access_token');
const response = await fetch('/api/endpoint/', {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
```

### Token Validation
```python
# Backend
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    user = request.user
    # User is authenticated
```

## Security

### Password Hashing
Django uses PBKDF2 with SHA256 by default.

### Password Validation
- Minimum 8 characters
- Must contain letters and numbers
- Cannot be too similar to username/email
- Cannot be a common password

### CSRF Protection
- Enabled for all POST requests
- Token included in forms
- Verified on backend

### Rate Limiting
Not currently implemented. Future enhancement.

## Testing

### Test Registration
```bash
curl -X POST https://smartriskfx.com/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Test123!"}'
```

### Test Login
```bash
curl -X POST https://smartriskfx.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

### Test Protected Endpoint
```bash
curl https://smartriskfx.com/api/auth/user/ \
  -H "Authorization: Bearer <token>"
```

## Common Issues

### 1. Login Not Working
**Cause**: Token name mismatch
**Solution**: Use `access_token` (not `auth_token`)

### 2. Subscription Check Failing
**Cause**: Profile not created
**Solution**: Ensure UserProfile is created on registration

### 3. Email Not Sending
**Cause**: Gmail app password incorrect
**Solution**: Generate new app password

### 4. Trial Not Activating
**Cause**: trial_end not set correctly
**Solution**: Check UserProfile creation in registration view

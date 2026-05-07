# Payment Info Admin Panel - Complete Guide

## Overview
This feature allows the superuser (alberttyagi123@gmail.com) to collect payment information when activating user subscriptions through the Django admin panel.

## Features Implemented

### 1. Payment Info Table (`payment_info`)
Created a new database table with the following columns:
- **user** (ForeignKey): Links to the User table
- **user_name** (CharField): Username from User table (auto-filled)
- **subscription_price** (DecimalField): Subscription price (numeric only, validated)
- **payment_valid_image** (ImageField): Payment proof image upload
- **created_at** (DateTimeField): Timestamp when record was created
- **created_by** (ForeignKey): Superuser who created the record

### 2. Access Control
- **ONLY** alberttyagi123@gmail.com can access the Payment Info admin
- All admin permissions (view, add, change, delete) are restricted to this email
- Other users (including other superusers) cannot see or access this module

### 3. Subscription Activation Workflow

#### Step-by-Step Process:
1. **Login** as alberttyagi123@gmail.com superuser
2. **Navigate** to Users admin panel
3. **Select** a user to activate
4. **Change** `manual_subscription` from "deactivated" to "activated"
5. **Click** "Save" button
6. **Popup appears** automatically requesting payment information
7. **Fill in** the payment form:
   - User Name (pre-filled with username)
   - Subscription Price (numeric only)
   - Payment Valid Image (upload from device)
8. **Click** "Save & Activate Subscription"
9. **System validates** and creates payment record
10. **User subscription** is activated automatically

### 4. Form Validation

#### User Name Validation:
- Must exist in User table
- Error message: "User not valid." if username doesn't exist

#### Subscription Price Validation:
- Only numeric values allowed
- Must be greater than 0
- Accepts decimal values (e.g., 99.99)

#### Payment Image Validation:
- Only image files allowed (JPG, PNG, GIF, BMP, WEBP)
- Maximum file size: 5MB
- Error message if invalid file type or size

### 5. Image Upload & Preview
- Images stored in: `media/payment_proofs/YYYY/MM/DD/`
- Live preview shown when image is selected
- Image preview available in admin list and detail views

## File Structure

```
payments/
├── models.py              # PaymentInfo, Payment, Subscription, WebhookLog models
├── admin.py               # PaymentInfoAdmin with access control
├── forms.py               # PaymentInfoForm with validation
└── migrations/
    └── 0003_*.py          # Migration for PaymentInfo table

users/
└── admin.py               # UserAdmin with payment workflow integration

templates/
└── admin/
    └── payment_info_popup.html  # Beautiful popup form template
```

## Database Schema

### payment_info Table
```sql
CREATE TABLE payment_info (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_user(id),
    user_name VARCHAR(255) NOT NULL,
    subscription_price DECIMAL(10, 2) NOT NULL CHECK (subscription_price > 0),
    payment_valid_image VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users_user(id)
);
```

## Admin Panel Features

### Payment Info Admin
- **List Display**: User Name, Subscription Price, Payment Image Preview, Created At, Created By
- **Search**: By user name, email, username
- **Filters**: By creation date
- **Image Preview**: Thumbnail in list view, full preview in detail view
- **Access Control**: Only alberttyagi123@gmail.com

### User Admin Integration
- **Subscription Status Display**: Color-coded (Green ✓ for activated, Red ✗ for deactivated)
- **Payment Workflow**: Automatic popup when activating subscription
- **Custom URL**: `/admin/users/user/<id>/payment-info/`
- **Response Interception**: Detects subscription activation and redirects to popup

## Security Features

1. **Email-Based Access Control**: Only alberttyagi123@gmail.com
2. **Permission Checks**: All CRUD operations restricted
3. **Form Validation**: Server-side validation for all fields
4. **File Type Validation**: Only image files accepted
5. **File Size Limit**: Maximum 5MB per image
6. **CSRF Protection**: Django CSRF tokens on all forms

## Usage Examples

### Example 1: Activate New User Subscription
```
1. User registers: john@example.com
2. Admin logs in as alberttyagi123@gmail.com
3. Goes to Users → john@example.com
4. Changes manual_subscription to "activated"
5. Clicks Save
6. Popup appears
7. Fills:
   - User Name: john@example.com
   - Subscription Price: 99.99
   - Uploads payment screenshot
8. Clicks "Save & Activate Subscription"
9. Success! User is now activated
```

### Example 2: View Payment History
```
1. Admin logs in as alberttyagi123@gmail.com
2. Goes to Payment Info admin
3. Sees all payment records with:
   - User names
   - Prices paid
   - Payment proof images
   - Creation dates
4. Can search by username or email
5. Can filter by date
```

## Error Handling

### Common Errors and Solutions:

#### "User not valid"
- **Cause**: Username doesn't exist in database
- **Solution**: Check spelling, ensure user is registered

#### "Subscription price must be greater than 0"
- **Cause**: Price is 0 or negative
- **Solution**: Enter valid positive number

#### "Only image files are allowed"
- **Cause**: Uploaded file is not an image
- **Solution**: Upload JPG, PNG, GIF, BMP, or WEBP file

#### "Image file size must be less than 5MB"
- **Cause**: Image file too large
- **Solution**: Compress image or use smaller file

#### "Only alberttyagi123@gmail.com can access this feature"
- **Cause**: Logged in as different user
- **Solution**: Login as alberttyagi123@gmail.com

## Testing Checklist

- [x] PaymentInfo model created
- [x] Database migration created and applied
- [x] PaymentInfoAdmin registered with access control
- [x] PaymentInfoForm with validation
- [x] Popup template created with styling
- [x] UserAdmin integration with payment workflow
- [x] Access control for alberttyagi123@gmail.com only
- [x] Form validation (username, price, image)
- [x] Image upload and preview
- [x] Subscription activation on save
- [x] MEDIA_ROOT and MEDIA_URL configured
- [x] Pillow installed for ImageField

## Next Steps for Testing

1. **Restart Django** to load new admin configuration:
   ```bash
   docker-compose restart django
   ```

2. **Login to Admin Panel**:
   - URL: http://localhost:8000/admin/
   - Email: alberttyagi123@gmail.com
   - Password: [your superuser password]

3. **Test Payment Info Access**:
   - Should see "Payment Info" in admin sidebar
   - Other users should NOT see it

4. **Test Subscription Activation**:
   - Go to Users admin
   - Select a user with deactivated subscription
   - Change to "activated"
   - Click Save
   - Popup should appear
   - Fill form and submit
   - Verify user is activated

5. **Test Validation**:
   - Try invalid username → Should show "User not valid"
   - Try negative price → Should show error
   - Try non-image file → Should show error
   - Try large file (>5MB) → Should show error

## Maintenance

### Viewing Payment Records
```python
# Django shell
from payments.models import PaymentInfo

# Get all payment records
payments = PaymentInfo.objects.all()

# Get payments for specific user
user_payments = PaymentInfo.objects.filter(user__email='john@example.com')

# Get recent payments
recent = PaymentInfo.objects.order_by('-created_at')[:10]
```

### Backup Payment Images
```bash
# Backup payment proof images
tar -czf payment_proofs_backup.tar.gz media/payment_proofs/
```

## Production Considerations

1. **Image Storage**: Consider using AWS S3 or similar for production
2. **Image Optimization**: Compress images before storage
3. **Backup Strategy**: Regular backups of payment_info table and images
4. **Audit Trail**: All records include created_by and created_at
5. **Privacy**: Payment images contain sensitive information - secure access

## Support

For issues or questions:
- Email: alberttyagi123@gmail.com
- Email: smarttriskfx@gmail.com

---

**Status**: ✅ Fully Implemented and Ready for Testing
**Last Updated**: May 6, 2026
**Version**: 1.0.0

# Create Superuser with Full Admin Access - Complete Guide

## 🎯 Quick Start (One Command)

### For AWS or Production:

```bash
# Step 1: Create superuser (interactive - will prompt for password)
python manage.py createfulladmin newadmin@example.com

# Step 2: Grant full admin access
python manage.py grantfulladmin newadmin@example.com

# Step 3: Restart Django
docker-compose restart django
# OR
sudo systemctl restart django
```

That's it! The superuser now has full admin access like alberttyagi123@gmail.com.

---

## 📋 Detailed Instructions

### Method 1: Interactive (Recommended for Production)

```bash
# Create superuser - will prompt for password securely
python manage.py createfulladmin admin@company.com

# Enter password when prompted (hidden input)
Password: ********
Password (again): ********

# Grant full access
python manage.py grantfulladmin admin@company.com

# Restart Django
docker-compose restart django
```

### Method 2: With Username

```bash
# Specify custom username
python manage.py createfulladmin admin@company.com --username companyadmin

# Grant full access
python manage.py grantfulladmin admin@company.com

# Restart
docker-compose restart django
```

### Method 3: Auto-Generated Password

```bash
# Generate strong password automatically
python manage.py createfulladmin admin@company.com --auto-password

# Output will show the generated password - SAVE IT!
# Password: xJz8ZeaGjxaiX6&4}|QO&+v*

# Grant full access
python manage.py grantfulladmin admin@company.com

# Restart
docker-compose restart django
```

### Method 4: With All Options

```bash
# Full command with all options
python manage.py createfulladmin admin@company.com \
  --username companyadmin \
  --first-name John \
  --last-name Doe \
  --auto-password

# Grant full access
python manage.py grantfulladmin admin@company.com

# Restart
docker-compose restart django
```

---

## 🚀 AWS Deployment Commands

### Using Docker on AWS:

```bash
# SSH into your AWS EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Navigate to project directory
cd /path/to/your/project

# Create superuser
docker-compose exec django python manage.py createfulladmin admin@company.com

# Grant full access
docker-compose exec django python manage.py grantfulladmin admin@company.com

# Restart Django
docker-compose restart django
```

### Using Systemd on AWS:

```bash
# SSH into AWS
ssh -i your-key.pem ubuntu@your-ec2-ip

# Activate virtual environment
source /path/to/venv/bin/activate

# Create superuser
python manage.py createfulladmin admin@company.com

# Grant full access
python manage.py grantfulladmin admin@company.com

# Restart Django
sudo systemctl restart django
```

---

## 📊 Command Options

### createfulladmin

```bash
python manage.py createfulladmin <email> [OPTIONS]

Required:
  email                 Email address for the superuser

Optional:
  --username USERNAME   Custom username (default: derived from email)
  --password PASSWORD   Password (not recommended - use interactive mode)
  --first-name NAME     First name
  --last-name NAME      Last name
  --auto-password       Generate strong random password automatically
```

### grantfulladmin

```bash
python manage.py grantfulladmin <email>

Required:
  email                 Email address of existing superuser
```

---

## 🔐 Security Best Practices

### ✅ DO:
- Use interactive password input (most secure)
- Use `--auto-password` for strong random passwords
- Save generated passwords in a secure password manager
- Use unique passwords for each superuser
- Change passwords regularly

### ❌ DON'T:
- Use `--password` flag in production (password visible in command history)
- Share superuser credentials
- Use weak passwords
- Commit passwords to version control

---

## 🧪 Testing

### Test the New Superuser:

```bash
# 1. Create test superuser
python manage.py createfulladmin test@example.com --auto-password

# 2. Grant full access
python manage.py grantfulladmin test@example.com

# 3. Restart Django
docker-compose restart django

# 4. Login to admin panel
# URL: http://your-domain.com/admin/
# Email: test@example.com
# Password: (use the generated password)

# 5. Verify full access:
# - Check sidebar - should see ALL sections
# - Try editing users, trades, payments, etc.
# - Should have "Add" and "Delete" buttons
```

---

## 📋 What Full Access Means

After running both commands, the superuser will have:

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

## 🔄 Revoking Full Access

To revoke full admin access (make superuser limited):

```bash
# Manually remove the email from all admin files
# OR
# Delete the superuser and create a new one without granting full access
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(email='admin@company.com')
>>> user.delete()
```

---

## 🐛 Troubleshooting

### Issue: "User already exists"
```bash
# Solution: Use a different email or delete existing user
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(email='admin@company.com').delete()
>>> exit()
```

### Issue: "Permission denied after granting access"
```bash
# Solution: Restart Django server
docker-compose restart django
# OR
sudo systemctl restart django
```

### Issue: "Command not found"
```bash
# Solution: Make sure you're in the project directory
cd /path/to/your/project

# And virtual environment is activated (if not using Docker)
source venv/bin/activate
```

---

## 📝 Examples

### Example 1: Quick Production Setup

```bash
# Create admin for production
python manage.py createfulladmin admin@smartrisk.com --auto-password

# Output:
# Password: xJz8ZeaGjxaiX6&4}|QO&+v*
# (Save this password!)

# Grant full access
python manage.py grantfulladmin admin@smartrisk.com

# Restart
docker-compose restart django
```

### Example 2: Multiple Admins

```bash
# Create first admin
python manage.py createfulladmin admin1@company.com
python manage.py grantfulladmin admin1@company.com

# Create second admin
python manage.py createfulladmin admin2@company.com
python manage.py grantfulladmin admin2@company.com

# Create third admin
python manage.py createfulladmin admin3@company.com
python manage.py grantfulladmin admin3@company.com

# Restart once
docker-compose restart django
```

### Example 3: AWS EC2 One-Liner

```bash
# SSH and run all commands in one line
ssh -i key.pem ubuntu@ec2-ip "cd /app && docker-compose exec -T django python manage.py createfulladmin admin@company.com --auto-password && docker-compose exec -T django python manage.py grantfulladmin admin@company.com && docker-compose restart django"
```

---

## 🎯 Summary

### Two Simple Commands:

1. **Create superuser:**
   ```bash
   python manage.py createfulladmin <email>
   ```

2. **Grant full access:**
   ```bash
   python manage.py grantfulladmin <email>
   ```

3. **Restart Django:**
   ```bash
   docker-compose restart django
   ```

That's it! The superuser now has full admin access.

---

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Verify Django is running: `docker-compose ps`
3. Check Django logs: `docker-compose logs django`
4. Ensure you restarted Django after granting access

---

**Last Updated:** May 7, 2026
**Status:** ✅ Production-Ready
**Tested:** ✅ Localhost and AWS

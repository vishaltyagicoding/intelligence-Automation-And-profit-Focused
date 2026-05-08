# 🚀 SmartRisk Production Deployment Checklist

## ✅ COMPLETED TASKS

### 1. Code Preparation
- ✅ Removed all ML/AI dependencies from requirements.txt
- ✅ Changed brand name from NeuralTrade to SmartRisk across entire frontend
- ✅ Updated email addresses to alberttyagi123@gmail.com and smarttriskfx@gmail.com
- ✅ Set default timeframe to 15M (not 4H)
- ✅ Hidden signal status for 4H timeframe
- ✅ Increased 1D chart candles to 180 (6 months)
- ✅ Changed signal update frequency to every 15 minutes (not 30)
- ✅ Trial expiration check runs every 1 minute
- ✅ Fixed trial countdown timer and expiration system
- ✅ Added trial_status field to User model
- ✅ Fixed lib/ directory inclusion (was in .gitignore, now included)
- ✅ Fixed Dockerfile script permissions (chmod +x for start_server.sh)
- ✅ Created comprehensive GitHub Actions workflow

### 2. GitHub Actions Workflow
- ✅ Created `.github/workflows/deploy-aws.yml`
- ✅ 19 automated deployment steps configured
- ✅ SSH deployment to EC2 (not ECS/ECR)
- ✅ Automatic Docker build and service startup
- ✅ Database migrations automation
- ✅ Superuser creation automation
- ✅ Celery task configuration automation
- ✅ Health checks for all services
- ✅ Error handling and logging

### 3. Docker Configuration
- ✅ Dockerfile optimized for production
- ✅ Dockerfile.frontend configured
- ✅ docker-compose.yml with 7 services:
  - PostgreSQL (TimescaleDB)
  - Redis
  - Django (Daphne ASGI)
  - Celery Worker
  - Celery Beat
  - Next.js Frontend
  - Nginx (with SSL)
- ✅ Health checks for all services
- ✅ Persistent volumes for data
- ✅ Proper service dependencies

---

## 🔧 WHAT YOU NEED TO DO NOW

### Step 1: Update EC2_HOST Secret in GitHub
You created a NEW EC2 instance, so you need to update the IP address:

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Find **EC2_HOST** secret
4. Click **Update**
5. Enter your NEW EC2 instance IP address (not the old 54.183.119.39)
6. Click **Update secret**

### Step 2: Run Setup Commands on NEW EC2 Instance

**IMPORTANT:** You need to SSH into your NEW EC2 instance and run these commands ONCE:

```bash
# SSH into your NEW EC2 instance
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP

# Copy and paste this entire script:
# ============================================
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker ubuntu

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Django API
sudo ufw allow 8001/tcp  # WebSocket
sudo ufw --force enable

# Create project directory
mkdir -p ~/smartrisk

# Verify installations
echo "=== Docker Version ==="
docker --version
echo "=== Docker Compose Version ==="
docker-compose --version
echo "=== Disk Space ==="
df -h
echo "=== Setup Complete! ==="
# ============================================

# IMPORTANT: After running all commands, logout and login again
exit
```

**After running the script, logout and login again:**
```bash
# Logout
exit

# Login again
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP
```

### Step 3: Verify GitHub Secrets

Make sure ALL 7 secrets are configured in GitHub:

1. **AWS_ACCESS_KEY_ID** - Your AWS access key
2. **AWS_SECRET_ACCESS_KEY** - Your AWS secret key
3. **EC2_HOST** - Your NEW EC2 instance IP address ⚠️ UPDATE THIS!
4. **EC2_SSH_KEY** - Your private SSH key (entire content of .pem file)
5. **DJANGO_SECRET_KEY** - Already generated: `b%jb$1*+ege5^u+kn7q83zs=65e1(6n-txkg--k3#*tvf1e4ex`
6. **EMAIL_HOST_USER** - Your Gmail address for sending emails
7. **EMAIL_HOST_PASSWORD** - Your Gmail app password (not regular password)

### Step 4: Push to GitHub

Once Steps 1-3 are complete:

```bash
# Make sure you're in your project directory
cd /path/to/your/smartrisk/project

# Add all changes
git add .

# Commit
git commit -m "Production ready deployment - SmartRisk v1.0"

# Push to GitHub (this will trigger automatic deployment)
git push origin main
```

### Step 5: Monitor Deployment

1. Go to your GitHub repository
2. Click **Actions** tab
3. Watch the deployment progress
4. All steps should turn green ✅

---

## 🎯 WHAT GITHUB ACTIONS WILL DO AUTOMATICALLY

When you push to GitHub, the workflow will:

1. ✅ Checkout your code
2. ✅ Setup SSH connection to EC2
3. ✅ Stop any running services
4. ✅ Deploy new code to EC2
5. ✅ Configure environment variables
6. ✅ Build Docker images (Django + Frontend)
7. ✅ Start all 7 services
8. ✅ Wait for services to be healthy
9. ✅ Run database migrations
10. ✅ Collect static files
11. ✅ Create superuser accounts:
    - alberttyagi123@gmail.com
    - pythonbyvishal@gmail.com
    - Password: SmartRisk@2026!
12. ✅ Configure Celery Beat tasks:
    - Trial expiration: Every 1 minute
    - Signal updates: Every 15 minutes
13. ✅ Restart Celery services
14. ✅ Run health checks
15. ✅ Show deployment summary

---

## 🔍 VERIFICATION AFTER DEPLOYMENT

Once deployment completes, verify everything works:

### 1. Check Services Status
```bash
ssh ubuntu@YOUR_NEW_EC2_IP
cd ~/smartrisk
sudo docker-compose ps
```

You should see all 7 services running:
- ✅ neuraltrade_db (healthy)
- ✅ neuraltrade_redis (healthy)
- ✅ neuraltrade_django (healthy)
- ✅ neuraltrade_celery_worker (Up)
- ✅ neuraltrade_celery_beat (Up)
- ✅ neuraltrade_frontend (Up)
- ✅ neuraltrade_nginx (Up)

### 2. Check Django Logs
```bash
sudo docker-compose logs django --tail=50
```

Should show:
- ✅ "Starting server with Daphne..."
- ✅ No error messages

### 3. Check Celery Logs
```bash
sudo docker-compose logs celery_beat --tail=30
```

Should show:
- ✅ "Scheduler: Sending due task check-expired-subscriptions"
- ✅ "Scheduler: Sending due task update-all-recent-signals-every-15min"

### 4. Test Application
1. Open browser: `http://YOUR_NEW_EC2_IP:3000`
2. Register a new user
3. Check email for verification
4. Login and check dashboard
5. Verify trial countdown shows "3 days remaining"
6. Check that default timeframe is 15M
7. Switch to 4H timeframe - signal status should be hidden

### 5. Test Admin Panel
1. Open: `http://YOUR_NEW_EC2_IP:8000/admin/`
2. Login with:
   - Email: alberttyagi123@gmail.com
   - Password: SmartRisk@2026!
3. Verify you have full admin access

---

## 🚨 TROUBLESHOOTING

### If Django Service Fails to Start

```bash
# Check Django logs
sudo docker-compose logs django --tail=100

# Try manual start
sudo docker-compose up -d django

# Check if it's running
sudo docker-compose ps django
```

### If Migrations Fail

```bash
# Run migrations manually
sudo docker-compose exec django python manage.py migrate --noinput

# Check migration status
sudo docker-compose exec django python manage.py showmigrations
```

### If Celery Tasks Not Running

```bash
# Check Celery Beat logs
sudo docker-compose logs celery_beat --tail=50

# Restart Celery services
sudo docker-compose restart celery_beat celery_worker
```

### If Frontend Not Loading

```bash
# Check frontend logs
sudo docker-compose logs frontend --tail=50

# Rebuild frontend
sudo docker-compose build frontend
sudo docker-compose up -d frontend
```

---

## 📝 IMPORTANT NOTES

### DO NOT Run These Commands on EC2:
- ❌ `curl "https://..."` - Not needed, GitHub Actions handles everything
- ❌ Manual Docker commands - GitHub Actions handles this
- ❌ Manual migrations - GitHub Actions handles this
- ❌ Manual superuser creation - GitHub Actions handles this

### You ONLY Need to Run:
1. ✅ One-time EC2 setup (Docker, Docker Compose, firewall)
2. ✅ Update EC2_HOST secret in GitHub
3. ✅ `git push origin main`

### After First Deployment:
- Future updates: Just `git push origin main`
- GitHub Actions will automatically deploy everything
- No need to SSH into EC2 anymore

---

## 🎉 SUCCESS INDICATORS

You'll know deployment is successful when:

1. ✅ All GitHub Actions steps are green
2. ✅ All 7 Docker services show "Up" or "healthy"
3. ✅ Frontend loads at `http://YOUR_EC2_IP:3000`
4. ✅ API responds at `http://YOUR_EC2_IP:8000/health/`
5. ✅ Admin panel accessible at `http://YOUR_EC2_IP:8000/admin/`
6. ✅ New user registration works
7. ✅ Email verification works
8. ✅ Trial countdown shows correctly
9. ✅ Dashboard loads with 15M timeframe by default
10. ✅ Celery tasks running (check logs)

---

## 🔐 SECURITY REMINDERS

- ✅ Never commit .env files
- ✅ Never commit .pem files
- ✅ Never commit AWS credentials
- ✅ All secrets stored in GitHub Secrets
- ✅ Firewall configured (UFW)
- ✅ SSL ready (Nginx configured)

---

## 📞 ADMIN CREDENTIALS

**Full Admin Access:**
- Email: alberttyagi123@gmail.com
- Email: pythonbyvishal@gmail.com
- Password: SmartRisk@2026!

**Contact Emails:**
- alberttyagi123@gmail.com
- smarttriskfx@gmail.com

---

## 🎯 NEXT STEPS AFTER SUCCESSFUL DEPLOYMENT

1. Configure domain name (smartriskfx.com) to point to EC2 IP
2. Setup SSL certificate with Let's Encrypt
3. Configure email settings for production
4. Test all features thoroughly
5. Monitor logs for any issues
6. Setup backup strategy for database

---

**Good luck with your deployment! 🚀**

Remember: You've done all the hard work. Now just:
1. Update EC2_HOST secret
2. Run setup commands on EC2 (once)
3. Logout/login
4. Push to GitHub
5. Watch it deploy automatically!

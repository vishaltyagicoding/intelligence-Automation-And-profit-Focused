# ✅ Final Verification Before Deployment

## 🔍 Pre-Deployment Checklist

### 1. Code Changes ✅
- [x] ML dependencies removed from requirements.txt
- [x] Brand name changed to SmartRisk in frontend
- [x] Email addresses updated (alberttyagi123@gmail.com, smarttriskfx@gmail.com)
- [x] Default timeframe set to 15M
- [x] 4H signal status hidden
- [x] 1D chart shows 180 candles
- [x] Signal updates every 15 minutes
- [x] Trial expiration checks every 1 minute
- [x] lib/ directory included (not in .gitignore)
- [x] Dockerfile script permissions fixed

### 2. GitHub Actions Workflow ✅
- [x] File: `.github/workflows/deploy-aws.yml`
- [x] 19 automated steps configured
- [x] SSH deployment to EC2
- [x] Docker build automation
- [x] Service startup automation
- [x] Database migrations automation
- [x] Superuser creation automation
- [x] Celery task configuration
- [x] Health checks for all services

### 3. Docker Configuration ✅
- [x] Dockerfile optimized
- [x] Dockerfile.frontend configured
- [x] docker-compose.yml with 7 services
- [x] Health checks configured
- [x] Persistent volumes configured
- [x] Service dependencies configured

### 4. GitHub Secrets Required ⚠️
You need to verify these 7 secrets are configured:

1. **AWS_ACCESS_KEY_ID** - Your AWS access key
2. **AWS_SECRET_ACCESS_KEY** - Your AWS secret key
3. **EC2_HOST** - ⚠️ **MUST UPDATE WITH NEW EC2 IP!**
4. **EC2_SSH_KEY** - Your private SSH key (entire .pem file)
5. **DJANGO_SECRET_KEY** - Use: `b%jb$1*+ege5^u+kn7q83zs=65e1(6n-txkg--k3#*tvf1e4ex`
6. **EMAIL_HOST_USER** - Your Gmail address
7. **EMAIL_HOST_PASSWORD** - Your Gmail app password

---

## 🎯 What You Need to Do

### Action 1: Update EC2_HOST Secret
**This is CRITICAL - you created a NEW EC2 instance!**

1. Go to GitHub → Your Repository
2. Click **Settings**
3. Click **Secrets and variables** → **Actions**
4. Find **EC2_HOST**
5. Click **Update**
6. Enter your NEW EC2 instance IP address
7. Click **Update secret**

### Action 2: Run EC2 Setup Commands (ONE TIME)

**SSH into your NEW EC2 instance:**
```bash
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP
```

**Copy and paste this entire script:**
```bash
#!/bin/bash
echo "=========================================="
echo "SmartRisk EC2 Setup Script"
echo "=========================================="

# Update system
echo "Step 1/8: Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Docker prerequisites
echo "Step 2/8: Installing Docker prerequisites..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
echo "Step 3/8: Adding Docker GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "Step 4/8: Adding Docker repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
echo "Step 5/8: Installing Docker..."
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
echo "Step 6/8: Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Add user to docker group
echo "Step 7/8: Adding user to docker group..."
sudo usermod -aG docker ubuntu

# Configure firewall
echo "Step 8/8: Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Django API
sudo ufw allow 8001/tcp  # WebSocket
sudo ufw --force enable

# Create project directory
mkdir -p ~/smartrisk

# Verify installations
echo ""
echo "=========================================="
echo "Verification"
echo "=========================================="
echo "Docker Version:"
docker --version
echo ""
echo "Docker Compose Version:"
docker-compose --version
echo ""
echo "Disk Space:"
df -h | grep -E "Filesystem|/$"
echo ""
echo "Memory:"
free -h
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: You MUST logout and login again!"
echo "Run: exit"
echo "Then reconnect: ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP"
echo ""
```

**After running the script:**
```bash
# Logout
exit

# Login again (IMPORTANT!)
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP

# Verify docker works without sudo
docker ps
```

### Action 3: Deploy to GitHub

```bash
# In your local project directory
cd /path/to/your/smartrisk/project

# Check status
git status

# Add all changes
git add .

# Commit
git commit -m "Production ready - SmartRisk v1.0"

# Push (this triggers automatic deployment)
git push origin main
```

---

## 📊 Expected Results

### GitHub Actions Should Show:
1. ✅ Checkout code
2. ✅ Setup SSH key
3. ✅ Check EC2 connection
4. ✅ Stop running services
5. ✅ Deploy code to EC2
6. ✅ Configure environment
7. ✅ Build Docker images
8. ✅ Start services
9. ✅ Wait for services to be ready
10. ✅ Run database migrations
11. ✅ Collect static files
12. ✅ Create superuser
13. ✅ Configure Celery Beat tasks
14. ✅ Restart services
15. ✅ Health checks
16. ✅ Deployment Summary

### On EC2, Services Should Show:
```
NAME                       STATUS
neuraltrade_db             Up (healthy)
neuraltrade_redis          Up (healthy)
neuraltrade_django         Up (healthy)
neuraltrade_celery_worker  Up
neuraltrade_celery_beat    Up
neuraltrade_frontend       Up (healthy)
neuraltrade_nginx          Up
```

---

## 🧪 Testing After Deployment

### 1. Check Services
```bash
ssh ubuntu@YOUR_NEW_EC2_IP
cd ~/smartrisk
sudo docker-compose ps
```

### 2. Check Django Logs
```bash
sudo docker-compose logs django --tail=50
```

Should show:
- ✅ "Starting server with Daphne..."
- ✅ "Listening on TCP address 0.0.0.0:8000"
- ❌ No error messages

### 3. Check Celery Beat
```bash
sudo docker-compose logs celery_beat --tail=30
```

Should show:
- ✅ "Scheduler: Sending due task check-expired-subscriptions"
- ✅ "Scheduler: Sending due task update-all-recent-signals-every-15min"

### 4. Test Frontend
```bash
# From your local machine
curl http://YOUR_NEW_EC2_IP:3000
```

Should return HTML content.

### 5. Test API
```bash
curl http://YOUR_NEW_EC2_IP:8000/health/
```

Should return: `{"status": "healthy"}`

### 6. Test Admin Panel
Open browser: `http://YOUR_NEW_EC2_IP:8000/admin/`
- Login with: alberttyagi123@gmail.com
- Password: SmartRisk@2026!

### 7. Test User Registration
1. Open: `http://YOUR_NEW_EC2_IP:3000`
2. Click Register
3. Fill form and submit
4. Check email for verification
5. Verify trial shows "3 days remaining"

### 8. Test Dashboard
1. Login with new user
2. Check default timeframe is 15M
3. Switch to 4H - signal status should be hidden
4. Switch to 1D - should show 180 candles

---

## 🚨 Common Issues and Solutions

### Issue 1: Django Service Won't Start
**Symptoms:** `docker-compose ps` shows django as "Exit" or "Restarting"

**Solution:**
```bash
# Check logs
sudo docker-compose logs django --tail=100

# Try manual start
sudo docker-compose up -d django

# If still failing, check permissions
sudo docker-compose exec django ls -la /app/scripts/
```

### Issue 2: Migrations Fail
**Symptoms:** Error during "Run database migrations" step

**Solution:**
```bash
# Check database is running
sudo docker-compose ps db

# Run migrations manually
sudo docker-compose exec django python manage.py migrate --noinput

# Check migration status
sudo docker-compose exec django python manage.py showmigrations
```

### Issue 3: Celery Tasks Not Running
**Symptoms:** No scheduled tasks in logs

**Solution:**
```bash
# Check Celery Beat logs
sudo docker-compose logs celery_beat --tail=50

# Restart Celery services
sudo docker-compose restart celery_beat celery_worker

# Verify tasks are configured
sudo docker-compose exec django python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
```

### Issue 4: Frontend Not Loading
**Symptoms:** Cannot access http://YOUR_EC2_IP:3000

**Solution:**
```bash
# Check frontend logs
sudo docker-compose logs frontend --tail=50

# Rebuild frontend
sudo docker-compose build frontend
sudo docker-compose up -d frontend

# Check if port is open
sudo ufw status | grep 3000
```

### Issue 5: SSH Connection Failed
**Symptoms:** GitHub Actions fails at "Check EC2 connection"

**Solution:**
1. Verify EC2_HOST secret has correct IP
2. Verify EC2_SSH_KEY secret has entire .pem file content
3. Check EC2 security group allows SSH (port 22) from GitHub Actions IPs
4. Try manual SSH: `ssh ubuntu@YOUR_EC2_IP`

---

## 📝 Important Notes

### Container Names
The Docker containers use "neuraltrade" prefix (this is correct):
- `neuraltrade_db`
- `neuraltrade_redis`
- `neuraltrade_django`
- `neuraltrade_celery_worker`
- `neuraltrade_celery_beat`
- `neuraltrade_frontend`
- `neuraltrade_nginx`

This is the Django project name and doesn't need to change.

### Brand Name
The brand name "SmartRisk" is used in:
- ✅ Frontend UI (all pages)
- ✅ Email templates
- ✅ Documentation
- ✅ GitHub workflow messages

### Backend Project Name
The backend still uses "neuraltrade" as the Django project name:
- ✅ `neuraltrade/settings.py`
- ✅ `neuraltrade/urls.py`
- ✅ `neuraltrade/asgi.py`
- ✅ Container names

This is correct and doesn't need to change.

---

## ✅ Final Checklist Before Push

- [ ] EC2_HOST secret updated with NEW IP
- [ ] All 7 GitHub secrets configured
- [ ] EC2 setup commands completed
- [ ] Logged out and back in to EC2
- [ ] Verified docker works without sudo: `docker ps`
- [ ] All code changes committed
- [ ] Ready to push to GitHub

---

## 🎉 Success Indicators

You'll know everything worked when:

1. ✅ GitHub Actions workflow completes (all green)
2. ✅ All 7 services show "Up" or "healthy"
3. ✅ Frontend loads at `http://YOUR_EC2_IP:3000`
4. ✅ API responds at `http://YOUR_EC2_IP:8000/health/`
5. ✅ Admin panel works at `http://YOUR_EC2_IP:8000/admin/`
6. ✅ User registration works
7. ✅ Email verification works
8. ✅ Trial countdown shows correctly
9. ✅ Dashboard loads with 15M default
10. ✅ Celery tasks running (check logs)

---

## 🔐 Admin Credentials

**Full Admin Access:**
- Email: alberttyagi123@gmail.com
- Email: pythonbyvishal@gmail.com
- Password: SmartRisk@2026!

**Contact Emails:**
- alberttyagi123@gmail.com
- smarttriskfx@gmail.com

---

## 📞 Support

If you encounter any issues:
1. Check GitHub Actions logs
2. Check EC2 service logs: `sudo docker-compose logs [service-name]`
3. Verify all secrets are configured correctly
4. Ensure EC2 setup was completed and you logged out/in

---

**You're ready to deploy! 🚀**

Remember:
1. Update EC2_HOST secret ⚠️
2. Run EC2 setup (once)
3. Logout/login
4. Push to GitHub
5. Watch it deploy!

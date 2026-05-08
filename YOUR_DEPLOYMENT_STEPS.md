# 🚀 Your Deployment Steps - SmartRisk

## ✅ What You've Already Done

1. ✅ **Created NEW EC2 instance**
   - IP: 54.183.178.141
   
2. ✅ **Updated GitHub Secrets**
   - ✅ EC2_HOST: 54.183.178.141 (updated 1 minute ago)
   - ✅ EC2_SSH_KEY: New key uploaded (updated just now)
   - ✅ AWS_ACCESS_KEY_ID: Configured
   - ✅ AWS_SECRET_ACCESS_KEY: Configured
   - ✅ DJANGO_SECRET_KEY: Configured
   - ✅ EMAIL_HOST_USER: Configured
   - ✅ EMAIL_HOST_PASSWORD: Configured

3. ✅ **Updated Domain DNS**
   - ✅ smartriskfx.com → 54.183.178.141
   - ✅ www.smartriskfx.com → 54.183.178.141

---

## 🎯 What You Need to Do Now

### Step 1: Run Setup Commands on EC2 (5 minutes - ONE TIME)

**SSH into your EC2 instance:**
```bash
ssh -i your-new-key.pem ubuntu@54.183.178.141
```

**Copy and paste this ENTIRE script:**
```bash
#!/bin/bash
echo "=========================================="
echo "SmartRisk EC2 Setup - Starting..."
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
echo "Firewall Status:"
sudo ufw status
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: You MUST logout and login again!"
echo ""
echo "Run these commands:"
echo "  exit"
echo "  ssh -i your-new-key.pem ubuntu@54.183.178.141"
echo "  docker ps"
echo ""
echo "If 'docker ps' works without sudo, you're ready!"
echo "=========================================="
```

**After the script completes, LOGOUT and LOGIN again:**
```bash
# Logout
exit

# Login again (REQUIRED!)
ssh -i your-new-key.pem ubuntu@54.183.178.141

# Verify docker works without sudo
docker ps
```

**Expected output:** Empty list (no containers yet) - this is correct!

If you see the table headers without errors, you're ready! ✅

---

### Step 2: Deploy to GitHub (1 minute)

**On your local machine (in Kiro IDE terminal):**
```bash
# Check current status
git status

# Add all changes
git add .

# Commit
git commit -m "Production deployment - SmartRisk v1.0 - Domain configured"

# Push to GitHub (this triggers automatic deployment)
git push origin main
```

**That's it!** 🎉

---

## 📊 Monitor Deployment

### 1. Watch GitHub Actions
1. Go to: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused/actions
2. You'll see your workflow running
3. Click on it to see detailed progress
4. All 19 steps should turn green ✅

**Deployment takes about 10-15 minutes on first run.**

### 2. What GitHub Actions Will Do Automatically:
1. ✅ Checkout code
2. ✅ Setup SSH key
3. ✅ Check EC2 connection
4. ✅ Stop running services (if any)
5. ✅ Deploy code to EC2
6. ✅ Configure environment (.env file)
7. ✅ Build Docker images (Django + Frontend)
8. ✅ Start all 7 services
9. ✅ Wait for services to be healthy
10. ✅ Run database migrations
11. ✅ Collect static files
12. ✅ Create superuser accounts:
    - alberttyagi123@gmail.com
    - pythonbyvishal@gmail.com
    - Password: SmartRisk@2026!
13. ✅ Configure Celery Beat tasks:
    - Trial expiration: Every 1 minute
    - Signal updates: Every 15 minutes
14. ✅ Restart Celery services
15. ✅ Run health checks
16. ✅ Show deployment summary

---

## ✅ Verify Deployment Success

### 1. Check GitHub Actions
All steps should be green ✅

### 2. Check Services on EC2
```bash
ssh -i your-new-key.pem ubuntu@54.183.178.141
cd ~/smartrisk
sudo docker-compose ps
```

**Expected output:**
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

### 3. Check Django Logs
```bash
sudo docker-compose logs django --tail=50
```

**Should show:**
- ✅ "Starting server with Daphne..."
- ✅ "Listening on TCP address 0.0.0.0:8000"
- ❌ No error messages

### 4. Check Celery Beat Logs
```bash
sudo docker-compose logs celery_beat --tail=30
```

**Should show:**
- ✅ "Scheduler: Sending due task check-expired-subscriptions"
- ✅ "Scheduler: Sending due task update-all-recent-signals-every-15min"

### 5. Test Application URLs

**Using IP Address:**
- Frontend: http://54.183.178.141:3000
- API Health: http://54.183.178.141:8000/health/
- Admin Panel: http://54.183.178.141:8000/admin/

**Using Domain (after DNS propagates - may take 5-30 minutes):**
- Frontend: http://smartriskfx.com:3000
- API Health: http://smartriskfx.com:8000/health/
- Admin Panel: http://smartriskfx.com:8000/admin/

### 6. Test User Registration
1. Open: http://54.183.178.141:3000 (or http://smartriskfx.com:3000)
2. Click **Register**
3. Fill in the form
4. Submit
5. Check email for verification
6. Login
7. Verify trial shows "3 days remaining"
8. Check dashboard loads with 15M timeframe

### 7. Test Admin Access
1. Open: http://54.183.178.141:8000/admin/
2. Login with:
   - **Email:** alberttyagi123@gmail.com
   - **Password:** SmartRisk@2026!
3. Verify you have full admin access

---

## 🎉 Success Indicators

You'll know everything worked when:

1. ✅ GitHub Actions workflow completes (all 19 steps green)
2. ✅ All 7 services show "Up" or "healthy"
3. ✅ Frontend loads at http://54.183.178.141:3000
4. ✅ API responds: `{"status": "healthy"}`
5. ✅ Admin panel works
6. ✅ User registration works
7. ✅ Email verification works
8. ✅ Trial countdown shows correctly
9. ✅ Dashboard loads with 15M default
10. ✅ Celery tasks running (check logs)

---

## 🚨 If Something Goes Wrong

### Issue 1: SSH Connection Failed in GitHub Actions
**Check:**
- EC2_HOST secret is correct: 54.183.178.141 ✅
- EC2_SSH_KEY secret has the entire .pem file content ✅
- EC2 security group allows SSH (port 22) from anywhere

**Solution:**
```bash
# Test SSH manually
ssh -i your-new-key.pem ubuntu@54.183.178.141
```

### Issue 2: Django Service Won't Start
**Check logs:**
```bash
cd ~/smartrisk
sudo docker-compose logs django --tail=100
```

**Try manual start:**
```bash
sudo docker-compose up -d django
```

### Issue 3: Migrations Fail
**Run manually:**
```bash
sudo docker-compose exec django python manage.py migrate --noinput
```

### Issue 4: Frontend Not Loading
**Check logs:**
```bash
sudo docker-compose logs frontend --tail=50
```

**Rebuild:**
```bash
sudo docker-compose build frontend
sudo docker-compose up -d frontend
```

### Issue 5: Domain Not Working Yet
**This is normal!** DNS propagation takes 5-30 minutes.

**Check DNS propagation:**
```bash
# From your local machine
nslookup smartriskfx.com
```

Should return: 54.183.178.141

**Use IP address while waiting:**
- http://54.183.178.141:3000

---

## 📝 Important Notes

### Your Configuration:
- **EC2 IP:** 54.183.178.141
- **Domain:** smartriskfx.com
- **DNS:** Configured ✅
- **GitHub Secrets:** All 7 configured ✅

### Container Names:
The containers use "neuraltrade" prefix (this is correct - it's the Django project name):
- neuraltrade_db
- neuraltrade_redis
- neuraltrade_django
- neuraltrade_celery_worker
- neuraltrade_celery_beat
- neuraltrade_frontend
- neuraltrade_nginx

### Brand Name:
The frontend shows "SmartRisk" everywhere ✅

### Admin Accounts:
- alberttyagi123@gmail.com / SmartRisk@2026!
- pythonbyvishal@gmail.com / SmartRisk@2026!

### Scheduled Tasks:
- Trial expiration: Every 1 minute
- Signal updates: Every 15 minutes

---

## 🔄 Future Updates

After initial deployment, to update your application:

```bash
# Just push to GitHub
git add .
git commit -m "Update description"
git push origin main
```

GitHub Actions will automatically deploy the changes. No need to SSH into EC2!

---

## 📞 Support

**Admin Emails:**
- alberttyagi123@gmail.com
- smarttriskfx@gmail.com

**Support:**
- pythonbyvishal@gmail.com

---

## ✅ Final Checklist Before Deployment

- [x] EC2 instance created (54.183.178.141)
- [x] GitHub secrets updated (all 7)
- [x] Domain DNS configured (smartriskfx.com)
- [ ] EC2 setup commands completed
- [ ] Logged out and back in to EC2
- [ ] Verified docker works without sudo
- [ ] Code pushed to GitHub

---

## 🎯 Your Next Steps (Right Now!)

1. **SSH into EC2:** `ssh -i your-new-key.pem ubuntu@54.183.178.141`
2. **Run the setup script** (copy-paste from Step 1 above)
3. **Logout and login again**
4. **Verify docker:** `docker ps`
5. **Push to GitHub:** `git push origin main`
6. **Watch deployment:** GitHub Actions tab

---

**You're ready to deploy!** 🚀

Everything is configured correctly. Just run the EC2 setup script, logout/login, and push to GitHub!

**Good luck!** 💪

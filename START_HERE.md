# 🎯 START HERE - SmartRisk Deployment

## 👋 Welcome!

You're about to deploy your **production-ready** SmartRisk trading platform to AWS EC2.

Everything is configured and automated. You just need to follow 3 simple steps.

---

## ⚡ 3 Steps to Deploy

### ✅ Step 1: Update EC2_HOST Secret (2 minutes)

You created a **NEW EC2 instance**, so you need to update the IP address in GitHub:

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Find **EC2_HOST** in the list
5. Click **Update** (pencil icon)
6. Enter your **NEW EC2 instance IP address**
7. Click **Update secret**

**Example:** If your new EC2 IP is `54.123.45.67`, enter exactly that.

---

### ✅ Step 2: Setup EC2 Instance (5 minutes - ONE TIME ONLY)

**SSH into your NEW EC2 instance:**
```bash
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP
```

**Copy and paste this ENTIRE script:**
```bash
# SmartRisk EC2 Setup Script
sudo apt update && sudo apt upgrade -y
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
sudo usermod -aG docker ubuntu
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw allow 8000/tcp && sudo ufw allow 8001/tcp
sudo ufw --force enable
mkdir -p ~/smartrisk
echo "✅ Setup Complete! Now logout and login again."
```

**IMPORTANT: After the script completes, logout and login again:**
```bash
# Logout
exit

# Login again (REQUIRED for docker group changes)
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP

# Verify docker works without sudo
docker ps
```

If `docker ps` works without sudo, you're ready! ✅

---

### ✅ Step 3: Deploy to GitHub (1 minute)

**On your local machine (in your project directory):**
```bash
# Navigate to your project
cd /path/to/your/smartrisk/project

# Add all changes
git add .

# Commit
git commit -m "Production ready - SmartRisk v1.0"

# Push to GitHub (this triggers automatic deployment)
git push origin main
```

**That's it!** 🎉

GitHub Actions will now automatically:
1. Deploy code to EC2
2. Build Docker images
3. Start all services
4. Run migrations
5. Create admin accounts
6. Configure scheduled tasks
7. Run health checks

---

## 📊 Monitor Deployment

### Watch GitHub Actions
1. Go to your GitHub repository
2. Click **Actions** tab (top menu)
3. You'll see your workflow running
4. Click on it to see detailed progress
5. All steps should turn green ✅

**Deployment takes about 10-15 minutes on first run.**

---

## ✅ Verify Success

### 1. Check GitHub Actions
All steps should be green ✅

### 2. Check Services on EC2
```bash
ssh ubuntu@YOUR_NEW_EC2_IP
cd ~/smartrisk
sudo docker-compose ps
```

You should see 7 services running:
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

### 3. Test Application
Open your browser:
- **Frontend:** `http://YOUR_EC2_IP:3000`
- **API Health:** `http://YOUR_EC2_IP:8000/health/`
- **Admin Panel:** `http://YOUR_EC2_IP:8000/admin/`

### 4. Test User Registration
1. Go to `http://YOUR_EC2_IP:3000`
2. Click **Register**
3. Fill in the form
4. Check your email for verification
5. Login and check dashboard
6. Verify trial shows "3 days remaining"

### 5. Test Admin Access
1. Go to `http://YOUR_EC2_IP:8000/admin/`
2. Login with:
   - **Email:** alberttyagi123@gmail.com
   - **Password:** SmartRisk@2026!
3. Verify you have full admin access

---

## 🎉 Success!

If all the above checks pass, your deployment is successful! 🚀

**What's Running:**
- ✅ PostgreSQL database (TimescaleDB)
- ✅ Redis cache
- ✅ Django API (Daphne ASGI)
- ✅ Celery worker (background tasks)
- ✅ Celery beat (task scheduler)
- ✅ Next.js frontend
- ✅ Nginx reverse proxy

**Scheduled Tasks:**
- ✅ Trial expiration check: Every 1 minute
- ✅ Signal updates: Every 15 minutes

**Admin Accounts:**
- ✅ alberttyagi123@gmail.com
- ✅ pythonbyvishal@gmail.com
- ✅ Password: SmartRisk@2026!

---

## 🚨 If Something Goes Wrong

### Django Service Won't Start
```bash
# Check logs
sudo docker-compose logs django --tail=100

# Try manual start
sudo docker-compose up -d django
```

### Migrations Fail
```bash
# Run manually
sudo docker-compose exec django python manage.py migrate --noinput
```

### Frontend Not Loading
```bash
# Check logs
sudo docker-compose logs frontend --tail=50

# Rebuild
sudo docker-compose build frontend
sudo docker-compose up -d frontend
```

### Need More Help?
Check these files:
- **QUICK_DEPLOYMENT_GUIDE.md** - Detailed deployment guide
- **COMMANDS_REFERENCE.md** - All useful commands
- **FINAL_VERIFICATION.md** - Troubleshooting guide

---

## 📋 GitHub Secrets Checklist

Make sure these 7 secrets are configured in GitHub:

1. ✅ **AWS_ACCESS_KEY_ID**
2. ✅ **AWS_SECRET_ACCESS_KEY**
3. ⚠️ **EC2_HOST** - UPDATE WITH NEW IP!
4. ✅ **EC2_SSH_KEY** (entire .pem file content)
5. ✅ **DJANGO_SECRET_KEY**: `b%jb$1*+ege5^u+kn7q83zs=65e1(6n-txkg--k3#*tvf1e4ex`
6. ✅ **EMAIL_HOST_USER**
7. ✅ **EMAIL_HOST_PASSWORD**

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

## 📚 Documentation Files

- **START_HERE.md** ← You are here
- **QUICK_DEPLOYMENT_GUIDE.md** - Quick 3-step guide
- **PRODUCTION_DEPLOYMENT_CHECKLIST.md** - Complete checklist
- **FINAL_VERIFICATION.md** - Pre-deployment verification
- **COMMANDS_REFERENCE.md** - All useful commands
- **README_DEPLOYMENT.md** - Complete deployment documentation

---

## 💡 Important Notes

### DO NOT Run These on EC2:
- ❌ `curl "https://..."` commands (not needed)
- ❌ Manual Docker commands (GitHub Actions handles this)
- ❌ Manual migrations (automated)
- ❌ Manual superuser creation (automated)

### You ONLY Need:
1. ✅ Update EC2_HOST secret
2. ✅ Run EC2 setup script (once)
3. ✅ Logout/login
4. ✅ `git push origin main`

---

## 🎯 Ready to Deploy?

Follow these 3 steps:

1. **Update EC2_HOST secret** with new IP
2. **Run setup script** on EC2 (logout/login after)
3. **Push to GitHub**: `git push origin main`

**You've got this!** 💪

---

## 📞 Contact

**Admin Emails:**
- alberttyagi123@gmail.com
- smarttriskfx@gmail.com

**Support:**
- pythonbyvishal@gmail.com

---

**Good luck with your deployment!** 🚀

Remember: You've done all the hard work. The deployment is fully automated. Just follow the 3 steps above and watch it deploy!

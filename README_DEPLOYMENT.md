# 🚀 SmartRisk - Production Deployment

## 📖 Quick Start

This is your **production-ready** SmartRisk trading platform. Everything is configured and automated. You just need to:

1. **Update EC2_HOST secret** with your new EC2 IP
2. **Run setup commands** on EC2 (one time only)
3. **Push to GitHub** - deployment happens automatically

---

## 📚 Documentation Files

### For Deployment:
1. **QUICK_DEPLOYMENT_GUIDE.md** - ⚡ Start here! 3 simple steps
2. **PRODUCTION_DEPLOYMENT_CHECKLIST.md** - 📋 Complete checklist
3. **FINAL_VERIFICATION.md** - ✅ Pre-deployment verification

### For Reference:
- **AWS_SECURITY_GROUP_PORTS.md** - Security group configuration
- **ADMIN_PERMISSIONS_GUIDE.md** - Admin access guide
- **API_DOCUMENTATION.md** - API endpoints

---

## ⚡ Quick Deployment (3 Steps)

### Step 1: Update GitHub Secret (2 min)
```
GitHub → Settings → Secrets → Actions → EC2_HOST → Update
Enter your NEW EC2 IP address
```

### Step 2: Setup EC2 (5 min - ONE TIME)
```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP

# Run this script (copy-paste entire block):
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
docker --version && docker-compose --version

# IMPORTANT: Logout and login again
exit
# Then reconnect
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP
```

### Step 3: Deploy (1 min)
```bash
# In your local project
git add .
git commit -m "Production deployment"
git push origin main
```

**Done! GitHub Actions deploys everything automatically.**

---

## ✅ Verify Deployment

### Check GitHub Actions
```
GitHub → Actions tab → Watch workflow run → All steps green ✅
```

### Check Services on EC2
```bash
ssh ubuntu@YOUR_NEW_EC2_IP
cd ~/smartrisk
sudo docker-compose ps
```

Should show 7 services running:
- ✅ neuraltrade_db (healthy)
- ✅ neuraltrade_redis (healthy)
- ✅ neuraltrade_django (healthy)
- ✅ neuraltrade_celery_worker (Up)
- ✅ neuraltrade_celery_beat (Up)
- ✅ neuraltrade_frontend (Up)
- ✅ neuraltrade_nginx (Up)

### Test Application
```
Frontend: http://YOUR_EC2_IP:3000
API: http://YOUR_EC2_IP:8000/health/
Admin: http://YOUR_EC2_IP:8000/admin/
```

---

## 🎯 What's Automated

GitHub Actions automatically:
1. ✅ Deploys code to EC2
2. ✅ Builds Docker images
3. ✅ Starts all services
4. ✅ Runs database migrations
5. ✅ Creates superuser accounts
6. ✅ Configures scheduled tasks
7. ✅ Runs health checks

---

## 🔐 Admin Access

**Superuser Accounts:**
- Email: alberttyagi123@gmail.com
- Email: pythonbyvishal@gmail.com
- Password: SmartRisk@2026!

**Admin Panel:**
- URL: http://YOUR_EC2_IP:8000/admin/

---

## ⏰ Scheduled Tasks

Automatically configured:
- ✅ Trial expiration check: Every 1 minute
- ✅ Signal updates: Every 15 minutes

---

## 🐳 Services

7 Docker containers:
1. **PostgreSQL** (TimescaleDB) - Database
2. **Redis** - Cache & message broker
3. **Django** (Daphne ASGI) - Backend API
4. **Celery Worker** - Background tasks
5. **Celery Beat** - Task scheduler
6. **Next.js** - Frontend
7. **Nginx** - Reverse proxy & SSL

---

## 📋 GitHub Secrets Required

Make sure these 7 secrets are configured:

1. **AWS_ACCESS_KEY_ID**
2. **AWS_SECRET_ACCESS_KEY**
3. **EC2_HOST** ⚠️ UPDATE WITH NEW IP!
4. **EC2_SSH_KEY** (entire .pem file)
5. **DJANGO_SECRET_KEY**: `b%jb$1*+ege5^u+kn7q83zs=65e1(6n-txkg--k3#*tvf1e4ex`
6. **EMAIL_HOST_USER**
7. **EMAIL_HOST_PASSWORD**

---

## 🚨 Troubleshooting

### Django Won't Start
```bash
sudo docker-compose logs django --tail=100
sudo docker-compose up -d django
```

### Check All Logs
```bash
sudo docker-compose logs --tail=50
```

### Restart Everything
```bash
sudo docker-compose restart
```

### Rebuild Everything
```bash
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d
```

---

## 🎉 Features

### User Features:
- ✅ User registration with email verification
- ✅ 3-day free trial (auto-expires)
- ✅ Real-time trading signals
- ✅ Live market charts (15M, 1H, 4H, 1D)
- ✅ Signal alerts
- ✅ Trading history
- ✅ Subscription management

### Admin Features:
- ✅ Full Django admin panel
- ✅ User management
- ✅ Subscription management
- ✅ Signal monitoring
- ✅ System health checks

### Technical Features:
- ✅ WebSocket support for real-time data
- ✅ Celery for background tasks
- ✅ Redis for caching
- ✅ TimescaleDB for time-series data
- ✅ Docker containerization
- ✅ Automated CI/CD with GitHub Actions
- ✅ Health checks for all services
- ✅ Automatic migrations
- ✅ SSL ready (Nginx configured)

---

## 📊 System Requirements

### EC2 Instance:
- **Type:** t2.medium or better
- **OS:** Ubuntu 24.04 LTS
- **Storage:** 30GB minimum
- **Memory:** 4GB minimum

### Ports Required:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 8000 (Django API)
- 8001 (WebSocket)

---

## 🔄 Future Updates

After initial deployment, to update:

```bash
# Just push to GitHub
git add .
git commit -m "Update description"
git push origin main
```

GitHub Actions will automatically:
1. Deploy new code
2. Rebuild containers
3. Run migrations
4. Restart services

**No need to SSH into EC2!**

---

## 📞 Contact

**Admin Emails:**
- alberttyagi123@gmail.com
- smarttriskfx@gmail.com

**Support:**
- pythonbyvishal@gmail.com

---

## 🎯 Project Status

- ✅ ML dependencies removed
- ✅ Brand changed to SmartRisk
- ✅ Trial system working
- ✅ Signal updates automated
- ✅ GitHub Actions configured
- ✅ Docker optimized
- ✅ All services configured
- ✅ Health checks working
- ✅ Admin accounts configured
- ✅ Email verification working

**Status: PRODUCTION READY** 🚀

---

## 📝 Important Notes

### DO NOT Run on EC2:
- ❌ Manual Docker commands (GitHub Actions handles this)
- ❌ Manual migrations (automated)
- ❌ Manual superuser creation (automated)
- ❌ `curl "https://..."` commands (not needed)

### You ONLY Need:
1. ✅ One-time EC2 setup (Docker, Docker Compose, firewall)
2. ✅ Update EC2_HOST secret
3. ✅ `git push origin main`

### After First Deployment:
- Future updates: Just `git push`
- No SSH needed
- Everything automated

---

**Ready to deploy? Follow QUICK_DEPLOYMENT_GUIDE.md** 🚀

Good luck! You've got this! 💪

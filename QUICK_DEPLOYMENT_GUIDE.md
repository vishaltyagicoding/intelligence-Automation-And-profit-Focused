# ⚡ Quick Deployment Guide - SmartRisk

## 🎯 3 Simple Steps to Deploy

### Step 1: Update EC2_HOST Secret (2 minutes)
1. Go to GitHub → Your Repository
2. Settings → Secrets and variables → Actions
3. Find **EC2_HOST** → Click Update
4. Enter your NEW EC2 IP address
5. Click Update secret

### Step 2: Setup EC2 Instance (5 minutes - ONE TIME ONLY)

**SSH into your NEW EC2 instance:**
```bash
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP
```

**Copy-paste this entire script:**
```bash
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
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
sudo ufw --force enable

# Create project directory
mkdir -p ~/smartrisk

# Verify
docker --version
docker-compose --version
df -h
```

**IMPORTANT: Logout and login again:**
```bash
exit
# Then reconnect
ssh -i your-key.pem ubuntu@YOUR_NEW_EC2_IP
```

### Step 3: Deploy (1 minute)

```bash
# In your local project directory
git add .
git commit -m "Production deployment"
git push origin main
```

**That's it! GitHub Actions will do everything else automatically.**

---

## ✅ Verify Deployment Success

### Check GitHub Actions
1. Go to GitHub → Actions tab
2. Watch the workflow run
3. All steps should be green ✅

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
1. Open: `http://YOUR_EC2_IP:3000`
2. Register a new user
3. Check email verification
4. Login and test dashboard

---

## 🚨 If Something Goes Wrong

### Check Django Logs
```bash
sudo docker-compose logs django --tail=100
```

### Check All Services
```bash
sudo docker-compose logs --tail=50
```

### Restart Services
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

## 📋 GitHub Secrets Checklist

Make sure these 7 secrets are configured:

1. ✅ **AWS_ACCESS_KEY_ID**
2. ✅ **AWS_SECRET_ACCESS_KEY**
3. ✅ **EC2_HOST** ⚠️ UPDATE WITH NEW IP!
4. ✅ **EC2_SSH_KEY** (entire .pem file content)
5. ✅ **DJANGO_SECRET_KEY**: `b%jb$1*+ege5^u+kn7q83zs=65e1(6n-txkg--k3#*tvf1e4ex`
6. ✅ **EMAIL_HOST_USER**
7. ✅ **EMAIL_HOST_PASSWORD**

---

## 🎉 After Successful Deployment

**Admin Access:**
- URL: `http://YOUR_EC2_IP:8000/admin/`
- Email: alberttyagi123@gmail.com
- Password: SmartRisk@2026!

**Application:**
- Frontend: `http://YOUR_EC2_IP:3000`
- API: `http://YOUR_EC2_IP:8000/api/`
- WebSocket: `ws://YOUR_EC2_IP:8001/ws/`

**Scheduled Tasks:**
- ✅ Trial expiration: Every 1 minute
- ✅ Signal updates: Every 15 minutes

---

## 💡 Remember

- ✅ First time: Run EC2 setup commands (once)
- ✅ After that: Just `git push origin main`
- ✅ GitHub Actions handles everything automatically
- ✅ No need to SSH into EC2 for deployments
- ✅ All configurations are automated

**You're ready to deploy! 🚀**

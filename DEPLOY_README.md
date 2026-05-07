# Deploy NeuralTrade to AWS - Simple Instructions

## ONE COMMAND DEPLOYMENT 🚀

### On AWS Server:

```bash
# 1. Install Docker (one time only)
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $USER

# 2. Install Docker Compose (one time only)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose

# 3. Logout and login again (one time only)
exit

# 4. Upload your project and configure
cp .env.production .env
nano .env  # Update passwords and API keys

# 5. DEPLOY EVERYTHING
chmod +x deploy.sh && ./deploy.sh
```

## That's It! ✅

Your application is now running at:
- **http://your-server-ip** (Frontend)
- **http://your-server-ip/api/** (Backend API)

---

## Files Created for You

1. **docker-compose.prod.yml** - Production Docker configuration
2. **deploy.sh** - One-command deployment script
3. **.env.production** - Environment variables template
4. **AWS_DEPLOYMENT_GUIDE.md** - Complete guide
5. **QUICK_START.md** - 5-minute quick start
6. **DEPLOYMENT_SUMMARY.md** - Overview

---

## Quick Commands

```bash
# Deploy/Update
./deploy.sh

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart
docker-compose -f docker-compose.prod.yml restart

# Stop
docker-compose -f docker-compose.prod.yml down

# Status
docker-compose -f docker-compose.prod.yml ps
```

---

## What Gets Deployed

✅ Frontend (Next.js with reversal zones)
✅ Backend (Django API)
✅ Database (PostgreSQL)
✅ Redis (Cache)
✅ Celery (Background tasks)
✅ Nginx (Reverse proxy)

All in Docker, all connected, all working!

---

For detailed instructions, see **AWS_DEPLOYMENT_GUIDE.md**

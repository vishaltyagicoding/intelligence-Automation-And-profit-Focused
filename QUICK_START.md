# Quick Start - Deploy to AWS in 5 Minutes

## 1. Prepare Your AWS Server

```bash
# Connect to AWS
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again
exit
```

## 2. Upload Your Project

```bash
# Option A: Using Git
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Option B: Using SCP (from local machine)
scp -i your-key.pem -r /path/to/project ubuntu@your-ec2-ip:~/neuraltrade
```

## 3. Configure Environment

```bash
# Copy and edit .env file
cp .env.production .env
nano .env

# Update these values:
# - DB_PASSWORD
# - SECRET_KEY (generate with: python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# - ALLOWED_HOSTS (add your domain/IP)
# - BINANCE_API_KEY and BINANCE_API_SECRET
```

## 4. Deploy Everything

```bash
# Make script executable
chmod +x deploy.sh

# Deploy with ONE command
./deploy.sh
```

## 5. Access Your Application

- **Frontend**: `http://your-ec2-ip`
- **Backend API**: `http://your-ec2-ip/api/`
- **Admin**: `http://your-ec2-ip/admin/`

---

## That's It! 🎉

Your application is now running with:
- ✅ Frontend (Next.js) 
- ✅ Backend (Django)
- ✅ Database (PostgreSQL)
- ✅ Redis Cache
- ✅ Celery Workers
- ✅ Nginx Reverse Proxy
- ✅ Reversal Zones Calculation
- ✅ Live Market Data
- ✅ WebSocket Support

---

## Common Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop everything
docker-compose -f docker-compose.prod.yml down

# Update application
git pull origin main
./deploy.sh
```

---

## Troubleshooting

**Container won't start?**
```bash
docker-compose -f docker-compose.prod.yml logs [service-name]
```

**Need to rebuild?**
```bash
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

**Database issues?**
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT 1"
```

---

For detailed documentation, see `AWS_DEPLOYMENT_GUIDE.md`

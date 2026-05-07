# GitHub Actions Setup Guide for SmartRisk

This guide will help you set up automatic deployment to your AWS EC2 server using GitHub Actions.

## 📋 Prerequisites

- GitHub repository for your SmartRisk project
- AWS EC2 Ubuntu server (54.183.119.39)
- SSH access to EC2 server
- Docker and Docker Compose installed on EC2

## 🔑 Step 1: Add GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following 7 secrets:

### 1. AWS_ACCESS_KEY_ID
```
AKIAV7HDFDCOE5JDE45U
```

### 2. AWS_SECRET_ACCESS_KEY
```
hosoEmau8FPhol9ekGInsqfTam0wwPzCcCkasObi
```

### 3. EC2_HOST
```
54.183.119.39
```

### 4. EC2_SSH_KEY
```
-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAuy1aOAnvchtcrQ1VGdJo+FQEEQZ0mXlMASBfITZnz4ZCaPwy
7JWpyUKnlTxTF/IP2UEz3r19VqEWfPQfqGsULtNN2d8WAdHICkc/LSwd4MTEhKYG
QhfDQVtpGfaS3Oqt2nNRViDni0N+LS3FoIeY+AI6H2+1aAmM42HOKlmLuPV/2hcb
LkbU0zDvHmVTlGx3LhlU5UawVCM/0HlqbQN7YS9zTKyLgemO6eGIG3ax5GBMPfxq
28fXfYhXYmbZtY49igloiioPKxAES8m3mbCJVu2/XNfJf/MndFUXqM+5sQm5FLnj
AbTcy3yC/F0pRd9XC6UsAp3/kieIwmo6+AvJeQIDAQABAoIBACo07dUZGG9IkDtN
eFUcRyNH/qrAI+a/nU3buNfKZto60hrOU8VZcjG54AQc2DfcE4rP0xx06iBwrpt6
iPD3RFPSvglU7qd2YH9A1ZQgEJSwigfHUD3zEcpZDHgYS8GZAZ7yxfJ/9PZIP9l8
KsYqDWpPRj/0dpmBHc3gLhcKniEUh9fTzufc/Q/0Cmsjwuh7b8k2U8e+C2XlFHci
cIbyvgng6F+D1P0Rq7QzL798PsXP0dNv6z/TgH3jUtLyHfYaFWEXc2HksuDprYn/
HoImdpABxAZPtLek7/ws4kZCJYuAzRiyNGDCXvQ5DRjytP8+iRtpuz1Y7j6h23qh
LIDPgEkCgYEA6QRHthuUc+XQHe+cdJ/30rBD14eTmMdJbhLNHpWjJCGujnUNbiRd
s7JCKNXjP6A7pPHRcfJCyqxIfWj1i5LnLjPOzcrcK/RYJxYVictNkoiE2plP9rhK
ENU1JOeuNgSTkX5G5WXhw/I8y5MA1YkqNQvXwP7kK8sEKzOl2tYSlO8CgYEAzaOd
Lg+Lu3Dx6JVDwoGZDQrOk/Q9agJK95r6A2gszhLLK7iKWlyQluW9B7WfHhwd3oBr
KN3meClbjlZY3S9vq3dnzzZ8Q+rwBIEMNLajHcZmmz5SLGLPy2K4utDaWswfQHjo
fdoSFrC2frsGXv96ikjtAQNyHe2X8pjEvKw2GBcCgYBvpW5asgJCOcWq4kjblF4g
o/YNiddNZ4cmZ3nCgr4FLOI/PZRuxpvi4rFScZENxk9tq7PH3eTkyQF+nVCxTHTa
LVaUQfOWV9/48lrlh/SmFiVZvAWVWB2czRtGkH9nQHAYUSHU/ijbQvCgNdI7fhos
Cn2Y6kgXN5HKxVddcB69HwKBgE+B8hTMB++6FJ4jkCZVK1LimcqUxWYGauvfLMlC
bwhiNdG6sSuM3I6rVvHzJAllP5s2tbgAS8qr2u1mr0cdvyRhr25rl5I+9PwY1RpQ
fzLU8fkWGHl23va5PcllVPeEMpUf6mw2c4X4XycSsrzqNHvhBFm+9lFh+rzemjqE
rwmTAoGABt60Bf4viljZ5VIgRPeZ8rnEo0tb8aRn2vLGJlx9uGWJHSg7l9EyTfzo
vg0Zk4W3DVl09vaSV4gHHR+S93d+0Fw0B/U/wUWzicTFGTcTDknTMxR1U4SCX2zX
uun3ZW0SaUuNBHsRG3tIhE3hvxNJoWbR2N1WY8hE9MG46Yts8yM=
-----END RSA PRIVATE KEY-----
```

### 5. DJANGO_SECRET_KEY

Generate a new Django secret key by running this command on your local machine:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and add it as the secret value.

### 6. EMAIL_HOST_USER
```
alberttyagi123@gmail.com
```
(or your Gmail address)

### 7. EMAIL_HOST_PASSWORD

You need to create a Gmail App Password:

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already enabled
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and "Other (Custom name)"
5. Enter "SmartRisk" as the name
6. Click "Generate"
7. Copy the 16-character password (without spaces)
8. Add it as the secret value

## 🚀 Step 2: Prepare Your EC2 Server

SSH into your EC2 server and prepare it:

```bash
ssh ubuntu@54.183.119.39

# Create project directory
mkdir -p ~/smartrisk
cd ~/smartrisk

# Install Docker if not already installed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Django API
sudo ufw allow 8001/tcp  # WebSocket
sudo ufw --force enable

# Logout and login again for docker group to take effect
exit
```

## 📦 Step 3: Push to GitHub

Once all secrets are added, push your code to GitHub:

```bash
# Add all files
git add .

# Commit changes
git commit -m "Add GitHub Actions deployment workflow"

# Push to main branch (this will trigger deployment)
git push origin main
```

## 🔍 Step 4: Monitor Deployment

1. Go to your GitHub repository
2. Click on **Actions** tab
3. You'll see the deployment workflow running
4. Click on the workflow run to see detailed logs
5. Wait for all steps to complete (takes about 5-10 minutes)

## ✅ Step 5: Verify Deployment

After deployment completes, verify everything is working:

### Check Application URLs:
- **Frontend**: http://54.183.119.39
- **API**: http://54.183.119.39:8000
- **Admin Panel**: http://54.183.119.39:8000/admin/

### Admin Login:
- **Email**: alberttyagi123@gmail.com
- **Password**: SmartRisk@2026!

### Check Services on EC2:
```bash
ssh ubuntu@54.183.119.39
cd ~/smartrisk
sudo docker-compose ps
sudo docker-compose logs -f
```

## 🔄 Automatic Deployments

From now on, every time you push to the `main` or `master` branch, GitHub Actions will automatically:

1. ✅ Stop running services
2. ✅ Deploy new code to EC2
3. ✅ Build Docker images
4. ✅ Start all services
5. ✅ Run database migrations
6. ✅ Configure Celery Beat tasks (1 min + 15 min)
7. ✅ Perform health checks
8. ✅ Show deployment summary

## 🎯 Manual Deployment Trigger

You can also trigger deployment manually:

1. Go to **Actions** tab in GitHub
2. Click on **Deploy SmartRisk to AWS EC2** workflow
3. Click **Run workflow** button
4. Select branch (main/master)
5. Click **Run workflow**

## 🐛 Troubleshooting

### Deployment Failed?

1. Check GitHub Actions logs for error details
2. SSH into EC2 and check logs:
   ```bash
   ssh ubuntu@54.183.119.39
   cd ~/smartrisk
   sudo docker-compose logs [service-name]
   ```

### Common Issues:

**SSH Connection Failed:**
- Verify EC2_HOST secret is correct
- Verify EC2_SSH_KEY secret contains the complete private key
- Check EC2 security group allows SSH (port 22)

**Docker Build Failed:**
- Check if EC2 has enough disk space: `df -h`
- Check if Docker is running: `sudo systemctl status docker`

**Service Won't Start:**
- Check logs: `sudo docker-compose logs [service-name]`
- Verify .env file exists: `cat ~/smartrisk/.env`
- Check if ports are available: `sudo netstat -tulpn`

**Database Migration Failed:**
- Check PostgreSQL logs: `sudo docker-compose logs db`
- Verify database credentials in .env file

## 📊 Services Overview

After successful deployment, these services will be running:

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | TimescaleDB database |
| Redis | 6379 | Cache and message broker |
| Django | 8000 | Backend API (Daphne ASGI) |
| WebSocket | 8001 | Real-time updates |
| Celery Worker | - | Background task processor |
| Celery Beat | - | Task scheduler |
| Next.js | 3000 | Frontend application |
| Nginx | 80 | Reverse proxy |

## ⏰ Scheduled Tasks

Two Celery Beat tasks are automatically configured:

1. **Trial Expiration Check**: Runs every 1 minute
   - Checks for expired trials
   - Sends expiration emails
   - Updates user status

2. **Signal Updates**: Runs every 15 minutes
   - Updates trading signals
   - Processes market data
   - Sends signal alerts

## 🎉 Success!

Your SmartRisk application is now set up for automatic deployment! Every push to main/master will automatically deploy to your EC2 server.

## 📞 Support

If you encounter any issues:
1. Check GitHub Actions logs
2. Check EC2 service logs
3. Verify all secrets are correctly added
4. Ensure EC2 security group allows required ports

---

**Last Updated**: May 8, 2026
**Version**: 1.0.0

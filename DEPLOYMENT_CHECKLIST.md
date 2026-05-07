# SmartRisk Deployment Checklist

Complete this checklist before deploying to AWS EC2 via GitHub Actions.

---

## ✅ Pre-Deployment Checklist

### 1. GitHub Repository Setup
- [ ] GitHub repository created
- [ ] Code pushed to repository
- [ ] Repository is private (recommended for production)

### 2. GitHub Secrets Configuration
Go to: **Settings → Secrets and variables → Actions → New repository secret**

- [ ] `AWS_ACCESS_KEY_ID` added (AKIAV7HDFDCOE5JDE45U)
- [ ] `AWS_SECRET_ACCESS_KEY` added (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)
- [ ] `EC2_HOST` added (54.183.119.39)
- [ ] `EC2_SSH_KEY` added (full RSA private key)
- [ ] `DJANGO_SECRET_KEY` generated and added
- [ ] `EMAIL_HOST_USER` added (alberttyagi123@gmail.com)
- [ ] `EMAIL_HOST_PASSWORD` added (Gmail app password)

### 3. EC2 Server Preparation
SSH into server: `ssh ubuntu@54.183.119.39`

- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Project directory created (`~/smartrisk`)
- [ ] Firewall configured (ports 22, 80, 443, 8000, 8001)
- [ ] User added to docker group (`sudo usermod -aG docker ubuntu`)
- [ ] Logged out and back in for group changes

### 4. Local Code Verification
- [ ] All environment files excluded from git (.env, .env.local, etc.)
- [ ] No sensitive data in code (API keys, passwords, etc.)
- [ ] Docker files present (Dockerfile.backend, Dockerfile.frontend)
- [ ] docker-compose.yml configured correctly
- [ ] GitHub Actions workflow file present (.github/workflows/deploy-aws.yml)

### 5. Configuration Files
- [ ] `.gitignore` includes all sensitive files
- [ ] `docker-compose.yml` uses correct service names
- [ ] `requirements.txt` has all Python dependencies
- [ ] `package.json` has all Node.js dependencies

---

## 🚀 Deployment Steps

### Step 1: Generate Django Secret Key
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
- [ ] Generated and added to GitHub Secrets

### Step 2: Create Gmail App Password
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to https://myaccount.google.com/apppasswords
4. Create app password for "SmartRisk"
- [ ] Created and added to GitHub Secrets

### Step 3: Verify All Secrets
- [ ] All 7 secrets added to GitHub
- [ ] No typos in secret names
- [ ] No extra spaces in secret values

### Step 4: Push to GitHub
```bash
git add .
git commit -m "Add GitHub Actions deployment workflow"
git push origin main
```
- [ ] Code pushed successfully
- [ ] GitHub Actions workflow triggered

### Step 5: Monitor Deployment
- [ ] Go to GitHub → Actions tab
- [ ] Watch deployment progress
- [ ] All steps completed successfully (green checkmarks)

---

## 🔍 Post-Deployment Verification

### 1. Check Application URLs
- [ ] Frontend accessible: http://54.183.119.39
- [ ] API accessible: http://54.183.119.39:8000
- [ ] Admin panel accessible: http://54.183.119.39:8000/admin/
- [ ] WebSocket working: ws://54.183.119.39:8001

### 2. Test Admin Login
- [ ] Login with alberttyagi123@gmail.com / SmartRisk@2026!
- [ ] Login with pythonbyvishal@gmail.com / SmartRisk@2026!
- [ ] Both accounts have superuser access

### 3. Verify Services on EC2
SSH into server and run:
```bash
cd ~/smartrisk
sudo docker-compose ps
```

Expected services (all should be "Up"):
- [ ] db (PostgreSQL)
- [ ] redis
- [ ] django
- [ ] celery_worker
- [ ] celery_beat
- [ ] frontend
- [ ] nginx

### 4. Check Celery Beat Tasks
```bash
sudo docker-compose logs celery_beat | grep "check-expired-subscriptions"
sudo docker-compose logs celery_beat | grep "update-all-recent-signals"
```

- [ ] Trial expiration task running every 1 minute
- [ ] Signal update task running every 15 minutes

### 5. Test User Registration
- [ ] Register new user
- [ ] Receive verification email
- [ ] Verify email works
- [ ] Trial countdown shows correctly (3 days)

### 6. Test Trading Features
- [ ] Dashboard loads with default 15M timeframe
- [ ] Can switch between timeframes (5M, 15M, 1H, 4H, 1D)
- [ ] Live charts display correctly
- [ ] Signals display correctly (except 4H - should be hidden)
- [ ] WebSocket updates work in real-time

### 7. Test Email Notifications
- [ ] Trial expiration emails sent
- [ ] Signal alert emails sent
- [ ] Password reset emails sent

---

## 🐛 Troubleshooting

### If Deployment Fails:

1. **Check GitHub Actions Logs**
   - Go to Actions tab
   - Click on failed workflow
   - Review error messages

2. **Check EC2 Service Logs**
   ```bash
   ssh ubuntu@54.183.119.39
   cd ~/smartrisk
   sudo docker-compose logs [service-name]
   ```

3. **Common Issues:**

   **SSH Connection Failed:**
   - Verify EC2_HOST is correct
   - Verify EC2_SSH_KEY is complete (including BEGIN/END lines)
   - Check EC2 security group allows port 22

   **Docker Build Failed:**
   - Check disk space: `df -h`
   - Check Docker status: `sudo systemctl status docker`
   - Clear old images: `sudo docker system prune -a`

   **Service Won't Start:**
   - Check logs: `sudo docker-compose logs [service]`
   - Verify .env file: `cat ~/smartrisk/.env`
   - Check port availability: `sudo netstat -tulpn`

   **Database Migration Failed:**
   - Check PostgreSQL: `sudo docker-compose logs db`
   - Verify credentials in .env
   - Try manual migration: `sudo docker-compose exec django python manage.py migrate`

   **Celery Tasks Not Running:**
   - Check Celery Beat: `sudo docker-compose logs celery_beat`
   - Check Celery Worker: `sudo docker-compose logs celery_worker`
   - Verify Redis: `sudo docker-compose exec redis redis-cli ping`

---

## 🔄 Future Deployments

After initial setup, every push to `main` or `master` branch will automatically:

1. ✅ Stop running services
2. ✅ Deploy new code
3. ✅ Build Docker images
4. ✅ Start services
5. ✅ Run migrations
6. ✅ Configure Celery tasks
7. ✅ Perform health checks

**Manual Deployment:**
- Go to Actions tab
- Click "Deploy SmartRisk to AWS EC2"
- Click "Run workflow"
- Select branch and run

---

## 📊 Monitoring

### Daily Checks:
- [ ] All services running: `sudo docker-compose ps`
- [ ] No errors in logs: `sudo docker-compose logs --tail=100`
- [ ] Disk space available: `df -h`
- [ ] Memory usage: `free -h`

### Weekly Checks:
- [ ] Database backups created
- [ ] Log files rotated
- [ ] Security updates applied: `sudo apt update && sudo apt upgrade`

### Monthly Checks:
- [ ] Review user activity
- [ ] Check for failed tasks
- [ ] Update dependencies if needed
- [ ] Review and optimize database

---

## 🎯 Success Criteria

Your deployment is successful when:

- ✅ All 7 services are running
- ✅ Frontend loads without errors
- ✅ API responds to requests
- ✅ Admin panel accessible
- ✅ User registration works
- ✅ Email notifications sent
- ✅ Trial countdown displays correctly
- ✅ Trading signals update every 15 minutes
- ✅ Trial expiration checks every 1 minute
- ✅ WebSocket real-time updates work
- ✅ Charts display correctly for all timeframes
- ✅ No errors in service logs

---

## 📞 Support Resources

- **GitHub Actions Logs**: Repository → Actions tab
- **EC2 Service Logs**: `sudo docker-compose logs [service]`
- **Django Admin**: http://54.183.119.39:8000/admin/
- **API Documentation**: http://54.183.119.39:8000/api/docs/

---

## 🎉 Congratulations!

If all items are checked, your SmartRisk application is successfully deployed and running in production on AWS EC2!

---

**Last Updated**: May 8, 2026
**Version**: 1.0.0

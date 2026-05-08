# GitHub Workflow Configuration

## ✅ Active Workflow File

**File**: `.github/workflows/deploy-aws.yml`

**Status**: ✅ **ACTIVE AND CONFIGURED**

**What it does**:
- Deploys SmartRisk to your EC2 server (54.183.119.39)
- Triggers on push to `main` or `master` branch
- Can be manually triggered from GitHub Actions UI
- Uses SSH to connect to EC2 (no AWS CLI needed)
- Builds Docker images on EC2 server
- Starts all 7 services automatically
- Configures Celery Beat tasks (1 min + 15 min)
- Runs health checks

---

## ❌ Deleted Files

**File**: `.github/workflows/deploy.yml`

**Status**: ❌ **DELETED** (was old ECS-based workflow)

**Why deleted**: 
- Used AWS ECS (Elastic Container Service) - not needed
- Used AWS ECR (Elastic Container Registry) - not needed
- Required AWS CLI - not needed
- More complex and expensive
- Not compatible with your EC2 direct deployment

---

## 🎯 Your Deployment Method

### Simple and Direct:
```
GitHub Actions → SSH → EC2 Server → Docker Compose
```

### No Need For:
- ❌ AWS CLI
- ❌ AWS ECR (Container Registry)
- ❌ AWS ECS (Container Service)
- ❌ Complex AWS configurations

### What You Use:
- ✅ GitHub Actions (CI/CD)
- ✅ SSH (Secure connection)
- ✅ EC2 (Your Ubuntu server)
- ✅ Docker & Docker Compose (On EC2)

---

## 📋 Workflow Configuration

### File Location:
```
.github/workflows/deploy-aws.yml
```

### Triggers:
1. **Automatic**: Push to `main` or `master` branch
2. **Manual**: Click "Run workflow" in GitHub Actions UI

### Required GitHub Secrets (7):
1. `AWS_ACCESS_KEY_ID`
2. `AWS_SECRET_ACCESS_KEY`
3. `EC2_HOST`
4. `EC2_SSH_KEY`
5. `DJANGO_SECRET_KEY`
6. `EMAIL_HOST_USER`
7. `EMAIL_HOST_PASSWORD`

### Deployment Steps (19 total):
1. Checkout code
2. Setup SSH key
3. Check EC2 connection
4. Stop running services
5. Deploy code to EC2
6. Configure environment
7. Build Docker images
8. Start services
9. Wait for services
10. Run migrations
11. Collect static files
12. Create superusers
13. Configure Celery tasks
14. Restart services
15-19. Health checks

---

## 🚀 How to Deploy

### Option 1: Automatic (Recommended)
```bash
# Any push to main triggers deployment
git add .
git commit -m "Your changes"
git push origin main
```

### Option 2: Manual Trigger
1. Go to: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused/actions
2. Click "Deploy SmartRisk to AWS EC2"
3. Click "Run workflow"
4. Select branch: main
5. Click "Run workflow"

---

## 📊 Deployment Timeline

**First Deployment**: 8-12 minutes
- Building Docker images (longest step)
- Installing dependencies
- Starting services
- Running migrations

**Future Deployments**: 3-5 minutes
- Using cached Docker images
- Only rebuilding changed layers
- Faster startup

---

## ✅ What Gets Deployed

### Services (7):
1. PostgreSQL (TimescaleDB)
2. Redis
3. Django (Daphne ASGI)
4. Celery Worker
5. Celery Beat
6. Next.js Frontend
7. Nginx

### Scheduled Tasks:
1. Trial expiration check: Every 1 minute
2. Signal updates: Every 15 minutes

### Admin Accounts:
1. alberttyagi123@gmail.com / SmartRisk@2026!
2. pythonbyvishal@gmail.com / SmartRisk@2026!

---

## 🔍 Monitor Deployment

### GitHub Actions:
https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused/actions

### What to Watch:
- ✅ Each step should show green checkmark
- ⏱️ Total time: 8-12 minutes
- 📊 Deployment summary at the end
- ❌ If any step fails, check logs

---

## ✅ Verify Deployment

### URLs:
- Frontend: http://54.183.119.39
- API: http://54.183.119.39:8000
- Admin: http://54.183.119.39:8000/admin/
- WebSocket: ws://54.183.119.39:8001

### Test:
1. Visit frontend
2. Register new user
3. Check email verification
4. Login to dashboard
5. View live charts
6. Test timeframe switching
7. Verify signals display

---

## 🎯 Current Status

- ✅ Workflow file: `deploy-aws.yml` (active)
- ✅ Old workflow: `deploy.yml` (deleted)
- ✅ Code pushed to GitHub
- ✅ EC2 server ready
- ⏭️ Add GitHub secrets
- ⏭️ Trigger deployment

---

## 📞 Quick Links

- **Repository**: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused
- **Actions**: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused/actions
- **Add Secrets**: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused/settings/secrets/actions
- **Workflow File**: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused/blob/main/.github/workflows/deploy-aws.yml

---

**Last Updated**: May 8, 2026
**Active Workflow**: deploy-aws.yml
**Status**: ✅ Ready to Deploy

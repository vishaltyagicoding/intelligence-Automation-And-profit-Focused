# 🚀 AWS Quick Start Guide

## Prerequisites Checklist

- [ ] AWS Account with billing enabled
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker installed locally
- [ ] GitHub account with repository
- [ ] Domain name (optional but recommended)

## 5-Minute Quick Start

### Step 1: Verify Project is Ready (2 minutes)

```bash
# Run verification script
bash scripts/verify_deployment_ready.sh

# If all checks pass, proceed to Step 2
```

### Step 2: Set Up AWS Infrastructure (30-60 minutes)

**Option A: Using AWS Console (Recommended for first-time)**
1. Follow `AWS_DEPLOYMENT_COMPLETE_GUIDE.md` step by step
2. Create VPC, RDS, ElastiCache, ECR, ECS, ALB
3. Note down all resource IDs and endpoints

**Option B: Using AWS CLI (Advanced)**
```bash
# Follow the commands in AWS_DEPLOYMENT_COMPLETE_GUIDE.md
# Section 2: AWS Infrastructure Setup
```

### Step 3: Configure GitHub Secrets (5 minutes)

Go to: `GitHub Repository → Settings → Secrets and variables → Actions`

Add these secrets:
```
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_REGION=us-east-1
ECR_REPOSITORY_BACKEND=neuraltrade-backend
ECR_REPOSITORY_FRONTEND=neuraltrade-frontend
ECS_SERVICE=neuraltrade-service
ECS_CLUSTER=neuraltrade-cluster
ECS_TASK_DEFINITION=neuraltrade-task
```

### Step 4: Store Secrets in AWS Secrets Manager (10 minutes)

```bash
# Generate strong SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Create Django secrets
aws secretsmanager create-secret \
  --name neuraltrade/django \
  --secret-string '{
    "SECRET_KEY": "<GENERATED_KEY>",
    "DEBUG": "False",
    "ALLOWED_HOSTS": "<YOUR_DOMAIN>,<ALB_DNS>"
  }'

# Create database secrets
aws secretsmanager create-secret \
  --name neuraltrade/database \
  --secret-string '{
    "username": "neuraltrade_admin",
    "password": "<DB_PASSWORD>",
    "host": "<RDS_ENDPOINT>",
    "port": "5432",
    "dbname": "neuraltrade"
  }'

# Create Redis secrets
aws secretsmanager create-secret \
  --name neuraltrade/redis \
  --secret-string '{
    "host": "<REDIS_ENDPOINT>",
    "port": "6379"
  }'
```

### Step 5: Deploy! (10-15 minutes)

```bash
# Commit and push to GitHub
git add .
git commit -m "Deploy to AWS"
git push origin main

# GitHub Actions will automatically:
# 1. Run tests
# 2. Build Docker images
# 3. Push to ECR
# 4. Deploy to ECS
```

**Watch deployment progress:**
- GitHub: `Actions` tab
- AWS Console: `ECS → Clusters → neuraltrade-cluster → Services`

### Step 6: Verify Deployment (5 minutes)

```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --names neuraltrade-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text

# Open in browser
# http://<ALB-DNS-NAME>

# Check logs
aws logs tail /ecs/neuraltrade --follow
```

---

## Common Issues & Quick Fixes

### Issue: Tasks Not Starting

```bash
# Check task status
aws ecs describe-tasks \
  --cluster neuraltrade-cluster \
  --tasks $(aws ecs list-tasks --cluster neuraltrade-cluster --query 'taskArns[0]' --output text)

# Common causes:
# - Image pull errors → Check ECR permissions
# - Health check failures → Check /health/ endpoint
# - Resource limits → Increase CPU/memory in task definition
```

### Issue: Database Connection Failed

```bash
# Test from ECS task
aws ecs execute-command \
  --cluster neuraltrade-cluster \
  --task <TASK_ID> \
  --container backend \
  --interactive \
  --command "/bin/bash"

# Inside container:
python manage.py dbshell

# If fails, check:
# - RDS security group allows ECS security group
# - Port 5432 is open
# - Credentials are correct in Secrets Manager
```

### Issue: WebSocket Not Working

```bash
# Check ALB listener rules
aws elbv2 describe-rules \
  --listener-arn <LISTENER_ARN>

# Ensure /ws/* forwards to backend target group
# Check sticky sessions are enabled
# Increase connection timeout to 300s+
```

### Issue: 503 Service Unavailable

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <TARGET_GROUP_ARN>

# Common causes:
# - Health check path incorrect
# - Security group blocking traffic
# - Container not listening on correct port
```

---

## Manual Deployment (Without GitHub Actions)

If you prefer to deploy manually:

```bash
# 1. Build and push images
bash scripts/aws_deploy.sh

# 2. Update ECS service
aws ecs update-service \
  --cluster neuraltrade-cluster \
  --service neuraltrade-service \
  --force-new-deployment

# 3. Wait for stability
aws ecs wait services-stable \
  --cluster neuraltrade-cluster \
  --services neuraltrade-service
```

---

## Rollback Procedure

If deployment fails:

```bash
# Option 1: Rollback via GitHub
git revert HEAD
git push origin main
# GitHub Actions will automatically deploy previous version

# Option 2: Rollback via AWS CLI
aws ecs update-service \
  --cluster neuraltrade-cluster \
  --service neuraltrade-service \
  --task-definition neuraltrade-task:<PREVIOUS_REVISION>
```

---

## Cost Optimization Tips

### Reduce Costs by 50-70%

1. **Use Fargate Spot** (50-70% cheaper)
   ```bash
   # Update capacity provider strategy
   aws ecs put-cluster-capacity-providers \
     --cluster neuraltrade-cluster \
     --capacity-providers FARGATE_SPOT \
     --default-capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1
   ```

2. **Use RDS Reserved Instances** (40% cheaper)
   - AWS Console → RDS → Reserved Instances → Purchase

3. **Enable Auto-Scaling** (scale down during low traffic)
   ```bash
   # Set up auto-scaling
   aws application-autoscaling register-scalable-target \
     --service-namespace ecs \
     --scalable-dimension ecs:service:DesiredCount \
     --resource-id service/neuraltrade-cluster/neuraltrade-service \
     --min-capacity 1 \
     --max-capacity 4
   ```

4. **Use CloudFront CDN** (reduce data transfer costs)
   - Cache static assets
   - Reduce origin requests

---

## Monitoring & Alerts

### Set Up CloudWatch Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name neuraltrade-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# High memory alarm
aws cloudwatch put-metric-alarm \
  --alarm-name neuraltrade-high-memory \
  --alarm-description "Alert when memory exceeds 80%" \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### View Logs

```bash
# Tail logs in real-time
aws logs tail /ecs/neuraltrade --follow

# Filter by container
aws logs tail /ecs/neuraltrade --follow --filter-pattern "backend"

# View specific time range
aws logs tail /ecs/neuraltrade --since 1h
```

---

## Next Steps After Deployment

1. **Configure Custom Domain**
   - Route 53 → Create hosted zone
   - Add A record pointing to ALB
   - Request SSL certificate in ACM

2. **Enable HTTPS**
   - Certificate Manager → Request certificate
   - Add HTTPS listener to ALB
   - Redirect HTTP to HTTPS

3. **Set Up Monitoring**
   - CloudWatch dashboard
   - CloudWatch alarms
   - SNS notifications

4. **Configure Backups**
   - RDS automated backups (already enabled)
   - Manual snapshots weekly
   - S3 backups for media files

5. **Add Razorpay** (when ready)
   - Uncomment in requirements.txt
   - Add secrets to Secrets Manager
   - Update task definition
   - Deploy

---

## Support & Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **ECS Best Practices**: https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/
- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **Next.js Deployment**: https://nextjs.org/docs/deployment

---

## Estimated Timeline

| Task | Time |
|------|------|
| Verify project ready | 2 minutes |
| Set up AWS infrastructure | 30-60 minutes |
| Configure GitHub secrets | 5 minutes |
| Store secrets in AWS | 10 minutes |
| Deploy via GitHub Actions | 10-15 minutes |
| Verify deployment | 5 minutes |
| **Total** | **~1-2 hours** |

---

## Estimated Monthly Cost

| Service | Cost |
|---------|------|
| ECS Fargate (2 tasks) | $30-50 |
| RDS db.t3.micro | $15-20 |
| ElastiCache t3.micro | $12-15 |
| ALB | $20-25 |
| Data Transfer | $10-20 |
| CloudWatch | $5-10 |
| **Total** | **$92-140/month** |

*With optimizations (Spot, Reserved Instances): $40-70/month*

---

**You're ready to deploy! 🚀**

For detailed instructions, see `AWS_DEPLOYMENT_COMPLETE_GUIDE.md`

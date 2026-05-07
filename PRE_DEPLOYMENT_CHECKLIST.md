# ✅ Pre-Deployment Checklist for AWS

Complete this checklist before deploying to AWS to ensure everything works correctly.

## 🔧 Local Testing

- [ ] **All tests pass locally**
  ```bash
  python manage.py test
  npm run build
  ```

- [ ] **Docker containers build successfully**
  ```bash
  docker-compose build
  docker-compose up -d
  ```

- [ ] **Application works on localhost**
  - [ ] Frontend loads at http://localhost
  - [ ] Backend API responds at http://localhost/api/health
  - [ ] WebSocket connections work
  - [ ] Database migrations applied
  - [ ] Static files collected

- [ ] **No console errors in browser**
  - Open DevTools → Console
  - Check for JavaScript errors
  - Verify API calls succeed

## 🔐 Security

- [ ] **Environment variables configured**
  - [ ] `SECRET_KEY` is strong and unique
  - [ ] `DEBUG=False` in production
  - [ ] Database credentials are secure
  - [ ] No sensitive data in code

- [ ] **Secrets stored in AWS Secrets Manager**
  - [ ] Database credentials
  - [ ] Django SECRET_KEY
  - [ ] Redis connection string
  - [ ] API keys (if any)

- [ ] **Security groups configured**
  - [ ] ALB allows HTTP/HTTPS from internet
  - [ ] ECS tasks only accept traffic from ALB
  - [ ] RDS only accepts traffic from ECS
  - [ ] Redis only accepts traffic from ECS

- [ ] **SSL/TLS certificate obtained**
  - [ ] Certificate created in AWS Certificate Manager
  - [ ] Domain validated
  - [ ] HTTPS listener configured on ALB

## 📦 Dependencies

- [ ] **All dependencies in requirements.txt**
  ```bash
  pip freeze > requirements.txt
  ```

- [ ] **Razorpay removed** (commented out)
  - [ ] `requirements.txt` updated
  - [ ] `.env` file updated
  - [ ] No import errors

- [ ] **Frontend dependencies up to date**
  ```bash
  npm install
  npm audit fix
  ```

## 🗄️ Database

- [ ] **Migrations created and tested**
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

- [ ] **Database backup strategy planned**
  - [ ] RDS automated backups enabled
  - [ ] Backup retention period set
  - [ ] Manual snapshot schedule planned

- [ ] **Initial data prepared**
  - [ ] Superuser creation script ready
  - [ ] Initial fixtures (if any)

## 🌐 Networking

- [ ] **Domain name registered** (if using custom domain)
  - [ ] DNS configured in Route 53
  - [ ] A record points to ALB
  - [ ] CNAME for www subdomain

- [ ] **ALLOWED_HOSTS configured**
  - [ ] Domain name added
  - [ ] ALB DNS name added
  - [ ] No wildcard (*) in production

- [ ] **CORS settings configured**
  - [ ] Frontend domain allowed
  - [ ] API endpoints accessible

## 📊 Monitoring

- [ ] **CloudWatch log groups created**
  - [ ] `/ecs/neuraltrade` log group exists
  - [ ] Log retention period set

- [ ] **CloudWatch alarms configured**
  - [ ] High CPU usage
  - [ ] High memory usage
  - [ ] Database connections
  - [ ] ALB 5xx errors

- [ ] **Health checks configured**
  - [ ] Backend health endpoint works
  - [ ] Frontend health endpoint works
  - [ ] Target group health checks configured

## 🚀 Deployment

- [ ] **ECR repositories created**
  - [ ] neuraltrade-backend
  - [ ] neuraltrade-frontend

- [ ] **ECS cluster created**
  - [ ] Fargate capacity provider enabled
  - [ ] Container Insights enabled

- [ ] **Task definition registered**
  - [ ] CPU and memory limits set
  - [ ] Environment variables configured
  - [ ] Secrets referenced correctly
  - [ ] Health checks defined

- [ ] **ECS service created**
  - [ ] Desired count set (minimum 2 for HA)
  - [ ] Load balancer configured
  - [ ] Auto-scaling enabled
  - [ ] Deployment circuit breaker enabled

- [ ] **GitHub Actions secrets configured**
  - [ ] AWS_ACCESS_KEY_ID
  - [ ] AWS_SECRET_ACCESS_KEY
  - [ ] AWS_REGION
  - [ ] ECR repository names
  - [ ] ECS cluster and service names

## 🧪 Post-Deployment Testing

- [ ] **Application accessible via ALB**
  - [ ] Frontend loads
  - [ ] API responds
  - [ ] WebSocket connects

- [ ] **Database connectivity**
  - [ ] Migrations applied
  - [ ] Data persists
  - [ ] Queries execute

- [ ] **Celery tasks running**
  - [ ] Worker processes active
  - [ ] Beat scheduler running
  - [ ] Tasks execute successfully

- [ ] **Static files served**
  - [ ] CSS loads
  - [ ] JavaScript loads
  - [ ] Images display

- [ ] **Logs visible in CloudWatch**
  - [ ] Application logs
  - [ ] Error logs
  - [ ] Access logs

## 💰 Cost Optimization

- [ ] **Right-sized resources**
  - [ ] ECS task CPU/memory appropriate
  - [ ] RDS instance size appropriate
  - [ ] Redis instance size appropriate

- [ ] **Auto-scaling configured**
  - [ ] ECS service auto-scaling
  - [ ] RDS storage auto-scaling

- [ ] **Unused resources removed**
  - [ ] Old ECR images deleted
  - [ ] Unused EBS volumes deleted
  - [ ] Unused Elastic IPs released

## 📝 Documentation

- [ ] **Deployment guide updated**
  - [ ] AWS_DEPLOYMENT_COMPLETE_GUIDE.md
  - [ ] Environment variables documented
  - [ ] Architecture diagram created

- [ ] **Runbook created**
  - [ ] Common issues and solutions
  - [ ] Rollback procedure
  - [ ] Emergency contacts

- [ ] **Team notified**
  - [ ] Deployment schedule communicated
  - [ ] Maintenance window announced
  - [ ] Rollback plan shared

## 🔄 CI/CD Pipeline

- [ ] **GitHub Actions workflow tested**
  - [ ] Workflow file syntax valid
  - [ ] All jobs execute successfully
  - [ ] Deployment completes

- [ ] **Branch protection configured**
  - [ ] Require pull request reviews
  - [ ] Require status checks to pass
  - [ ] Restrict who can push to main

- [ ] **Rollback strategy defined**
  - [ ] Previous task definition saved
  - [ ] Rollback command documented
  - [ ] Rollback tested

---

## ✅ Final Checks

Before clicking "Deploy":

1. **Backup everything**
   - Database snapshot
   - Code repository tagged
   - Configuration files saved

2. **Notify stakeholders**
   - Deployment time
   - Expected downtime (if any)
   - Contact information

3. **Monitor deployment**
   - Watch CloudWatch logs
   - Check ECS service events
   - Verify health checks pass

4. **Test immediately after deployment**
   - Run smoke tests
   - Check critical functionality
   - Verify data integrity

---

## 🆘 Emergency Rollback

If something goes wrong:

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster neuraltrade-cluster \
  --service neuraltrade-service \
  --task-definition neuraltrade-task:<PREVIOUS_REVISION>

# Or rollback via GitHub Actions
# Revert the commit and push to trigger re-deployment
```

---

## 📞 Support Contacts

- **AWS Support**: https://console.aws.amazon.com/support/
- **GitHub Support**: https://support.github.com/
- **Team Lead**: [Your contact info]
- **DevOps**: [Your contact info]

---

**Remember**: It's better to delay deployment than to deploy with issues!

Good luck! 🚀

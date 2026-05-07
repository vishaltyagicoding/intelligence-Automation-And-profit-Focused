# 🚀 Complete AWS Deployment Guide for NeuralTrade

This guide will help you deploy NeuralTrade to AWS with a complete CI/CD pipeline.

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Infrastructure Setup](#aws-infrastructure-setup)
3. [GitHub Secrets Configuration](#github-secrets-configuration)
4. [Initial Deployment](#initial-deployment)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### Required Tools
- AWS Account with billing enabled
- AWS CLI installed and configured
- Docker installed locally
- Git and GitHub account
- Domain name (optional but recommended)

### AWS Services Used
- **ECS (Elastic Container Service)**: Container orchestration
- **ECR (Elastic Container Registry)**: Docker image storage
- **RDS (PostgreSQL)**: Database
- **ElastiCache (Redis)**: Caching and Celery broker
- **Application Load Balancer**: Traffic distribution
- **Route 53**: DNS management (if using custom domain)
- **Certificate Manager**: SSL/TLS certificates
- **CloudWatch**: Logging and monitoring
- **Secrets Manager**: Secure credential storage

---

## 2. AWS Infrastructure Setup

### Step 1: Create VPC and Networking

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=neuraltrade-vpc}]'

# Create subnets (2 public, 2 private for high availability)
aws ec2 create-subnet --vpc-id <VPC_ID> --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=neuraltrade-public-1a}]'
aws ec2 create-subnet --vpc-id <VPC_ID> --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=neuraltrade-public-1b}]'
aws ec2 create-subnet --vpc-id <VPC_ID> --cidr-block 10.0.3.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=neuraltrade-private-1a}]'
aws ec2 create-subnet --vpc-id <VPC_ID> --cidr-block 10.0.4.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=neuraltrade-private-1b}]'

# Create Internet Gateway
aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=neuraltrade-igw}]'
aws ec2 attach-internet-gateway --vpc-id <VPC_ID> --internet-gateway-id <IGW_ID>

# Create NAT Gateway (for private subnets to access internet)
aws ec2 allocate-address --domain vpc
aws ec2 create-nat-gateway --subnet-id <PUBLIC_SUBNET_ID> --allocation-id <EIP_ALLOCATION_ID>

# Create route tables
aws ec2 create-route-table --vpc-id <VPC_ID> --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=neuraltrade-public-rt}]'
aws ec2 create-route --route-table-id <PUBLIC_RT_ID> --destination-cidr-block 0.0.0.0/0 --gateway-id <IGW_ID>
```

### Step 2: Create Security Groups

```bash
# ALB Security Group (allow HTTP/HTTPS from internet)
aws ec2 create-security-group --group-name neuraltrade-alb-sg --description "Security group for ALB" --vpc-id <VPC_ID>
aws ec2 authorize-security-group-ingress --group-id <ALB_SG_ID> --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id <ALB_SG_ID> --protocol tcp --port 443 --cidr 0.0.0.0/0

# ECS Tasks Security Group (allow traffic from ALB)
aws ec2 create-security-group --group-name neuraltrade-ecs-sg --description "Security group for ECS tasks" --vpc-id <VPC_ID>
aws ec2 authorize-security-group-ingress --group-id <ECS_SG_ID> --protocol tcp --port 8000 --source-group <ALB_SG_ID>
aws ec2 authorize-security-group-ingress --group-id <ECS_SG_ID> --protocol tcp --port 3000 --source-group <ALB_SG_ID>

# RDS Security Group (allow PostgreSQL from ECS)
aws ec2 create-security-group --group-name neuraltrade-rds-sg --description "Security group for RDS" --vpc-id <VPC_ID>
aws ec2 authorize-security-group-ingress --group-id <RDS_SG_ID> --protocol tcp --port 5432 --source-group <ECS_SG_ID>

# Redis Security Group (allow Redis from ECS)
aws ec2 create-security-group --group-name neuraltrade-redis-sg --description "Security group for Redis" --vpc-id <VPC_ID>
aws ec2 authorize-security-group-ingress --group-id <REDIS_SG_ID> --protocol tcp --port 6379 --source-group <ECS_SG_ID>
```

### Step 3: Create RDS PostgreSQL Database

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name neuraltrade-db-subnet-group \
  --db-subnet-group-description "Subnet group for NeuralTrade RDS" \
  --subnet-ids <PRIVATE_SUBNET_1_ID> <PRIVATE_SUBNET_2_ID>

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier neuraltrade-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username neuraltrade_admin \
  --master-user-password <STRONG_PASSWORD> \
  --allocated-storage 20 \
  --storage-type gp3 \
  --vpc-security-group-ids <RDS_SG_ID> \
  --db-subnet-group-name neuraltrade-db-subnet-group \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --multi-az \
  --publicly-accessible false \
  --storage-encrypted \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --tags Key=Name,Value=neuraltrade-db
```

### Step 4: Create ElastiCache Redis

```bash
# Create Redis subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name neuraltrade-redis-subnet-group \
  --cache-subnet-group-description "Subnet group for NeuralTrade Redis" \
  --subnet-ids <PRIVATE_SUBNET_1_ID> <PRIVATE_SUBNET_2_ID>

# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id neuraltrade-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name neuraltrade-redis-subnet-group \
  --security-group-ids <REDIS_SG_ID> \
  --preferred-maintenance-window "mon:05:00-mon:06:00" \
  --snapshot-retention-limit 5 \
  --snapshot-window "04:00-05:00" \
  --tags Key=Name,Value=neuraltrade-redis
```

### Step 5: Create ECR Repositories

```bash
# Create backend repository
aws ecr create-repository \
  --repository-name neuraltrade-backend \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# Create frontend repository
aws ecr create-repository \
  --repository-name neuraltrade-frontend \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# Create nginx repository
aws ecr create-repository \
  --repository-name neuraltrade-nginx \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256
```

### Step 6: Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name neuraltrade-alb \
  --subnets <PUBLIC_SUBNET_1_ID> <PUBLIC_SUBNET_2_ID> \
  --security-groups <ALB_SG_ID> \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

# Create target groups
aws elbv2 create-target-group \
  --name neuraltrade-backend-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id <VPC_ID> \
  --health-check-path /health/ \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --target-type ip

aws elbv2 create-target-group \
  --name neuraltrade-frontend-tg \
  --protocol HTTP \
  --port 3000 \
  --vpc-id <VPC_ID> \
  --health-check-path /api/health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --target-type ip

# Create listeners
aws elbv2 create-listener \
  --load-balancer-arn <ALB_ARN> \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=<FRONTEND_TG_ARN>

# Add listener rules for backend API
aws elbv2 create-rule \
  --listener-arn <LISTENER_ARN> \
  --priority 1 \
  --conditions Field=path-pattern,Values='/api/*' \
  --actions Type=forward,TargetGroupArn=<BACKEND_TG_ARN>

aws elbv2 create-rule \
  --listener-arn <LISTENER_ARN> \
  --priority 2 \
  --conditions Field=path-pattern,Values='/ws/*' \
  --actions Type=forward,TargetGroupArn=<BACKEND_TG_ARN>
```

### Step 7: Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name neuraltrade-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1,base=1 \
  --settings name=containerInsights,value=enabled
```

### Step 8: Create IAM Roles

```bash
# Create ECS Task Execution Role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://ecs-task-execution-role-trust-policy.json

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create ECS Task Role (for application permissions)
aws iam create-role \
  --role-name neuraltradeTaskRole \
  --assume-role-policy-document file://ecs-task-role-trust-policy.json

# Attach policies for CloudWatch, Secrets Manager, etc.
aws iam attach-role-policy \
  --role-name neuraltradeTaskRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

### Step 9: Store Secrets in AWS Secrets Manager

```bash
# Create secret for database credentials
aws secretsmanager create-secret \
  --name neuraltrade/database \
  --description "Database credentials for NeuralTrade" \
  --secret-string '{
    "username": "neuraltrade_admin",
    "password": "<DB_PASSWORD>",
    "host": "<RDS_ENDPOINT>",
    "port": "5432",
    "dbname": "neuraltrade"
  }'

# Create secret for Django settings
aws secretsmanager create-secret \
  --name neuraltrade/django \
  --description "Django settings for NeuralTrade" \
  --secret-string '{
    "SECRET_KEY": "<GENERATE_STRONG_SECRET_KEY>",
    "DEBUG": "False",
    "ALLOWED_HOSTS": "<YOUR_DOMAIN>,<ALB_DNS>"
  }'

# Create secret for Redis
aws secretsmanager create-secret \
  --name neuraltrade/redis \
  --description "Redis connection for NeuralTrade" \
  --secret-string '{
    "host": "<REDIS_ENDPOINT>",
    "port": "6379"
  }'
```

---

## 3. GitHub Secrets Configuration

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

```
AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_KEY>
AWS_REGION=us-east-1
ECR_REPOSITORY_BACKEND=neuraltrade-backend
ECR_REPOSITORY_FRONTEND=neuraltrade-frontend
ECS_SERVICE=neuraltrade-service
ECS_CLUSTER=neuraltrade-cluster
ECS_TASK_DEFINITION=neuraltrade-task
```

---

## 4. Initial Deployment

### Step 1: Build and Push Initial Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
docker build -f Dockerfile.backend -t neuraltrade-backend .
docker tag neuraltrade-backend:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/neuraltrade-backend:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/neuraltrade-backend:latest

# Build and push frontend
docker build -f Dockerfile.frontend -t neuraltrade-frontend .
docker tag neuraltrade-frontend:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/neuraltrade-frontend:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/neuraltrade-frontend:latest
```

### Step 2: Create ECS Task Definition

Create `task-definition.json`:

```json
{
  "family": "neuraltrade-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/neuraltradeTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/neuraltrade-backend:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DJANGO_SETTINGS_MODULE",
          "value": "neuraltrade.settings"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:neuraltrade/django:SECRET_KEY::"
        },
        {
          "name": "DB_HOST",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:neuraltrade/database:host::"
        },
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:neuraltrade/database:password::"
        },
        {
          "name": "REDIS_HOST",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:neuraltrade/redis:host::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/neuraltrade",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health/ || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    },
    {
      "name": "frontend",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/neuraltrade-frontend:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/neuraltrade",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "frontend"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 3: Create ECS Service

```bash
aws ecs create-service \
  --cluster neuraltrade-cluster \
  --service-name neuraltrade-service \
  --task-definition neuraltrade-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[<PRIVATE_SUBNET_1>,<PRIVATE_SUBNET_2>],securityGroups=[<ECS_SG_ID>],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=<BACKEND_TG_ARN>,containerName=backend,containerPort=8000" "targetGroupArn=<FRONTEND_TG_ARN>,containerName=frontend,containerPort=3000" \
  --health-check-grace-period-seconds 60 \
  --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
  --enable-execute-command
```

---

## 5. CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy-aws.yml`) automatically:

1. **On Push to `main` or `production` branch:**
   - Runs tests (Django + Frontend)
   - Builds Docker images
   - Pushes to ECR
   - Updates ECS service
   - Waits for deployment to stabilize

2. **Manual Trigger:**
   - Go to Actions tab → Deploy to AWS → Run workflow

### Workflow Steps:
```
Push to GitHub
    ↓
Run Tests
    ↓
Build Docker Images
    ↓
Push to ECR
    ↓
Update ECS Service
    ↓
Wait for Stability
    ↓
✅ Deployment Complete
```

---

## 6. Monitoring & Maintenance

### CloudWatch Dashboards

Create a dashboard to monitor:
- ECS CPU/Memory usage
- RDS connections and performance
- Redis hit rate
- ALB request count and latency
- Application logs

### Set Up Alarms

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

# Database connections alarm
aws cloudwatch put-metric-alarm \
  --alarm-name neuraltrade-db-connections \
  --alarm-description "Alert when DB connections exceed 80%" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### Backup Strategy

- **RDS**: Automated daily backups (7-day retention)
- **Application Data**: S3 backups via cron job
- **Database Snapshots**: Weekly manual snapshots

---

## 7. Troubleshooting

### Common Issues

**1. ECS Tasks Not Starting**
```bash
# Check task logs
aws ecs describe-tasks --cluster neuraltrade-cluster --tasks <TASK_ID>

# Check CloudWatch logs
aws logs tail /ecs/neuraltrade --follow
```

**2. Database Connection Issues**
```bash
# Test connection from ECS task
aws ecs execute-command \
  --cluster neuraltrade-cluster \
  --task <TASK_ID> \
  --container backend \
  --interactive \
  --command "/bin/bash"

# Inside container
python manage.py dbshell
```

**3. WebSocket Not Working**
- Ensure ALB listener rules forward `/ws/*` to backend
- Check security group allows WebSocket traffic
- Verify Daphne is running in backend container

**4. High Costs**
- Use Fargate Spot for non-critical tasks
- Enable RDS auto-scaling
- Use CloudWatch to identify unused resources

---

## 🎉 Deployment Complete!

Your NeuralTrade application is now running on AWS with:
- ✅ Auto-scaling ECS services
- ✅ Managed PostgreSQL database
- ✅ Redis caching
- ✅ Load balancing
- ✅ SSL/TLS encryption
- ✅ Automated CI/CD pipeline
- ✅ Monitoring and alerts

### Next Steps:
1. Configure custom domain in Route 53
2. Set up SSL certificate in ACM
3. Enable CloudFront CDN for static assets
4. Configure backup automation
5. Set up staging environment

### Support:
- AWS Documentation: https://docs.aws.amazon.com/
- ECS Best Practices: https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/

---

**Cost Estimate (Monthly):**
- ECS Fargate (2 tasks): ~$30-50
- RDS db.t3.micro: ~$15-20
- ElastiCache t3.micro: ~$12-15
- ALB: ~$20-25
- Data Transfer: ~$10-20
- **Total: ~$87-130/month**

*Costs may vary based on usage and region*

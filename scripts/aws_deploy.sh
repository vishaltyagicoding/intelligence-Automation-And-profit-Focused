#!/bin/bash

# NeuralTrade AWS Deployment Script
# This script automates the deployment process to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 NeuralTrade AWS Deployment Script${NC}"
echo "========================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo -e "${GREEN}✅ AWS Account ID: $AWS_ACCOUNT_ID${NC}"
echo -e "${GREEN}✅ AWS Region: $AWS_REGION${NC}"

# ECR repository names
ECR_BACKEND="neuraltrade-backend"
ECR_FRONTEND="neuraltrade-frontend"

# Login to ECR
echo -e "${YELLOW}🔐 Logging in to Amazon ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build backend image
echo -e "${YELLOW}🏗️  Building backend Docker image...${NC}"
docker build -f Dockerfile.backend -t $ECR_BACKEND:latest .

# Tag and push backend
echo -e "${YELLOW}📤 Pushing backend image to ECR...${NC}"
docker tag $ECR_BACKEND:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND:latest

# Build frontend image
echo -e "${YELLOW}🏗️  Building frontend Docker image...${NC}"
docker build -f Dockerfile.frontend -t $ECR_FRONTEND:latest .

# Tag and push frontend
echo -e "${YELLOW}📤 Pushing frontend image to ECR...${NC}"
docker tag $ECR_FRONTEND:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_FRONTEND:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_FRONTEND:latest

# Update ECS service
echo -e "${YELLOW}🔄 Updating ECS service...${NC}"
aws ecs update-service \
    --cluster neuraltrade-cluster \
    --service neuraltrade-service \
    --force-new-deployment \
    --region $AWS_REGION

echo -e "${GREEN}✅ Deployment initiated successfully!${NC}"
echo -e "${YELLOW}⏳ Waiting for service to stabilize...${NC}"

# Wait for service to become stable
aws ecs wait services-stable \
    --cluster neuraltrade-cluster \
    --services neuraltrade-service \
    --region $AWS_REGION

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Check ECS service status: aws ecs describe-services --cluster neuraltrade-cluster --services neuraltrade-service"
echo "2. View logs: aws logs tail /ecs/neuraltrade --follow"
echo "3. Access your application at your ALB DNS name"

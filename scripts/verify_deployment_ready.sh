#!/bin/bash

# ============================================================================
# NeuralTrade AWS Deployment Verification Script
# ============================================================================
# This script verifies that the project is ready for AWS deployment
# Run this before pushing to GitHub to trigger CI/CD pipeline
# ============================================================================

set -e  # Exit on error

echo "🚀 NeuralTrade AWS Deployment Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

echo "1. Checking Python Dependencies..."
echo "-----------------------------------"

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    success "requirements.txt exists"
    
    # Check if Razorpay is commented out
    if grep -q "^#.*razorpay" requirements.txt; then
        success "Razorpay is commented out (as requested)"
    elif ! grep -q "razorpay" requirements.txt; then
        success "Razorpay not in requirements.txt"
    else
        warning "Razorpay is active in requirements.txt (should be commented out)"
    fi
    
    # Check for ML dependencies (should be removed)
    if grep -q "tensorflow\|torch\|scikit-learn\|transformers" requirements.txt; then
        error "ML dependencies found (should be removed)"
    else
        success "No unnecessary ML dependencies"
    fi
else
    error "requirements.txt not found"
fi

echo ""
echo "2. Checking Docker Configuration..."
echo "-----------------------------------"

# Check Dockerfiles
if [ -f "Dockerfile.backend" ]; then
    success "Dockerfile.backend exists"
else
    error "Dockerfile.backend not found"
fi

if [ -f "Dockerfile.frontend" ]; then
    success "Dockerfile.frontend exists"
else
    error "Dockerfile.frontend not found"
fi

# Check .dockerignore
if [ -f ".dockerignore" ]; then
    success ".dockerignore exists"
    
    # Check if it excludes important files
    if grep -q "node_modules" .dockerignore && grep -q "__pycache__" .dockerignore; then
        success ".dockerignore properly configured"
    else
        warning ".dockerignore may be incomplete"
    fi
else
    error ".dockerignore not found"
fi

echo ""
echo "3. Checking Environment Configuration..."
echo "----------------------------------------"

# Check .env file
if [ -f ".env" ]; then
    success ".env file exists"
    
    # Check if Razorpay keys are commented
    if grep -q "^#.*RAZORPAY" .env; then
        success "Razorpay keys are commented out"
    elif ! grep -q "RAZORPAY" .env; then
        success "No Razorpay keys in .env"
    else
        warning "Razorpay keys are active in .env (should be commented out)"
    fi
else
    error ".env file not found"
fi

# Check .env.production
if [ -f ".env.production" ]; then
    success ".env.production exists"
else
    warning ".env.production not found (optional)"
fi

echo ""
echo "4. Checking Frontend Configuration..."
echo "--------------------------------------"

# Check package.json
if [ -f "package.json" ]; then
    success "package.json exists"
else
    error "package.json not found"
fi

# Check next.config.js
if [ -f "next.config.js" ]; then
    success "next.config.js exists"
    
    # Check if standalone output is configured
    if grep -q "output.*standalone" next.config.js; then
        success "Standalone output configured"
    else
        warning "Standalone output not configured"
    fi
else
    error "next.config.js not found"
fi

# Check if node_modules exists (should be in .dockerignore)
if [ -d "node_modules" ]; then
    warning "node_modules directory exists (will be excluded by .dockerignore)"
else
    success "No node_modules directory"
fi

echo ""
echo "5. Checking Backend Configuration..."
echo "------------------------------------"

# Check Django settings
if [ -f "neuraltrade/settings.py" ]; then
    success "Django settings.py exists"
    
    # Check CORS configuration
    if grep -q "CORS_ALLOW_ALL_ORIGINS.*True" neuraltrade/settings.py; then
        success "CORS configured for production (behind nginx)"
    else
        warning "CORS may need configuration"
    fi
    
    # Check custom user model
    if grep -q "AUTH_USER_MODEL.*users.User" neuraltrade/settings.py; then
        success "Custom user model configured"
    else
        error "Custom user model not configured"
    fi
else
    error "Django settings.py not found"
fi

# Check if migrations exist
if [ -d "users/migrations" ] && [ -d "payments/migrations" ]; then
    success "Migration directories exist"
else
    warning "Some migration directories may be missing"
fi

echo ""
echo "6. Checking CI/CD Configuration..."
echo "----------------------------------"

# Check GitHub Actions workflow
if [ -f ".github/workflows/deploy-aws.yml" ]; then
    success "GitHub Actions workflow exists"
else
    error "GitHub Actions workflow not found"
fi

# Check docker-compose files
if [ -f "docker-compose.yml" ]; then
    success "docker-compose.yml exists (for local dev)"
else
    warning "docker-compose.yml not found"
fi

if [ -f "docker-compose.prod.yml" ]; then
    success "docker-compose.prod.yml exists"
else
    warning "docker-compose.prod.yml not found"
fi

echo ""
echo "7. Checking Documentation..."
echo "----------------------------"

# Check deployment documentation
if [ -f "AWS_DEPLOYMENT_COMPLETE_GUIDE.md" ]; then
    success "AWS deployment guide exists"
else
    warning "AWS deployment guide not found"
fi

if [ -f "PRE_DEPLOYMENT_CHECKLIST.md" ]; then
    success "Pre-deployment checklist exists"
else
    warning "Pre-deployment checklist not found"
fi

if [ -f "DEPLOYMENT_READY.md" ]; then
    success "Deployment ready guide exists"
else
    warning "Deployment ready guide not found"
fi

echo ""
echo "8. Checking Nginx Configuration..."
echo "----------------------------------"

if [ -f "nginx/nginx.conf" ]; then
    success "Nginx configuration exists"
    
    # Check rate limiting
    if grep -q "limit_req_zone" nginx/nginx.conf; then
        success "Rate limiting configured"
    else
        warning "Rate limiting not configured"
    fi
    
    # Check WebSocket support
    if grep -q "proxy_set_header Upgrade" nginx/nginx.conf; then
        success "WebSocket support configured"
    else
        error "WebSocket support not configured"
    fi
else
    error "Nginx configuration not found"
fi

echo ""
echo "9. Checking Scripts..."
echo "----------------------"

# Check startup scripts
if [ -f "scripts/start_server.sh" ]; then
    success "Backend startup script exists"
    
    # Check if executable
    if [ -x "scripts/start_server.sh" ]; then
        success "Startup script is executable"
    else
        warning "Startup script is not executable (will be fixed in Dockerfile)"
    fi
else
    error "Backend startup script not found"
fi

echo ""
echo "10. Testing Docker Build (Optional)..."
echo "---------------------------------------"

# Ask user if they want to test Docker build
read -p "Do you want to test Docker builds? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Testing backend Docker build..."
    if docker build -f Dockerfile.backend -t neuraltrade-backend-test . > /dev/null 2>&1; then
        success "Backend Docker build successful"
    else
        error "Backend Docker build failed"
    fi
    
    echo "Testing frontend Docker build..."
    if docker build -f Dockerfile.frontend -t neuraltrade-frontend-test . > /dev/null 2>&1; then
        success "Frontend Docker build successful"
    else
        error "Frontend Docker build failed"
    fi
else
    warning "Skipped Docker build test"
fi

echo ""
echo "=========================================="
echo "📊 Verification Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Your project is ready for AWS deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review PRE_DEPLOYMENT_CHECKLIST.md"
    echo "2. Set up AWS infrastructure (see AWS_DEPLOYMENT_COMPLETE_GUIDE.md)"
    echo "3. Configure GitHub secrets"
    echo "4. Push to GitHub to trigger deployment"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Please fix the errors before deploying${NC}"
    echo ""
    echo "Review the errors above and fix them before deployment."
    echo ""
    exit 1
fi

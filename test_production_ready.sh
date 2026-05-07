#!/bin/bash

###############################################################################
# SmartRisk Production Readiness Test
# Comprehensive system check before AWS deployment
###############################################################################

echo "=========================================================================="
echo "🧪 SmartRisk Production Readiness Test"
echo "=========================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test function
test_check() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "📊 Service Health Checks"
echo "----------------------------------------"

# Check Docker services
test_check "PostgreSQL running" "docker-compose ps db | grep -q 'Up'"
test_check "Redis running" "docker-compose ps redis | grep -q 'Up'"
test_check "Django running" "docker-compose ps django | grep -q 'Up'"
test_check "Celery Worker running" "docker-compose ps celery_worker | grep -q 'Up'"
test_check "Celery Beat running" "docker-compose ps celery_beat | grep -q 'Up'"
test_check "Frontend running" "docker-compose ps frontend | grep -q 'Up'"
test_check "Nginx running" "docker-compose ps nginx | grep -q 'Up'"

echo ""
echo "🔌 Connectivity Checks"
echo "----------------------------------------"

# Check service connectivity
test_check "Redis PING" "docker-compose exec -T redis redis-cli ping | grep -q 'PONG'"
test_check "Django health endpoint" "curl -s http://localhost:8000/health/ | grep -q 'healthy'"
test_check "Frontend accessible" "curl -s http://localhost:3000 | grep -q 'html'"

echo ""
echo "⚙️ Celery Task Checks"
echo "----------------------------------------"

# Check Celery tasks
test_check "Celery Beat scheduling" "docker-compose logs --tail=50 celery_beat | grep -q 'Scheduler: Sending'"
test_check "Celery Worker processing" "docker-compose logs --tail=50 celery_worker | grep -q 'succeeded'"
test_check "Trial expiration task exists" "docker-compose exec -T django python manage.py shell -c 'from django_celery_beat.models import PeriodicTask; exit(0 if PeriodicTask.objects.filter(name=\"check-expired-subscriptions\").exists() else 1)'"

echo ""
echo "💾 Database Checks"
echo "----------------------------------------"

# Check database
test_check "Database accessible" "docker-compose exec -T db psql -U neuraltrade -d neuraltrade -c 'SELECT 1;' 2>/dev/null | grep -q '1'"
test_check "Users table exists" "docker-compose exec -T db psql -U neuraltrade -d neuraltrade -c 'SELECT COUNT(*) FROM users_user;' 2>/dev/null | grep -q '[0-9]'"
test_check "Subscriptions table exists" "docker-compose exec -T db psql -U neuraltrade -d neuraltrade -c 'SELECT COUNT(*) FROM payments_subscription;' 2>/dev/null | grep -q '[0-9]'"

echo ""
echo "🔐 Security Checks"
echo "----------------------------------------"

# Check environment
test_check ".env file exists" "[ -f .env ]"
test_check "SECRET_KEY configured" "grep -q 'SECRET_KEY=' .env"
test_check "EMAIL configured" "grep -q 'EMAIL_HOST_USER=' .env"

echo ""
echo "📁 File Checks"
echo "----------------------------------------"

# Check important files
test_check ".gitignore exists" "[ -f .gitignore ]"
test_check "docker-compose.yml exists" "[ -f docker-compose.yml ]"
test_check "Dockerfile exists" "[ -f Dockerfile ]"
test_check "requirements.txt exists" "[ -f requirements.txt ]"
test_check "deploy_aws.sh exists" "[ -f deploy_aws.sh ]"

echo ""
echo "=========================================================================="
echo "📊 Test Results"
echo "=========================================================================="
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! System is PRODUCTION READY!${NC}"
    echo ""
    echo "✅ Ready to deploy to AWS EC2"
    echo "✅ Run: sudo bash deploy_aws.sh"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please fix issues before deployment.${NC}"
    exit 1
fi

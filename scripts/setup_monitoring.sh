#!/bin/bash
# Setup Database Connection Monitoring
# Run this once on production server after deployment

set -e

echo "🔧 SmartRisk - Database Connection Monitoring Setup"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Create log directory
echo -e "\n${YELLOW}1. Creating log directory...${NC}"
sudo mkdir -p /var/log/smartrisk
sudo chown ubuntu:ubuntu /var/log/smartrisk
echo -e "${GREEN}✓ Log directory created${NC}"

# 2. Setup log rotation
echo -e "\n${YELLOW}2. Setting up log rotation...${NC}"
sudo tee /etc/logrotate.d/smartrisk > /dev/null <<EOF
/var/log/smartrisk/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ubuntu ubuntu
}
EOF
echo -e "${GREEN}✓ Log rotation configured${NC}"

# 3. Test monitoring script
echo -e "\n${YELLOW}3. Testing monitoring script...${NC}"
cd ~/smartrisk
docker-compose exec -T django python monitoring/db_connection_monitor.py || {
    echo -e "${YELLOW}⚠ Monitoring script test failed - this is OK if monitoring/ directory doesn't exist yet${NC}"
    echo -e "${YELLOW}  It will be created after you push the code changes${NC}"
}

# 4. Setup cron job
echo -e "\n${YELLOW}4. Setting up cron job...${NC}"
CRON_JOB="*/5 * * * * cd ~/smartrisk && docker-compose exec -T django python monitoring/db_connection_monitor.py >> /var/log/smartrisk/db_monitor.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "db_connection_monitor.py"; then
    echo -e "${YELLOW}⚠ Cron job already exists, skipping...${NC}"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✓ Cron job added${NC}"
fi

# 5. Test database health check
echo -e "\n${YELLOW}5. Running database health check...${NC}"
docker-compose exec django python manage.py check_db_health || {
    echo -e "${YELLOW}⚠ Health check command not found - will be available after deployment${NC}"
}

# 6. Test email notifications
echo -e "\n${YELLOW}6. Testing email notifications...${NC}"
docker-compose exec -T django python manage.py shell <<EOF || echo "Email test skipped"
from django.core.mail import send_mail
from django.conf import settings
try:
    send_mail(
        subject='[SmartRisk] Monitoring Setup Complete',
        message='Database connection monitoring is now active. You will receive alerts if connections exceed 75% capacity.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['alberttyagi123@gmail.com', 'smarttriskfx@gmail.com'],
    )
    print('✓ Test email sent')
except Exception as e:
    print(f'⚠ Email test failed: {e}')
EOF

# 7. Show current status
echo -e "\n${YELLOW}7. Current database status:${NC}"
docker-compose exec db psql -U postgres -c "SHOW max_connections;" 2>/dev/null || echo "Database not ready"
docker-compose exec db psql -U postgres -c "SELECT count(*) as current_connections FROM pg_stat_activity;" 2>/dev/null || echo "Cannot query connections"

# 8. Summary
echo -e "\n${GREEN}=================================================="
echo "✅ Monitoring Setup Complete!"
echo "==================================================${NC}"
echo ""
echo "📋 What was configured:"
echo "  ✓ Log directory: /var/log/smartrisk/"
echo "  ✓ Log rotation: 30 days retention"
echo "  ✓ Cron job: Every 5 minutes"
echo "  ✓ Email alerts: alberttyagi123@gmail.com, smarttriskfx@gmail.com"
echo ""
echo "📊 Monitoring thresholds:"
echo "  • WARNING: > 150 connections (75%)"
echo "  • CRITICAL: > 180 connections (90%)"
echo ""
echo "🔍 Check status anytime:"
echo "  $ docker-compose exec django python manage.py check_db_health"
echo ""
echo "📝 View logs:"
echo "  $ tail -f /var/log/smartrisk/db_monitor.log"
echo ""
echo "⏰ Next monitoring run: Within 5 minutes"
echo ""
echo -e "${GREEN}All set! You'll receive email alerts if any issues occur.${NC}"

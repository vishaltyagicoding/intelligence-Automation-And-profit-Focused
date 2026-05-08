#!/bin/bash

echo "=========================================="
echo "🔒 Automatic SSL Setup for SmartRisk"
echo "=========================================="
echo ""

# Step 1: Pull latest code
echo "📥 Step 1: Pulling latest code from GitHub..."
cd /home/ubuntu/smartrisk
git pull origin main
echo "✅ Code updated"
echo ""

# Step 2: Make SSL script executable
echo "🔧 Step 2: Making SSL script executable..."
chmod +x /home/ubuntu/smartrisk/scripts/setup_ssl.sh
echo "✅ Script is executable"
echo ""

# Step 3: Run SSL setup
echo "🔒 Step 3: Setting up SSL certificate..."
echo "This will take 2-3 minutes..."
/home/ubuntu/smartrisk/scripts/setup_ssl.sh

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully!"
else
    echo "❌ SSL setup failed. Please check the errors above."
    exit 1
fi

echo ""

# Step 4: Restart services with SSL
echo "🔄 Step 4: Restarting services with SSL enabled..."
cd /home/ubuntu/smartrisk
docker-compose down
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 30

echo ""
echo "📊 Checking service status..."
docker-compose ps

echo ""
echo "=========================================="
echo "✅ SSL SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "🌐 Your site is now available at:"
echo "   https://smartriskfx.com"
echo "   https://www.smartriskfx.com"
echo ""
echo "🔒 SSL Certificate:"
echo "   ✅ Installed and active"
echo "   ✅ Auto-renewal configured"
echo ""
echo "Test your site now! 🚀"
echo ""

#!/bin/bash

# SSL Setup Script for SmartRisk
# Domain: smartriskfx.com
# This script installs Let's Encrypt SSL certificate

set -e

DOMAIN="smartriskfx.com"
WWW_DOMAIN="www.smartriskfx.com"
EMAIL="alberttyagi123@gmail.com"

echo "=========================================="
echo "🔒 SSL Setup for SmartRisk"
echo "=========================================="
echo ""
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt-get update -qq

# Install Certbot
echo "📦 Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx

# Stop nginx temporarily
echo "🛑 Stopping Nginx..."
cd ~/smartrisk
docker-compose stop nginx

# Get SSL certificate
echo "🔒 Obtaining SSL certificate from Let's Encrypt..."
certbot certonly --standalone \
    --preferred-challenges http \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d $WWW_DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully!"
else
    echo "❌ Failed to obtain SSL certificate"
    echo "Please make sure:"
    echo "  1. DNS records are pointing to this server"
    echo "  2. Ports 80 and 443 are open"
    echo "  3. Domain is accessible"
    exit 1
fi

# Copy certificates to nginx directory
echo "📋 Copying certificates..."
mkdir -p ~/smartrisk/nginx/ssl
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ~/smartrisk/nginx/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ~/smartrisk/nginx/ssl/
chmod 644 ~/smartrisk/nginx/ssl/fullchain.pem
chmod 644 ~/smartrisk/nginx/ssl/privkey.pem

# Setup auto-renewal
echo "⏰ Setting up auto-renewal..."
(crontab -l 2>/dev/null; echo "0 0 * * 0 certbot renew --quiet --deploy-hook 'cd ~/smartrisk && docker-compose restart nginx'") | crontab -

echo ""
echo "=========================================="
echo "✅ SSL Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update nginx configuration to use SSL"
echo "2. Restart nginx container"
echo ""
echo "Certificates location:"
echo "  - Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "  - Private Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo ""
echo "Auto-renewal: Configured (runs weekly)"
echo ""

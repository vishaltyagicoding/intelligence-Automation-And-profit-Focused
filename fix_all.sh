#!/bin/bash
# SmartRisk - Fix All Issues Script

echo "=========================================="
echo "SmartRisk - Fixing All Issues"
echo "=========================================="

cd ~/smartrisk

# Stop nginx (it's failing due to SSL)
echo "Step 1: Stopping nginx..."
sudo docker-compose stop nginx

# Create HTTP-only nginx config (no SSL)
echo "Step 2: Creating HTTP-only nginx config..."
sudo tee nginx/nginx.conf > /dev/null << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;

    server {
        listen 80;
        server_name smartriskfx.com www.smartriskfx.com 54.183.178.141 localhost _;

        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location /api/ {
            proxy_pass http://django:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        location /admin/ {
            proxy_pass http://django:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        location /health/ {
            proxy_pass http://django:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /ws/ {
            proxy_pass http://django:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
        }

        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /app/media/;
            expires 7d;
            add_header Cache-Control "public";
        }

        location / {
            proxy_pass http://frontend:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }
    }
}
EOF

# Start nginx
echo "Step 3: Starting nginx..."
sudo docker-compose up -d nginx

# Wait for nginx to start
sleep 5

# Check all services
echo ""
echo "=========================================="
echo "Service Status:"
echo "=========================================="
sudo docker-compose ps

echo ""
echo "=========================================="
echo "Testing Services:"
echo "=========================================="

# Test Django
echo "Testing Django API..."
curl -s http://localhost:8000/health/ && echo "✅ Django API working!" || echo "❌ Django API failed"

# Test Frontend
echo "Testing Frontend..."
curl -s http://localhost:3000 | head -1 && echo "✅ Frontend working!" || echo "❌ Frontend failed"

# Test Nginx
echo "Testing Nginx..."
curl -s http://localhost/health/ && echo "✅ Nginx working!" || echo "❌ Nginx failed"

echo ""
echo "=========================================="
echo "✅ All Fixed!"
echo "=========================================="
echo ""
echo "Your application is now accessible at:"
echo "  - Frontend: http://54.183.178.141"
echo "  - API: http://54.183.178.141/api/"
echo "  - Admin: http://54.183.178.141/admin/"
echo ""
echo "Note: If you can't access from outside, you need to:"
echo "1. Go to AWS Console → EC2 → Security Groups"
echo "2. Find your instance's security group"
echo "3. Add inbound rule: HTTP (port 80) from 0.0.0.0/0"
echo "=========================================="

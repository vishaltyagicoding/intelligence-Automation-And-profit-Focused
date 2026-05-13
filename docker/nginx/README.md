# Nginx Configuration

## Overview
Nginx serves as the reverse proxy and SSL termination point for SmartRisk. It handles HTTPS, routes requests to frontend/backend, and manages WebSocket connections.

## Configuration File
Location: `nginx/nginx.conf`

## Main Configuration

### HTTP → HTTPS Redirect
```nginx
server {
    listen 80;
    server_name smartriskfx.com;
    return 301 https://$server_name$request_uri;
}
```

**Purpose**: Force all traffic to HTTPS

### HTTPS Server Block
```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name smartriskfx.com;

    ssl_certificate /etc/letsencrypt/live/smartriskfx.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smartriskfx.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}
```

## Routing Rules

### Frontend (/)
```nginx
location / {
    proxy_pass http://frontend:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Routes**: All paths except `/api/` and `/ws/`
**Target**: Next.js frontend on port 3000

### Backend API (/api/)
```nginx
location /api/ {
    proxy_pass http://django:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Routes**: All `/api/*` paths
**Target**: Django backend on port 8000

### WebSocket (/ws/)
```nginx
location /ws/ {
    proxy_pass http://django:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket timeouts
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
}
```

**Routes**: All `/ws/*` paths
**Target**: Django Channels on port 8000
**Special**: WebSocket upgrade headers

### Static Files (/static/)
```nginx
location /static/ {
    alias /app/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

**Routes**: Django static files
**Caching**: 30 days

### Admin (/admin/)
```nginx
location /admin/ {
    proxy_pass http://django:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**Routes**: Django admin interface
**Target**: Django backend

## SSL Configuration

### Certificate Location
```
/etc/letsencrypt/live/smartriskfx.com/fullchain.pem
/etc/letsencrypt/live/smartriskfx.com/privkey.pem
```

### SSL Protocols
- TLSv1.2
- TLSv1.3

### SSL Ciphers
High-security ciphers only, no weak ciphers

## Performance Optimization

### Gzip Compression
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript 
           application/x-javascript application/xml+rss 
           application/json application/javascript;
```

### Client Body Size
```nginx
client_max_body_size 10M;
```

### Timeouts
```nginx
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

## Testing Configuration

### Syntax Check
```bash
sudo docker-compose exec nginx nginx -t
```

### Reload Configuration
```bash
sudo docker-compose exec nginx nginx -s reload
```

### Restart Nginx
```bash
sudo docker-compose restart nginx
```

## Common Issues

### 502 Bad Gateway
**Cause**: Backend not responding
**Solution**: Check Django container is running
```bash
sudo docker-compose ps django
sudo docker-compose logs django
```

### 504 Gateway Timeout
**Cause**: Request taking too long
**Solution**: Increase timeout values
```nginx
proxy_read_timeout 120s;
```

### WebSocket Connection Failed
**Cause**: Missing upgrade headers
**Solution**: Verify WebSocket configuration
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### SSL Certificate Error
**Cause**: Certificate expired or not found
**Solution**: Renew certificate
```bash
sudo certbot renew
sudo docker-compose restart nginx
```

## Logs

### Access Log
```bash
sudo docker-compose exec nginx tail -f /var/log/nginx/access.log
```

### Error Log
```bash
sudo docker-compose exec nginx tail -f /var/log/nginx/error.log
```

### View Logs via Docker
```bash
sudo docker-compose logs -f nginx
```

## Security Headers

### Recommended Headers
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

## Monitoring

### Check Nginx Status
```bash
curl -I https://smartriskfx.com
```

### Test Backend Routing
```bash
curl https://smartriskfx.com/api/health/
```

### Test WebSocket
```bash
wscat -c wss://smartriskfx.com/ws/market/BTCUSD/15m/
```

## Backup Configuration
```bash
# Backup current config
sudo docker-compose exec nginx cat /etc/nginx/nginx.conf > nginx_backup.conf

# Restore from backup
sudo docker cp nginx_backup.conf nginx:/etc/nginx/nginx.conf
sudo docker-compose restart nginx
```

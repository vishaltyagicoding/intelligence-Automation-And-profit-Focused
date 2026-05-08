# 🔒 SSL Setup Guide for SmartRisk

## Your Domain: smartriskfx.com

This guide will help you set up FREE SSL certificate from Let's Encrypt to make your site secure (HTTPS with green padlock 🔒).

---

## ✅ Prerequisites Checklist

Before starting, make sure:
- [x] Domain registered: smartriskfx.com (Hostinger)
- [x] EC2 server running: 54.183.119.39
- [x] Application deployed and working
- [ ] DNS records configured (we'll do this now)

---

## 📋 Step 1: Configure DNS Records in Hostinger

### Go to Hostinger Dashboard:
1. Login to Hostinger: https://hpanel.hostinger.com
2. Go to **Domains** → **smartriskfx.com**
3. Click **DNS / Nameservers**
4. Click **Manage DNS Records**

### Add These DNS Records:

| Type | Name | Points to | TTL |
|------|------|-----------|-----|
| A | @ | 54.183.119.39 | 3600 |
| A | www | 54.183.119.39 | 3600 |

**What this does:**
- `smartriskfx.com` → points to your EC2 server
- `www.smartriskfx.com` → points to your EC2 server

### Save and Wait
- Click **Save** or **Add Record**
- Wait 5-30 minutes for DNS propagation

### Verify DNS is Working:
```bash
# On your local computer, run:
ping smartriskfx.com

# Should show: 54.183.119.39
```

Or visit: https://dnschecker.org/#A/smartriskfx.com

---

## 🔒 Step 2: Install SSL Certificate on EC2

### SSH into your EC2 server:
```bash
ssh ubuntu@54.183.119.39
```

### Run the SSL setup script:
```bash
cd ~/smartrisk

# Make script executable
chmod +x scripts/setup_ssl.sh

# Run the script (this will take 2-3 minutes)
sudo ./scripts/setup_ssl.sh
```

### What the script does:
1. ✅ Installs Certbot (Let's Encrypt client)
2. ✅ Stops Nginx temporarily
3. ✅ Obtains SSL certificate for smartriskfx.com and www.smartriskfx.com
4. ✅ Copies certificates to nginx directory
5. ✅ Sets up auto-renewal (certificates renew automatically every 90 days)

---

## 🚀 Step 3: Deploy Updated Configuration

The updated nginx configuration and docker-compose files are already in your repository.

### Pull the latest changes and restart:
```bash
cd ~/smartrisk

# Pull latest code
git pull origin main

# Restart services with new configuration
sudo docker-compose down
sudo docker-compose up -d

# Check if everything is running
sudo docker-compose ps
```

---

## ✅ Step 4: Verify SSL is Working

### Test your site:
1. Open browser and go to: **https://smartriskfx.com**
2. You should see:
   - 🔒 Green padlock in address bar
   - "Secure" or "Connection is secure"
   - No "Not secure" warning

### Test both URLs:
- https://smartriskfx.com ✅
- https://www.smartriskfx.com ✅
- http://smartriskfx.com → should redirect to HTTPS ✅

---

## 🔧 Troubleshooting

### Issue: "DNS not pointing to server"

**Check DNS:**
```bash
nslookup smartriskfx.com
# Should show: 54.183.119.39
```

**Solution:** Wait longer for DNS propagation (up to 48 hours, usually 5-30 minutes)

---

### Issue: "Certificate validation failed"

**Check if ports are open:**
```bash
sudo netstat -tulpn | grep -E ':(80|443)'
```

**Solution:** Make sure ports 80 and 443 are open in AWS Security Group:
- Go to AWS Console → EC2 → Security Groups
- Add inbound rules for ports 80 and 443

---

### Issue: "Nginx won't start"

**Check nginx logs:**
```bash
sudo docker-compose logs nginx
```

**Common causes:**
- SSL certificate files not found
- Nginx configuration syntax error

**Solution:**
```bash
# Test nginx configuration
sudo docker-compose exec nginx nginx -t

# If error, check the config file
cat ~/smartrisk/nginx/nginx.conf
```

---

### Issue: "Certificate files not found"

**Check if certificates exist:**
```bash
ls -la /etc/letsencrypt/live/smartriskfx.com/
ls -la ~/smartrisk/nginx/ssl/
```

**Solution:** Re-run the SSL setup script:
```bash
sudo ./scripts/setup_ssl.sh
```

---

## 🔄 SSL Certificate Auto-Renewal

Your SSL certificates are valid for 90 days and will auto-renew.

### Check renewal status:
```bash
sudo certbot renew --dry-run
```

### Manual renewal (if needed):
```bash
sudo certbot renew
sudo docker-compose restart nginx
```

### Renewal is automated via cron job:
```bash
# Check cron job
crontab -l

# Should show:
# 0 0 * * 0 certbot renew --quiet --deploy-hook 'cd ~/smartrisk && docker-compose restart nginx'
```

This runs every Sunday at midnight and automatically renews certificates if needed.

---

## 📊 What Changed

### Files Created/Updated:
1. **scripts/setup_ssl.sh** - Automated SSL setup script
2. **nginx/nginx.conf** - Updated with HTTPS configuration
3. **docker-compose.yml** - Added SSL certificate volume mount

### New Features:
- ✅ HTTPS enabled (port 443)
- ✅ HTTP → HTTPS redirect (port 80 redirects to 443)
- ✅ SSL/TLS security headers
- ✅ Auto-renewal configured
- ✅ Modern SSL protocols (TLSv1.2, TLSv1.3)

---

## 🎯 Quick Command Reference

```bash
# Check SSL certificate expiry
sudo certbot certificates

# Test SSL configuration
curl -I https://smartriskfx.com

# Check nginx status
sudo docker-compose ps nginx

# View nginx logs
sudo docker-compose logs nginx --tail=50

# Restart nginx
sudo docker-compose restart nginx

# Renew certificates manually
sudo certbot renew
sudo docker-compose restart nginx
```

---

## 🌐 After SSL Setup

Your site will be accessible at:
- **https://smartriskfx.com** ✅ (Secure)
- **https://www.smartriskfx.com** ✅ (Secure)
- **http://smartriskfx.com** → Redirects to HTTPS
- **http://www.smartriskfx.com** → Redirects to HTTPS

Admin panel:
- **https://smartriskfx.com/admin/** ✅ (Secure)

API:
- **https://smartriskfx.com/api/** ✅ (Secure)

---

## 🎉 Success Indicators

You'll know SSL is working when:
1. ✅ Browser shows green padlock 🔒
2. ✅ URL starts with "https://"
3. ✅ No "Not secure" warning
4. ✅ Certificate is valid (click padlock to view)
5. ✅ HTTP automatically redirects to HTTPS

---

## 📞 Support

If you encounter issues:
1. Check DNS propagation: https://dnschecker.org
2. Verify ports 80 and 443 are open in AWS Security Group
3. Check nginx logs: `sudo docker-compose logs nginx`
4. Re-run setup script: `sudo ./scripts/setup_ssl.sh`

---

**Domain**: smartriskfx.com  
**SSL Provider**: Let's Encrypt (Free)  
**Certificate Validity**: 90 days (auto-renews)  
**Status**: Ready to configure

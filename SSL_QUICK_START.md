# 🔒 SSL Quick Start - 3 Simple Steps

## Make Your Site Secure (HTTPS) in 15 Minutes!

---

## ✅ Step 1: Configure DNS in Hostinger (5 minutes)

### 1. Login to Hostinger:
👉 Go to: https://hpanel.hostinger.com

### 2. Navigate to DNS Settings:
- Click **Domains**
- Click **smartriskfx.com**
- Click **DNS / Nameservers**
- Click **Manage DNS Records**

### 3. Add These 2 Records:

**Record 1:**
- Type: `A`
- Name: `@`
- Points to: `54.183.119.39`
- TTL: `3600`

**Record 2:**
- Type: `A`
- Name: `www`
- Points to: `54.183.119.39`
- TTL: `3600`

### 4. Save and Wait:
- Click **Save** or **Add Record**
- Wait 5-10 minutes for DNS to update

### 5. Verify DNS is Working:
Open this link: https://dnschecker.org/#A/smartriskfx.com

Should show: **54.183.119.39** ✅

---

## 🔒 Step 2: Install SSL Certificate (5 minutes)

### 1. SSH into your server:
```bash
ssh ubuntu@54.183.119.39
```

### 2. Go to project directory:
```bash
cd ~/smartrisk
```

### 3. Pull latest code:
```bash
git pull origin main
```

### 4. Make script executable:
```bash
chmod +x scripts/setup_ssl.sh
```

### 5. Run SSL setup:
```bash
sudo ./scripts/setup_ssl.sh
```

**What you'll see:**
- Installing Certbot...
- Stopping Nginx...
- Obtaining SSL certificate...
- ✅ SSL certificate obtained successfully!

**This takes 2-3 minutes.**

---

## 🚀 Step 3: Restart Services (2 minutes)

### 1. Still in SSH, run:
```bash
cd ~/smartrisk
sudo docker-compose down
sudo docker-compose up -d
```

### 2. Wait 30 seconds, then check:
```bash
sudo docker-compose ps
```

All services should show "Up" ✅

---

## 🎉 Done! Test Your Secure Site

### Open your browser and visit:
👉 **https://smartriskfx.com**

You should see:
- 🔒 **Green padlock** in address bar
- **"Secure"** or **"Connection is secure"**
- **No "Not secure" warning**

### Also test:
- https://www.smartriskfx.com ✅
- http://smartriskfx.com (should redirect to HTTPS) ✅

---

## 🎯 Summary

| Step | What | Time |
|------|------|------|
| 1 | Add DNS records in Hostinger | 5 min |
| 2 | Run SSL setup script on EC2 | 5 min |
| 3 | Restart Docker services | 2 min |
| **Total** | **Your site is secure!** | **12 min** |

---

## ❓ Troubleshooting

### DNS not working?
- Wait longer (up to 30 minutes)
- Check: https://dnschecker.org/#A/smartriskfx.com

### SSL script fails?
- Make sure DNS is pointing to server first
- Check ports 80 and 443 are open in AWS Security Group

### Nginx won't start?
```bash
sudo docker-compose logs nginx
```

### Need help?
Read the detailed guide: **SSL_SETUP_GUIDE.md**

---

## 🔄 Auto-Renewal

Your SSL certificate will automatically renew every 90 days. No action needed! ✅

---

**Ready? Start with Step 1!** 🚀

# Nginx Rate Limits - Quick Reference Card

## 📊 Current Rate Limits

| Endpoint | Rate Limit | Burst | Purpose |
|----------|-----------|-------|---------|
| **General API** (`/api/*`) | 100 req/min | 20 | Prevent API abuse |
| **Authentication** (`/api/auth/*`, `/api/login/*`) | 10 req/min | 3 | Prevent brute force |
| **Signal History** (`/api/trading/signal-history/*`) | 30 req/min | 10 | Reduce DB load |
| **WebSocket** (`/ws/*`) | 10 connections | - | Prevent connection exhaustion |
| **All Endpoints** | 10 concurrent | - | General protection |

---

## 🎯 What This Means

### For Normal Users ✅
- **Homepage visits**: Unlimited
- **API calls**: 100 per minute (plenty for normal use)
- **Login attempts**: 10 per minute (enough for legitimate users)
- **Signal history**: 30 per minute (1 every 2 seconds)
- **WebSocket connections**: 10 simultaneous (more than enough)

### For Attackers ❌
- **DDoS attacks**: Blocked after 120 requests/minute
- **Brute force**: Blocked after 13 login attempts/minute
- **API scraping**: Blocked after 120 requests/minute
- **WebSocket spam**: Blocked after 10 connections

---

## 🔧 How to Adjust Limits

### 1. Edit `nginx/nginx.conf`
Find the rate limit zones (around line 30):
```nginx
# Change 100r/m to 200r/m for 200 requests per minute
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=200r/m;
```

### 2. Restart nginx
```bash
docker-compose restart nginx
```

### 3. Verify
```bash
docker-compose exec nginx nginx -t
```

---

## 📈 Monitoring

### Check if users are hitting limits:
```bash
docker-compose logs nginx | grep "limiting requests"
```

### Check blocked requests:
```bash
docker-compose logs nginx | grep "503"
```

### Real-time monitoring:
```bash
docker-compose logs -f nginx
```

---

## 🚨 When to Increase Limits

Increase limits if you see:
1. **Legitimate users getting 503 errors**
2. **High traffic during peak hours**
3. **Mobile apps making frequent requests**
4. **Multiple users behind same IP (office/school)**

**Don't increase if:**
- Single IP making thousands of requests
- Automated bots/scrapers
- Suspicious patterns in logs

---

## 💡 Best Practices

1. **Start conservative** (current limits are good)
2. **Monitor for 1 week** before adjusting
3. **Increase gradually** (double the limit, not 10x)
4. **Keep auth limits strict** (brute force protection)
5. **Use CloudFlare** for additional DDoS protection

---

## 🎯 Production Recommendations

### For Small Traffic (< 1000 users/day)
- Current limits are perfect ✅

### For Medium Traffic (1000-10000 users/day)
- API limit: 200 req/min
- History limit: 60 req/min

### For High Traffic (> 10000 users/day)
- API limit: 500 req/min
- History limit: 120 req/min
- Consider load balancing

---

## 📞 Quick Commands

```bash
# Restart nginx
docker-compose restart nginx

# Check nginx logs
docker-compose logs nginx --tail=100

# Test nginx config
docker-compose exec nginx nginx -t

# Reload nginx (no downtime)
docker-compose exec nginx nginx -s reload

# Check rate limit status
docker-compose logs nginx | grep -E "limiting|denied"
```

---

## ✅ Your Server is Protected Against:

- ✅ DDoS attacks (rate limiting)
- ✅ Brute force attacks (auth rate limiting)
- ✅ API abuse (general rate limiting)
- ✅ Connection exhaustion (connection limits)
- ✅ WebSocket spam (connection limits)
- ✅ Clickjacking (X-Frame-Options)
- ✅ XSS attacks (X-XSS-Protection)
- ✅ MIME sniffing (X-Content-Type-Options)

**Your production server is now enterprise-grade secure!** 🛡️

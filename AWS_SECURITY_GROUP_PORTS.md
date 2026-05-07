# AWS Security Group - Required Ports Configuration

## 🔒 Required Inbound Rules for SmartRisk Project

### ✅ Currently Configured (from your screenshot):
1. ✅ **SSH** - Port 22 (TCP) - For server access
2. ✅ **HTTP** - Port 80 (TCP) - For web traffic
3. ✅ **HTTPS** - Port 443 (TCP) - For secure web traffic
4. ✅ **Custom TCP** - Port 8080 (TCP) - Backend API
5. ✅ **PostgreSQL** - Port 5432 (TCP) - Database

---

## 📋 Complete Port Configuration

### 1. SSH (Server Access)
```
Type: SSH
Protocol: TCP
Port: 22
Source: Your IP / 0.0.0.0/0 (if you need access from anywhere)
Description: SSH access for server management
```

### 2. HTTP (Web Traffic)
```
Type: HTTP
Protocol: TCP
Port: 80
Source: 0.0.0.0/0 (allow from anywhere)
Description: HTTP web traffic (redirects to HTTPS)
```

### 3. HTTPS (Secure Web Traffic)
```
Type: HTTPS
Protocol: TCP
Port: 443
Source: 0.0.0.0/0 (allow from anywhere)
Description: HTTPS secure web traffic
```

### 4. Django Backend API
```
Type: Custom TCP
Protocol: TCP
Port: 8000
Source: 0.0.0.0/0 (or restrict to your frontend IP)
Description: Django backend API
```

### 5. WebSocket (Real-time Trading Signals)
```
Type: Custom TCP
Protocol: TCP
Port: 8001
Source: 0.0.0.0/0 (allow from anywhere for WebSocket connections)
Description: WebSocket for real-time trading signals and updates
```

### 6. PostgreSQL Database (Optional - Only if external access needed)
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: Your IP only (NOT 0.0.0.0/0 for security)
Description: PostgreSQL database (only if you need external access)
```

### 7. Redis (Optional - Only if external access needed)
```
Type: Custom TCP
Protocol: TCP
Port: 6379
Source: Your IP only (NOT 0.0.0.0/0 for security)
Description: Redis cache (only if you need external access)
```

---

## 🎯 Recommended Configuration for Production

### Minimum Required (Public Access):
```
┌─────────────┬──────────┬──────┬─────────────┬──────────────────────────┐
│ Type        │ Protocol │ Port │ Source      │ Description              │
├─────────────┼──────────┼──────┼─────────────┼──────────────────────────┤
│ SSH         │ TCP      │ 22   │ Your IP     │ Server management        │
│ HTTP        │ TCP      │ 80   │ 0.0.0.0/0   │ Web traffic              │
│ HTTPS       │ TCP      │ 443  │ 0.0.0.0/0   │ Secure web traffic       │
│ Custom TCP  │ TCP      │ 8000 │ 0.0.0.0/0   │ Django API               │
│ Custom TCP  │ TCP      │ 8001 │ 0.0.0.0/0   │ WebSocket (Real-time)    │
└─────────────┴──────────┴──────┴─────────────┴──────────────────────────┘
```

### Internal Services (Restrict Access):
```
┌─────────────┬──────────┬──────┬─────────────┬──────────────────────────┐
│ Type        │ Protocol │ Port │ Source      │ Description              │
├─────────────┼──────────┼──────┼─────────────┼──────────────────────────┤
│ PostgreSQL  │ TCP      │ 5432 │ Your IP     │ Database (if needed)     │
│ Redis       │ TCP      │ 6379 │ Your IP     │ Cache (if needed)        │
└─────────────┴──────────┴──────┴─────────────┴──────────────────────────┘
```

---

## ⚠️ What You're Missing (CRITICAL):

### 🔴 Port 8001 - WebSocket (MUST ADD!)
Your project uses WebSocket for real-time trading signals. You MUST add this port:

```
Type: Custom TCP
Protocol: TCP
Port: 8001
Source: 0.0.0.0/0
Description: WebSocket for real-time trading signals
```

**Why it's critical:**
- Real-time signal updates won't work without this
- Trading alerts won't be delivered
- Live price updates won't work
- Users won't receive notifications

---

## 🚀 How to Add Missing Ports in AWS

### Step 1: Add WebSocket Port (8001)

1. Click **"Add rule"** button
2. Select **"Custom TCP"** from Type dropdown
3. Enter **8001** in Port range
4. Select **"Anywhere-IPv4"** (0.0.0.0/0) for Source
5. Add description: **"WebSocket for real-time trading signals"**
6. Click **"Save rules"**

### Step 2: Verify Port 8000 Source

1. Check your Port 8000 rule
2. Make sure Source is **0.0.0.0/0** (not just your IP)
3. This allows frontend to connect to backend API

---

## 🔐 Security Best Practices

### ✅ DO:
- **SSH (22)**: Restrict to your IP only
- **HTTP (80)**: Allow from anywhere (0.0.0.0/0)
- **HTTPS (443)**: Allow from anywhere (0.0.0.0/0)
- **Django API (8000)**: Allow from anywhere (0.0.0.0/0)
- **WebSocket (8001)**: Allow from anywhere (0.0.0.0/0)
- **PostgreSQL (5432)**: Restrict to your IP or remove if not needed
- **Redis (6379)**: Restrict to your IP or remove if not needed

### ❌ DON'T:
- Don't expose PostgreSQL (5432) to 0.0.0.0/0
- Don't expose Redis (6379) to 0.0.0.0/0
- Don't remove SSH access (you'll be locked out!)
- Don't block WebSocket port (8001) - signals won't work

---

## 📊 Port Usage in Your Project

### Port 80 (HTTP):
- Nginx redirects to HTTPS
- Used for: Initial web requests

### Port 443 (HTTPS):
- Nginx serves frontend
- Used for: Secure web traffic, frontend application

### Port 8000 (Django API):
- Django backend API
- Used for: User authentication, trading data, subscriptions

### Port 8001 (WebSocket):
- Django Channels WebSocket
- Used for: Real-time trading signals, live updates, notifications

### Port 5432 (PostgreSQL):
- Database server
- Used for: Data storage (should be internal only)

### Port 6379 (Redis):
- Cache and message broker
- Used for: Session storage, Celery tasks (should be internal only)

---

## 🧪 Testing Ports After Configuration

### Test from your local machine:

```bash
# Test HTTP
curl http://your-ec2-ip

# Test HTTPS
curl https://your-domain.com

# Test Django API
curl http://your-ec2-ip:8000/api/health/

# Test WebSocket (using wscat)
npm install -g wscat
wscat -c ws://your-ec2-ip:8001/ws/signals/

# Test SSH
ssh -i your-key.pem ubuntu@your-ec2-ip
```

---

## 📋 Complete AWS Security Group Configuration

### Copy-Paste Ready Configuration:

```
Inbound Rules:

1. SSH
   Type: SSH
   Protocol: TCP
   Port: 22
   Source: Your IP (e.g., 203.0.113.0/32)
   Description: SSH access

2. HTTP
   Type: HTTP
   Protocol: TCP
   Port: 80
   Source: 0.0.0.0/0
   Description: HTTP web traffic

3. HTTPS
   Type: HTTPS
   Protocol: TCP
   Port: 443
   Source: 0.0.0.0/0
   Description: HTTPS secure web traffic

4. Django API
   Type: Custom TCP
   Protocol: TCP
   Port: 8000
   Source: 0.0.0.0/0
   Description: Django backend API

5. WebSocket (CRITICAL - ADD THIS!)
   Type: Custom TCP
   Protocol: TCP
   Port: 8001
   Source: 0.0.0.0/0
   Description: WebSocket for real-time signals

6. PostgreSQL (Optional - Only if needed)
   Type: PostgreSQL
   Protocol: TCP
   Port: 5432
   Source: Your IP only
   Description: Database access (if needed)
```

---

## 🔄 Outbound Rules

Keep default outbound rules (allow all):
```
Type: All traffic
Protocol: All
Port: All
Destination: 0.0.0.0/0
```

---

## ⚡ Quick Checklist

Before deploying, verify:

- [ ] Port 22 (SSH) - Restricted to your IP
- [ ] Port 80 (HTTP) - Open to 0.0.0.0/0
- [ ] Port 443 (HTTPS) - Open to 0.0.0.0/0
- [ ] Port 8000 (Django API) - Open to 0.0.0.0/0
- [ ] Port 8001 (WebSocket) - Open to 0.0.0.0/0 ⚠️ CRITICAL
- [ ] Port 5432 (PostgreSQL) - Restricted or closed
- [ ] Port 6379 (Redis) - Restricted or closed

---

## 🚨 Common Issues

### Issue 1: "WebSocket connection failed"
**Solution:** Add port 8001 to security group

### Issue 2: "API not accessible"
**Solution:** Ensure port 8000 source is 0.0.0.0/0

### Issue 3: "Can't SSH into server"
**Solution:** Check port 22 is open for your IP

### Issue 4: "Website not loading"
**Solution:** Ensure ports 80 and 443 are open to 0.0.0.0/0

---

## 📞 Summary

### MUST HAVE (5 ports):
1. ✅ SSH (22) - Your IP only
2. ✅ HTTP (80) - 0.0.0.0/0
3. ✅ HTTPS (443) - 0.0.0.0/0
4. ✅ Django API (8000) - 0.0.0.0/0
5. ⚠️ **WebSocket (8001) - 0.0.0.0/0** ← ADD THIS NOW!

### OPTIONAL (2 ports):
6. PostgreSQL (5432) - Your IP only (if external access needed)
7. Redis (6379) - Your IP only (if external access needed)

---

**Last Updated:** May 7, 2026
**Status:** ✅ Production-Ready Configuration
**Critical:** Don't forget to add Port 8001 for WebSocket!

# Manual Server Fix Commands

## 🚨 Your server is not responding. Follow these steps:

---

## Option 1: Run PowerShell Script (Easiest)

Open PowerShell in this directory and run:

```powershell
.\fix_server.ps1
```

This will automatically diagnose and attempt to fix the issue.

---

## Option 2: Manual Commands (Step by Step)

### Step 1: Test if server is reachable

```powershell
Test-Connection -ComputerName 54.183.119.39 -Count 4
```

**Expected**: Should show replies  
**If fails**: Go to AWS Console and check if instance is running

---

### Step 2: Connect via SSH

```powershell
ssh -i "smartriskfx (1).pem" ubuntu@54.183.119.39
```

**If this works**, you'll see a Ubuntu prompt. Then continue with Step 3.

**If this hangs or times out**:
- Wait 2-3 minutes and try again
- OR restart the EC2 instance from AWS Console

---

### Step 3: Check Docker services (once connected)

```bash
cd ~/smartrisk
sudo docker-compose ps
```

**Expected**: Should show list of containers  
**If empty or all "Exited"**: Services are down, continue to Step 4

---

### Step 4: Restart all services

```bash
cd ~/smartrisk
sudo docker-compose down
sudo docker-compose up -d
```

Wait 2 minutes for services to start.

---

### Step 5: Check services again

```bash
sudo docker-compose ps
```

**Expected**: All services should show "Up"

---

### Step 6: Check logs if services won't start

```bash
# Check Django logs
sudo docker-compose logs django --tail=50

# Check all logs
sudo docker-compose logs --tail=50
```

---

### Step 7: Test website

Open browser: **http://54.183.119.39**

Should show your SmartRisk login page ✅

---

## Option 3: Restart EC2 Instance from AWS Console

If SSH is completely unresponsive:

1. Go to: https://us-west-1.console.aws.amazon.com/ec2/home?region=us-west-1#Instances:
2. Select your instance
3. Click **Instance state** → **Reboot instance**
4. Wait 2-3 minutes
5. Try accessing http://54.183.119.39

---

## 🔍 Troubleshooting

### Issue: "Connection timed out"
**Solution**: 
- Instance might be stopped → Start it from AWS Console
- Security group might be blocking → Check port 22, 80, 443 are open

### Issue: "Permission denied (publickey)"
**Solution**: PEM file permissions are wrong. Run:
```powershell
icacls "smartriskfx (1).pem" /inheritance:r
icacls "smartriskfx (1).pem" /grant:r "$($env:USERNAME):R"
```

### Issue: Services won't start
**Solution**: Check logs and rebuild:
```bash
cd ~/smartrisk
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d
```

---

## 📞 Quick Diagnosis

Run this one command to see everything:

```powershell
ssh -i "smartriskfx (1).pem" ubuntu@54.183.119.39 "cd ~/smartrisk && sudo docker-compose ps && echo '---' && sudo docker-compose logs --tail=20"
```

---

## ⚡ Emergency: Full Restart

If nothing works, do a complete restart:

```bash
ssh -i "smartriskfx (1).pem" ubuntu@54.183.119.39

cd ~/smartrisk
sudo docker-compose down -v
sudo docker system prune -f
git pull origin main
sudo docker-compose build
sudo docker-compose up -d
```

**Warning**: This will delete all data and rebuild everything!

---

## 🎯 Most Likely Issue

Based on the symptoms (connection timeout), the most likely causes are:

1. **EC2 instance is overloaded** → Wait 5 minutes and try again
2. **SSH service is hung** → Reboot instance from AWS Console
3. **Docker is consuming all resources** → Reboot instance

**Recommended action**: Reboot the EC2 instance from AWS Console, then try again.

---

## AWS Console Quick Links

- **EC2 Instances**: https://us-west-1.console.aws.amazon.com/ec2/home?region=us-west-1#Instances:
- **Security Groups**: https://us-west-1.console.aws.amazon.com/ec2/home?region=us-west-1#SecurityGroups:

---

**Need help? Run `.\fix_server.ps1` for automatic diagnosis!**

# Quick Troubleshooting Commands

## 🚀 Essential Commands for EC2 Server

### Connect to Server
```bash
ssh ubuntu@54.183.119.39
```

---

## 📊 Check Service Status

### View all services
```bash
cd ~/smartrisk
sudo docker-compose ps
```

### Expected output (all should show "Up"):
```
NAME                         STATUS
neuraltrade_db               Up (healthy)
neuraltrade_redis            Up (healthy)
neuraltrade_django           Up (healthy)
neuraltrade_celery_worker    Up (healthy)
neuraltrade_celery_beat      Up (healthy)
neuraltrade_frontend         Up (healthy)
neuraltrade_nginx            Up
```

---

## 📝 View Logs

### Django logs (backend)
```bash
sudo docker-compose logs django --tail=50
sudo docker-compose logs django -f  # Follow live logs
```

### Celery Worker logs
```bash
sudo docker-compose logs celery_worker --tail=50
sudo docker-compose logs celery_worker -f
```

### Celery Beat logs (scheduled tasks)
```bash
sudo docker-compose logs celery_beat --tail=50
sudo docker-compose logs celery_beat -f
```

### Frontend logs
```bash
sudo docker-compose logs frontend --tail=50
sudo docker-compose logs frontend -f
```

### All services logs
```bash
sudo docker-compose logs --tail=50
sudo docker-compose logs -f  # Follow all logs
```

---

## 🔄 Restart Services

### Restart all services
```bash
cd ~/smartrisk
sudo docker-compose restart
```

### Restart specific service
```bash
sudo docker-compose restart django
sudo docker-compose restart celery_worker
sudo docker-compose restart celery_beat
sudo docker-compose restart frontend
```

### Stop and start (full restart)
```bash
sudo docker-compose down
sudo docker-compose up -d
```

---

## 🔧 Rebuild and Restart

### If you need to rebuild after code changes
```bash
cd ~/smartrisk
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

### Rebuild specific service
```bash
sudo docker-compose build --no-cache django
sudo docker-compose up -d django
```

---

## 🗄️ Database Commands

### Run migrations
```bash
sudo docker-compose exec django python manage.py migrate
```

### Create superuser manually
```bash
sudo docker-compose exec django python manage.py createsuperuser
```

### Access Django shell
```bash
sudo docker-compose exec django python manage.py shell
```

### Access PostgreSQL directly
```bash
sudo docker-compose exec db psql -U smartrisk_user -d smartrisk_db
```

---

## 🧹 Cleanup Commands

### Remove stopped containers
```bash
sudo docker-compose down
```

### Remove containers and volumes (⚠️ DELETES DATA)
```bash
sudo docker-compose down -v
```

### Clean up Docker system
```bash
sudo docker system prune -a
```

---

## 🔍 Health Checks

### Check Django health endpoint
```bash
curl http://localhost:8000/health/
```

### Check Redis
```bash
sudo docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Check PostgreSQL
```bash
sudo docker-compose exec db pg_isready -U smartrisk_user
# Should return: accepting connections
```

### Check disk space
```bash
df -h
```

### Check memory usage
```bash
free -h
```

### Check running processes
```bash
top
# Press 'q' to quit
```

---

## 📦 Docker Information

### List all containers
```bash
sudo docker ps -a
```

### List all images
```bash
sudo docker images
```

### Check Docker version
```bash
docker --version
docker-compose --version
```

### View container resource usage
```bash
sudo docker stats
# Press Ctrl+C to exit
```

---

## 🔐 Environment Variables

### View current .env file
```bash
cd ~/smartrisk
cat .env
```

### Edit .env file
```bash
nano .env
# Press Ctrl+X, then Y, then Enter to save
```

---

## 🌐 Network Checks

### Check if ports are open
```bash
sudo netstat -tulpn | grep LISTEN
```

### Test Django from server
```bash
curl http://localhost:8000/health/
```

### Test frontend from server
```bash
curl http://localhost:3000/api/health
```

---

## 🚨 Emergency Commands

### Stop everything immediately
```bash
cd ~/smartrisk
sudo docker-compose down
```

### Kill all Docker containers
```bash
sudo docker kill $(sudo docker ps -q)
```

### View system logs
```bash
sudo journalctl -xe
```

### Check Docker daemon status
```bash
sudo systemctl status docker
```

### Restart Docker daemon
```bash
sudo systemctl restart docker
```

---

## 📋 Useful One-Liners

### Check if Django is responding
```bash
curl -I http://localhost:8000/health/
```

### Count running containers
```bash
sudo docker ps | wc -l
```

### Show container IPs
```bash
sudo docker inspect -f '{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(sudo docker ps -q)
```

### Follow Django logs with grep filter
```bash
sudo docker-compose logs -f django | grep ERROR
```

---

## 🎯 Quick Diagnosis

### Run this to get full status
```bash
cd ~/smartrisk
echo "=== Services Status ==="
sudo docker-compose ps
echo ""
echo "=== Django Health ==="
curl -s http://localhost:8000/health/ || echo "Django not responding"
echo ""
echo "=== Redis Health ==="
sudo docker-compose exec redis redis-cli ping
echo ""
echo "=== PostgreSQL Health ==="
sudo docker-compose exec db pg_isready -U smartrisk_user
echo ""
echo "=== Disk Space ==="
df -h | grep -E "Filesystem|/$"
echo ""
echo "=== Memory ==="
free -h
```

---

## 📞 When to Use These Commands

| Situation | Command |
|-----------|---------|
| Check if services are running | `sudo docker-compose ps` |
| See error messages | `sudo docker-compose logs [service] --tail=50` |
| Service not responding | `sudo docker-compose restart [service]` |
| After code changes | `sudo docker-compose down && sudo docker-compose up -d` |
| Database issues | `sudo docker-compose exec django python manage.py migrate` |
| Out of memory | `free -h` and `sudo docker stats` |
| Port conflicts | `sudo netstat -tulpn \| grep LISTEN` |

---

**💡 Pro Tip**: Save this file for quick reference during troubleshooting!

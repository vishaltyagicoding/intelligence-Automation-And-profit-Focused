# Deployment Reference

## Server
- **IP**: 54.183.178.141
- **SSH**: `ssh -i smartriskfx1.pem ubuntu@54.183.178.141`
- **Dir**: `~/smartrisk`
- **Region**: AWS EC2 us-west-1 (California)

## CI/CD (Normal Deploy)
Push to `main` branch → GitHub Actions automatically:
1. SSH into server
2. `git pull origin main`
3. `docker-compose down && docker-compose up -d --build`
4. `python manage.py migrate`
5. `python manage.py collectstatic --noinput`

**Important**: Only 5 CI/CD deployments per week. Manual deploy if quota exceeded.

## Manual Deploy
```bash
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
git pull origin main
sudo docker-compose down
sudo docker-compose up -d --build
sudo docker-compose exec django python manage.py migrate
sudo docker-compose logs -f django
```

## Post-Deploy Checklist
- [ ] All containers running: `sudo docker-compose ps`
- [ ] No errors in logs: `sudo docker-compose logs --tail=50 django`
- [ ] Frontend accessible: `curl -I https://smartriskfx.com`
- [ ] Backend API: `curl https://smartriskfx.com/api/health/`

## When to Run backfill_signals.py
Run this AFTER any deployment that changes SL/Target calculation logic:
```bash
sudo docker-compose exec django python backfill_signals.py
```
This recalculates stop_loss and target for ALL historical signals in DB.
Required to keep history page and live chart values identical.

## Docker Container Names
| Service | Container Name | Note |
|---|---|---|
| Django backend | `django` | NOT "backend" |
| Frontend | `frontend` | |
| Database | `db` | |
| Redis | `redis` | |
| Nginx | `nginx` | |

## Environment Files
- Backend: `.env` (NOT `.env.production`)
- Frontend: `.env.local`
- Compose: `docker-compose.yml` (NOT `docker-compose.prod.yml`)

## Common Commands
```bash
# View logs
sudo docker-compose logs -f django
sudo docker-compose logs -f frontend

# Restart service
sudo docker-compose restart django

# Django shell
sudo docker-compose exec django python manage.py shell

# Run migrations
sudo docker-compose exec django python manage.py migrate

# Database backup
sudo docker-compose exec db pg_dump -U smartrisk_user neuraltrade > backup_$(date +%Y%m%d).sql
```

## SSL
- Let's Encrypt auto-renewal enabled
- Certificate path: `/etc/letsencrypt/live/smartriskfx.com/`
- Manual renew: `sudo certbot renew && sudo docker-compose restart nginx`
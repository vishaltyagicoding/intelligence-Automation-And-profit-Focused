# PostgreSQL Configuration

## Overview
PostgreSQL 16 is used as the primary database for SmartRisk, storing users, signals, trades, and all application data.

## Docker Configuration

### Service Definition
```yaml
db:
  image: postgres:16
  container_name: db
  volumes:
    - postgres_data:/var/lib/postgresql/data
  environment:
    - POSTGRES_DB=${DB_NAME}
    - POSTGRES_USER=${DB_USER}
    - POSTGRES_PASSWORD=${DB_PASSWORD}
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
    interval: 10s
    timeout: 5s
    retries: 5
```

## Database Details

### Connection Information
- **Host**: `db` (Docker internal) or `localhost` (external)
- **Port**: 5432
- **Database**: neuraltrade
- **User**: smartrisk_user
- **Password**: Set in .env file

### Connection String
```
postgresql://smartrisk_user:password@db:5432/neuraltrade
```

## Database Schema

### Core Tables
1. **auth_user** - Django user authentication
2. **users_userprofile** - Extended user data
3. **reversal_zones** - Calculated reversal zones
4. **signal_alerts** - User alert preferences
5. **trading_trade** - User trade history
6. **trading_marketsignal** - Generated signals
7. **reversal_status** - Current signal tracking

### Indexes
- Primary keys on all tables
- Foreign key indexes
- Composite indexes on (symbol, timeframe, reversal_time)
- Index on (symbol, is_bullish)

## Common Operations

### Connect to Database
```bash
# Via Docker
sudo docker-compose exec db psql -U smartrisk_user neuraltrade

# Direct connection
psql -h localhost -U smartrisk_user -d neuraltrade
```

### List Databases
```sql
\l
```

### List Tables
```sql
\dt
```

### Describe Table
```sql
\d reversal_zones
```

### View Table Data
```sql
SELECT * FROM reversal_zones LIMIT 10;
```

### Check Database Size
```sql
SELECT pg_size_pretty(pg_database_size('neuraltrade'));
```

### Check Table Sizes
```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Active Connections
```sql
SELECT count(*) FROM pg_stat_activity;
```

### Kill Connection
```sql
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'neuraltrade' AND pid <> pg_backend_pid();
```

## Backup and Restore

### Create Backup
```bash
# Full database backup
sudo docker-compose exec db pg_dump -U smartrisk_user neuraltrade > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
sudo docker-compose exec db pg_dump -U smartrisk_user neuraltrade | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Specific table backup
sudo docker-compose exec db pg_dump -U smartrisk_user -t reversal_zones neuraltrade > reversal_zones_backup.sql
```

### Restore from Backup
```bash
# Restore full database
sudo docker-compose exec -T db psql -U smartrisk_user neuraltrade < backup.sql

# Restore compressed backup
gunzip -c backup.sql.gz | sudo docker-compose exec -T db psql -U smartrisk_user neuraltrade

# Restore specific table
sudo docker-compose exec -T db psql -U smartrisk_user neuraltrade < reversal_zones_backup.sql
```

### Automated Backup Script
```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/neuraltrade_$DATE.sql.gz"

# Create backup
sudo docker-compose exec -T db pg_dump -U smartrisk_user neuraltrade | gzip > $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "neuraltrade_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

## Migrations

### Run Migrations
```bash
sudo docker-compose exec django python manage.py migrate
```

### Create Migration
```bash
sudo docker-compose exec django python manage.py makemigrations
```

### View Migration Status
```bash
sudo docker-compose exec django python manage.py showmigrations
```

### Rollback Migration
```bash
sudo docker-compose exec django python manage.py migrate app_name 0001_initial
```

### Fake Migration
```bash
sudo docker-compose exec django python manage.py migrate --fake app_name 0001
```

## Performance Tuning

### Check Slow Queries
```sql
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Analyze Table
```sql
ANALYZE reversal_zones;
```

### Vacuum Table
```sql
VACUUM ANALYZE reversal_zones;
```

### Reindex Table
```sql
REINDEX TABLE reversal_zones;
```

## Monitoring

### Check Health
```bash
sudo docker-compose exec db pg_isready -U smartrisk_user -d neuraltrade
```

### View Logs
```bash
sudo docker-compose logs -f db
```

### Database Statistics
```sql
SELECT 
  datname,
  numbackends,
  xact_commit,
  xact_rollback,
  blks_read,
  blks_hit,
  tup_returned,
  tup_fetched,
  tup_inserted,
  tup_updated,
  tup_deleted
FROM pg_stat_database
WHERE datname = 'neuraltrade';
```

## Troubleshooting

### Connection Refused
**Cause**: Database not running
**Solution**:
```bash
sudo docker-compose ps db
sudo docker-compose restart db
```

### Too Many Connections
**Cause**: Connection pool exhausted
**Solution**:
```sql
-- View connections
SELECT * FROM pg_stat_activity;

-- Kill idle connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '5 minutes';
```

### Disk Space Full
**Cause**: Database or logs too large
**Solution**:
```bash
# Check disk usage
df -h

# Vacuum database
sudo docker-compose exec db psql -U smartrisk_user neuraltrade -c "VACUUM FULL;"

# Clean old data
sudo docker-compose exec django python manage.py shell
>>> from reversal_zones.models import ReversalZone
>>> from django.utils import timezone
>>> import datetime
>>> cutoff = timezone.now() - datetime.timedelta(days=150)
>>> ReversalZone.objects.filter(reversal_time__lt=cutoff).delete()
```

### Slow Queries
**Cause**: Missing indexes or inefficient queries
**Solution**:
```sql
-- Enable query logging
ALTER DATABASE neuraltrade SET log_min_duration_statement = 1000;

-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY abs(correlation) DESC;
```

## Security

### Change Password
```sql
ALTER USER smartrisk_user WITH PASSWORD 'new_password';
```

### Grant Permissions
```sql
GRANT ALL PRIVILEGES ON DATABASE neuraltrade TO smartrisk_user;
```

### Revoke Permissions
```sql
REVOKE ALL PRIVILEGES ON DATABASE neuraltrade FROM username;
```

## Data Retention

### Clean Old Signals (Keep 5 Months)
```python
from reversal_zones.models import ReversalZone
from django.utils import timezone
import datetime

cutoff = timezone.now() - datetime.timedelta(days=150)
deleted = ReversalZone.objects.filter(reversal_time__lt=cutoff).delete()
print(f"Deleted {deleted[0]} old signals")
```

### Archive Old Data
```bash
# Export old data
sudo docker-compose exec db pg_dump -U smartrisk_user \
  -t reversal_zones \
  --where="reversal_time < '2025-01-01'" \
  neuraltrade > archive_2024.sql

# Delete archived data
sudo docker-compose exec django python manage.py shell
>>> from reversal_zones.models import ReversalZone
>>> ReversalZone.objects.filter(reversal_time__lt='2025-01-01').delete()
```

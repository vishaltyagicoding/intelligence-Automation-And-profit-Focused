"""
Database Connection Pool Monitor
Tracks PostgreSQL connections and sends alerts before issues occur.

Run this script via cron every 5 minutes:
*/5 * * * * cd /app && python monitoring/db_connection_monitor.py
"""

import os
import sys
import django
import logging
from datetime import datetime

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django.db import connection
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

# Thresholds
MAX_CONNECTIONS = 200
WARNING_THRESHOLD = 150  # 75% of max
CRITICAL_THRESHOLD = 180  # 90% of max

def get_connection_stats():
    """Get current database connection statistics."""
    with connection.cursor() as cursor:
        # Total connections
        cursor.execute("SELECT count(*) FROM pg_stat_activity;")
        total = cursor.fetchone()[0]
        
        # Active connections (running queries)
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
        active = cursor.fetchone()[0]
        
        # Idle connections
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';")
        idle = cursor.fetchone()[0]
        
        # Idle in transaction (potential connection leaks)
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction';")
        idle_in_transaction = cursor.fetchone()[0]
        
        # Long-running queries (> 5 minutes)
        cursor.execute("""
            SELECT count(*) 
            FROM pg_stat_activity 
            WHERE state = 'active' 
            AND now() - query_start > interval '5 minutes';
        """)
        long_running = cursor.fetchone()[0]
        
        # Connections by application
        cursor.execute("""
            SELECT application_name, count(*) 
            FROM pg_stat_activity 
            GROUP BY application_name 
            ORDER BY count(*) DESC;
        """)
        by_app = cursor.fetchall()
        
        return {
            'total': total,
            'active': active,
            'idle': idle,
            'idle_in_transaction': idle_in_transaction,
            'long_running': long_running,
            'by_app': by_app,
            'timestamp': datetime.now(),
        }

def send_alert(subject, message):
    """Send email alert to admins."""
    try:
        send_mail(
            subject=f"[SmartRisk Alert] {subject}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['alberttyagi123@gmail.com', 'smarttriskfx@gmail.com'],
            fail_silently=False,
        )
        logger.info(f"✅ Alert sent: {subject}")
    except Exception as e:
        logger.error(f"❌ Failed to send alert: {e}")

def check_and_alert(stats):
    """Check thresholds and send alerts if needed."""
    total = stats['total']
    
    # Critical: > 90% capacity
    if total >= CRITICAL_THRESHOLD:
        message = f"""
🚨 CRITICAL: Database Connection Pool Near Exhaustion

Current Status:
- Total Connections: {total} / {MAX_CONNECTIONS} ({total/MAX_CONNECTIONS*100:.1f}%)
- Active (running queries): {stats['active']}
- Idle: {stats['idle']}
- Idle in transaction (leak suspect): {stats['idle_in_transaction']}
- Long-running queries (>5min): {stats['long_running']}

Connections by Application:
{format_connections_by_app(stats['by_app'])}

Action Required:
1. Check if any long-running queries can be killed
2. Review recent code changes for connection leaks
3. Consider increasing max_connections to 300
4. Check Celery task concurrency settings

Timestamp: {stats['timestamp']}
        """
        send_alert("CRITICAL: DB Connection Pool at 90%", message)
        return 'critical'
    
    # Warning: > 75% capacity
    elif total >= WARNING_THRESHOLD:
        message = f"""
⚠️ WARNING: Database Connection Pool at 75%

Current Status:
- Total Connections: {total} / {MAX_CONNECTIONS} ({total/MAX_CONNECTIONS*100:.1f}%)
- Active: {stats['active']}
- Idle: {stats['idle']}
- Idle in transaction: {stats['idle_in_transaction']}

Monitor closely. If this persists, consider scaling database.

Timestamp: {stats['timestamp']}
        """
        send_alert("WARNING: DB Connection Pool at 75%", message)
        return 'warning'
    
    # Info: Check for connection leaks
    elif stats['idle_in_transaction'] > 10:
        message = f"""
ℹ️ INFO: Potential Connection Leak Detected

Found {stats['idle_in_transaction']} connections idle in transaction.
This suggests queries that started transactions but didn't commit/rollback.

Current Status:
- Total Connections: {total} / {MAX_CONNECTIONS}
- Idle in transaction: {stats['idle_in_transaction']}

Review recent code for missing transaction handling.

Timestamp: {stats['timestamp']}
        """
        send_alert("INFO: Potential Connection Leak", message)
        return 'info'
    
    return 'ok'

def format_connections_by_app(by_app):
    """Format connection breakdown by application."""
    lines = []
    for app_name, count in by_app[:10]:  # Top 10
        app = app_name or '(unknown)'
        lines.append(f"  - {app}: {count} connections")
    return '\n'.join(lines)

def log_stats(stats):
    """Log statistics to file for trending."""
    log_file = '/app/logs/db_connections.log'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"{stats['timestamp'].isoformat()},"
                f"{stats['total']},"
                f"{stats['active']},"
                f"{stats['idle']},"
                f"{stats['idle_in_transaction']},"
                f"{stats['long_running']}\n")

def main():
    """Main monitoring function."""
    try:
        stats = get_connection_stats()
        status = check_and_alert(stats)
        log_stats(stats)
        
        # Print to stdout for cron logging
        print(f"[{stats['timestamp']}] DB Connections: {stats['total']}/{MAX_CONNECTIONS} "
              f"(Active: {stats['active']}, Idle: {stats['idle']}) - Status: {status.upper()}")
        
        return 0 if status in ['ok', 'info'] else 1
        
    except Exception as e:
        logger.error(f"❌ Monitoring failed: {e}", exc_info=True)
        print(f"ERROR: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

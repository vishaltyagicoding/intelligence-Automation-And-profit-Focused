"""
Django management command to check database connection health.

Usage:
    python manage.py check_db_health
    python manage.py check_db_health --kill-idle  # Kill idle connections > 10 min
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
import sys

class Command(BaseCommand):
    help = 'Check database connection pool health'

    def add_arguments(self, parser):
        parser.add_argument(
            '--kill-idle',
            action='store_true',
            help='Kill idle connections older than 10 minutes',
        )
        parser.add_argument(
            '--kill-long-running',
            action='store_true',
            help='Kill queries running longer than 30 minutes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Database Connection Health Check'))
        self.stdout.write('=' * 60)
        
        with connection.cursor() as cursor:
            # 1. Check max_connections setting
            cursor.execute("SHOW max_connections;")
            max_conn = int(cursor.fetchone()[0])
            self.stdout.write(f"\n📊 Max Connections: {max_conn}")
            
            # 2. Current connection count
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            total = cursor.fetchone()[0]
            percentage = (total / max_conn) * 100
            
            status_color = self.style.SUCCESS
            if percentage > 90:
                status_color = self.style.ERROR
            elif percentage > 75:
                status_color = self.style.WARNING
            
            self.stdout.write(status_color(
                f"📈 Current Connections: {total} / {max_conn} ({percentage:.1f}%)"
            ))
            
            # 3. Breakdown by state
            cursor.execute("""
                SELECT state, count(*) 
                FROM pg_stat_activity 
                WHERE state IS NOT NULL
                GROUP BY state 
                ORDER BY count(*) DESC;
            """)
            self.stdout.write(f"\n📋 Connection States:")
            for state, count in cursor.fetchall():
                self.stdout.write(f"  • {state}: {count}")
            
            # 4. Connections by application
            cursor.execute("""
                SELECT 
                    COALESCE(application_name, '(unknown)') as app,
                    count(*) as conn_count
                FROM pg_stat_activity
                GROUP BY application_name
                ORDER BY conn_count DESC
                LIMIT 10;
            """)
            self.stdout.write(f"\n📱 Top Applications:")
            for app, count in cursor.fetchall():
                self.stdout.write(f"  • {app}: {count}")
            
            # 5. Long-running queries
            cursor.execute("""
                SELECT 
                    pid,
                    now() - query_start as duration,
                    state,
                    LEFT(query, 100) as query_preview
                FROM pg_stat_activity
                WHERE state = 'active'
                AND now() - query_start > interval '5 minutes'
                ORDER BY query_start;
            """)
            long_running = cursor.fetchall()
            if long_running:
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️  Long-Running Queries ({len(long_running)}):"
                ))
                for pid, duration, state, query in long_running:
                    self.stdout.write(f"  • PID {pid}: {duration} - {query}...")
            else:
                self.stdout.write(self.style.SUCCESS(
                    "\n✅ No long-running queries"
                ))
            
            # 6. Idle in transaction (potential leaks)
            cursor.execute("""
                SELECT 
                    pid,
                    now() - state_change as idle_duration,
                    LEFT(query, 80) as last_query
                FROM pg_stat_activity
                WHERE state = 'idle in transaction'
                ORDER BY state_change;
            """)
            idle_in_trans = cursor.fetchall()
            if idle_in_trans:
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️  Idle in Transaction ({len(idle_in_trans)}) - Possible Connection Leaks:"
                ))
                for pid, duration, query in idle_in_trans:
                    self.stdout.write(f"  • PID {pid}: {duration} - {query}...")
            else:
                self.stdout.write(self.style.SUCCESS(
                    "\n✅ No idle-in-transaction connections"
                ))
            
            # 7. Kill idle connections if requested
            if options['kill_idle']:
                self.stdout.write(self.style.WARNING(
                    "\n🔪 Killing idle connections > 10 minutes..."
                ))
                cursor.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE state = 'idle'
                    AND now() - state_change > interval '10 minutes'
                    AND pid != pg_backend_pid();
                """)
                killed = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Killed {killed} idle connections"
                ))
            
            # 8. Kill long-running queries if requested
            if options['kill_long_running']:
                self.stdout.write(self.style.WARNING(
                    "\n🔪 Killing queries running > 30 minutes..."
                ))
                cursor.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    AND now() - query_start > interval '30 minutes'
                    AND pid != pg_backend_pid();
                """)
                killed = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Killed {killed} long-running queries"
                ))
            
            # 9. Overall health status
            self.stdout.write('\n' + '=' * 60)
            if percentage > 90:
                self.stdout.write(self.style.ERROR(
                    '🚨 STATUS: CRITICAL - Connection pool near exhaustion!'
                ))
                self.stdout.write(self.style.ERROR(
                    '   Action: Increase max_connections or kill idle connections'
                ))
                sys.exit(1)
            elif percentage > 75:
                self.stdout.write(self.style.WARNING(
                    '⚠️  STATUS: WARNING - Connection pool at 75%'
                ))
                self.stdout.write(self.style.WARNING(
                    '   Action: Monitor closely, consider scaling'
                ))
                sys.exit(1)
            elif len(idle_in_trans) > 10:
                self.stdout.write(self.style.WARNING(
                    '⚠️  STATUS: WARNING - Potential connection leaks detected'
                ))
                sys.exit(1)
            else:
                self.stdout.write(self.style.SUCCESS(
                    '✅ STATUS: HEALTHY - Connection pool is healthy'
                ))
                sys.exit(0)

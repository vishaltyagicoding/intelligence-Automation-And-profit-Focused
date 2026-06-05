"""
Management command: update_signal_statuses

Runs check_signal_statuses() directly (bypasses Celery) to immediately
update all OPEN signal statuses in the database.

Usage on server:
    sudo docker-compose exec django python manage.py update_signal_statuses

Use this any time you want to force an immediate status update without
waiting for the Celery beat 2-minute schedule.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check all OPEN signals and update status to TARGET_HIT or SL_HIT'

    def handle(self, *args, **options):
        self.stdout.write('Running check_signal_statuses...')
        from reversal_zones.tasks import check_signal_statuses
        result = check_signal_statuses()
        checked = result.get('checked', 0)
        updated = result.get('updated', 0)
        status  = result.get('status', 'unknown')
        if status == 'ok':
            self.stdout.write(
                self.style.SUCCESS(
                    f'Done: {checked} signals checked, {updated} updated.'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'Error: {result.get("error", "unknown error")}'
                )
            )
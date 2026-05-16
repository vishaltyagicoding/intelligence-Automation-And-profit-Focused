"""
Django management command to delete all 1m, 3m, and 10m timeframe records from database.

These timeframes are not implemented in the frontend and are being removed from the backend.

Usage:
    docker-compose exec django python manage.py delete_unused_timeframes
    docker-compose exec django python manage.py delete_unused_timeframes --dry-run
"""

from django.core.management.base import BaseCommand
from reversal_zones.models import ReversalZone


class Command(BaseCommand):
    help = 'Delete all 1m, 3m, and 10m timeframe records from database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*80}\n'
            f'DELETING 1m, 3m, AND 10m TIMEFRAME RECORDS\n'
            f'{"="*80}\n'
            f'Dry Run: {dry_run}\n'
            f'{"="*80}\n'
        ))

        # Count records to be deleted
        records_1m = ReversalZone.objects.filter(timeframe='1m')
        records_3m = ReversalZone.objects.filter(timeframe='3m')
        records_10m = ReversalZone.objects.filter(timeframe='10m')
        
        count_1m = records_1m.count()
        count_3m = records_3m.count()
        count_10m = records_10m.count()
        total = count_1m + count_3m + count_10m

        self.stdout.write(f'Found {count_1m} records with 1m timeframe')
        self.stdout.write(f'Found {count_3m} records with 3m timeframe')
        self.stdout.write(f'Found {count_10m} records with 10m timeframe')
        self.stdout.write(f'Total records to delete: {total}\n')

        if total == 0:
            self.stdout.write(self.style.WARNING('No records found. Exiting.'))
            return

        if not dry_run:
            # Delete the records
            deleted_1m, _ = records_1m.delete()
            deleted_3m, _ = records_3m.delete()
            deleted_10m, _ = records_10m.delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n{"="*80}\n'
                f'DELETION COMPLETE\n'
                f'{"="*80}\n'
                f'Deleted 1m records:  {deleted_1m}\n'
                f'Deleted 3m records:  {deleted_3m}\n'
                f'Deleted 10m records: {deleted_10m}\n'
                f'Total deleted:       {deleted_1m + deleted_3m + deleted_10m}\n'
                f'{"="*80}\n'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️  DRY RUN MODE - No changes were made to database\n'
                f'Run without --dry-run to delete {total} records\n'
            ))

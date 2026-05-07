"""
Django management command to monitor kill switch.
"""

import time
import logging
from django.core.management.base import BaseCommand
from security.kill_switch import kill_switch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor system health and activate kill switch if needed'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Kill switch monitor started'))
        
        while True:
            try:
                # Check if kill switch should be triggered
                should_trigger, reason = kill_switch.should_trigger()
                
                if should_trigger and not kill_switch.is_active:
                    self.stdout.write(
                        self.style.ERROR(f'Triggering kill switch: {reason}')
                    )
                    kill_switch.activate(reason)
                
                elif not should_trigger and kill_switch.is_active:
                    self.stdout.write(
                        self.style.SUCCESS('System recovered, deactivating kill switch')
                    )
                    kill_switch.deactivate()
                
                # Sleep for 5 seconds
                time.sleep(5)
                
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('Kill switch monitor stopped'))
                break
            except Exception as e:
                logger.error(f'Error in kill switch monitor: {e}')
                time.sleep(5)

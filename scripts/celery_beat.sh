#!/bin/bash

# Start Celery beat scheduler
celery -A neuraltrade beat \
    -l info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

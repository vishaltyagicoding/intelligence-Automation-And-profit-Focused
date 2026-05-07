#!/bin/bash

# Start Celery worker with eventlet for async support
celery -A neuraltrade worker \
    -l info \
    --concurrency=4 \
    -P eventlet \
    --max-tasks-per-child=1000 \
    --time-limit=300

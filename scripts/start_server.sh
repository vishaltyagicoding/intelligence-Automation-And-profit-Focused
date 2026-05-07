#!/bin/bash

# Wait for database
echo "Waiting for database..."
sleep 10
echo "Database should be ready"

# Wait for Redis
echo "Waiting for Redis..."
sleep 2
echo "Redis should be ready"

# Create migrations for all apps (in case new models added)
echo "Creating migrations..."
python manage.py makemigrations --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if not exists
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@neuraltrade.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
END

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Initialize reversal zones (async - don't wait)
echo "Initializing reversal zones..."
python manage.py init_reversal_zones &

# Start server with Daphne for WebSocket support
echo "Starting server with Daphne..."
exec daphne -b 0.0.0.0 -p 8000 neuraltrade.asgi:application

#!/bin/bash
# Reset authentication migrations for custom User model

echo "🔄 Resetting authentication migrations..."

# Delete all migration files except __init__.py
find users/migrations -name "*.py" ! -name "__init__.py" -delete
find payments/migrations -name "*.py" ! -name "__init__.py" -delete
find security/migrations -name "*.py" ! -name "__init__.py" -delete
find trading/migrations -name "*.py" ! -name "__init__.py" -delete

# Delete __pycache__
find users/migrations -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find payments/migrations -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find security/migrations -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find trading/migrations -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Migration files deleted"

# Drop and recreate database
echo "🗄️  Resetting database..."
docker exec neuraltrade_db psql -U postgres -c "DROP DATABASE IF EXISTS neuraltrade;"
docker exec neuraltrade_db psql -U postgres -c "CREATE DATABASE neuraltrade;"

echo "✅ Database reset complete"

# Create fresh migrations
echo "📝 Creating fresh migrations..."
docker exec neuraltrade_django python manage.py makemigrations users
docker exec neuraltrade_django python manage.py makemigrations payments
docker exec neuraltrade_django python manage.py makemigrations security
docker exec neuraltrade_django python manage.py makemigrations trading
docker exec neuraltrade_django python manage.py makemigrations

# Run migrations
echo "🚀 Running migrations..."
docker exec neuraltrade_django python manage.py migrate

echo "✅ Authentication system setup complete!"

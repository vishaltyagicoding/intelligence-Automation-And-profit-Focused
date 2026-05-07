#!/bin/bash

echo "🚀 Setting up Email Verification & Password Reset Features"
echo "=========================================================="
echo ""

# Step 1: Create migrations
echo "📝 Step 1: Creating database migrations..."
docker-compose exec -T django python manage.py makemigrations users
if [ $? -eq 0 ]; then
    echo "✅ Migrations created successfully"
else
    echo "❌ Failed to create migrations"
    exit 1
fi
echo ""

# Step 2: Apply migrations
echo "📝 Step 2: Applying migrations..."
docker-compose exec -T django python manage.py migrate
if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully"
else
    echo "❌ Failed to apply migrations"
    exit 1
fi
echo ""

# Step 3: Rebuild backend
echo "🔨 Step 3: Rebuilding backend container..."
docker-compose stop django celery_worker celery_beat
docker-compose build django
if [ $? -eq 0 ]; then
    echo "✅ Backend rebuilt successfully"
else
    echo "❌ Failed to rebuild backend"
    exit 1
fi
echo ""

# Step 4: Start backend
echo "▶️  Step 4: Starting backend services..."
docker-compose up -d django celery_worker celery_beat
if [ $? -eq 0 ]; then
    echo "✅ Backend services started"
else
    echo "❌ Failed to start backend services"
    exit 1
fi
echo ""

# Step 5: Rebuild frontend
echo "🔨 Step 5: Rebuilding frontend container..."
docker-compose stop frontend
docker-compose build frontend
if [ $? -eq 0 ]; then
    echo "✅ Frontend rebuilt successfully"
else
    echo "❌ Failed to rebuild frontend"
    exit 1
fi
echo ""

# Step 6: Start frontend
echo "▶️  Step 6: Starting frontend service..."
docker-compose up -d frontend
if [ $? -eq 0 ]; then
    echo "✅ Frontend service started"
else
    echo "❌ Failed to start frontend service"
    exit 1
fi
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10
echo ""

# Check service status
echo "📊 Checking service status..."
docker-compose ps
echo ""

echo "=========================================================="
echo "✅ Setup Complete!"
echo "=========================================================="
echo ""
echo "🎯 Next Steps:"
echo "1. Clear your browser cache (Ctrl + Shift + R)"
echo "2. Go to http://localhost/register"
echo "3. Test email verification"
echo "4. Test forgot password from login page"
echo ""
echo "📧 Email Configuration:"
echo "   Email: alberttyagi123@gmail.com"
echo "   Check your inbox for OTP codes"
echo ""
echo "📚 For more details, see SETUP_INSTRUCTIONS.md"
echo ""

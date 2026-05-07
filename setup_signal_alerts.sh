#!/bin/bash

echo "🔔 Setting up Signal Alerts System"
echo "=================================="
echo ""

# Run migrations
echo "📦 Running database migrations..."
docker-compose exec django python manage.py makemigrations signal_alerts
docker-compose exec django python manage.py migrate signal_alerts
echo "✅ Migrations completed"
echo ""

# Test the system
echo "🧪 Testing signal alert system..."
docker-compose exec django python manage.py test_signal_alerts
echo ""

echo "✅ Setup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Visit http://localhost/signal-alerts to create an alert"
echo "2. Make sure you have a paid subscription (not trial)"
echo "3. When a new signal is generated, you'll receive an email"
echo ""
echo "🔍 To test with a specific email:"
echo "docker-compose exec django python manage.py test_signal_alerts --email=your@email.com --username=YourName"

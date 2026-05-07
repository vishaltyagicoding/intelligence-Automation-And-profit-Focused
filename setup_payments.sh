#!/bin/bash

echo "🚀 Setting up NeuralTrade Payment System..."

# 1. Install Razorpay SDK
echo "📦 Installing Razorpay SDK..."
docker exec neuraltrade_django pip install razorpay==1.4.1

# 2. Add to requirements.txt if not exists
if ! grep -q "razorpay" requirements.txt; then
    echo "razorpay==1.4.1" >> requirements.txt
    echo "✅ Added razorpay to requirements.txt"
fi

# 3. Create migrations
echo "🗄️ Creating database migrations..."
docker exec neuraltrade_django python manage.py makemigrations payments

# 4. Run migrations
echo "🗄️ Running migrations..."
docker exec neuraltrade_django python manage.py migrate payments

# 5. Restart Django
echo "🔄 Restarting Django..."
docker restart neuraltrade_django

echo ""
echo "✅ Payment system setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Add Razorpay keys to .env file"
echo "2. Update neuraltrade/settings.py (see PAYMENT_SYSTEM_SETUP.md)"
echo "3. Update neuraltrade/urls.py to include payments URLs"
echo "4. Add middleware to settings.py"
echo "5. Test payment flow"
echo ""
echo "📖 Full documentation: PAYMENT_SYSTEM_SETUP.md"

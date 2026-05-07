#!/bin/bash

# Start AI Signal Generation for BTCUSD
# This script starts the continuous signal generation in the background

echo "🤖 Starting AI Signal Generation for BTCUSD..."
echo "================================================"

# Start signal generation using Django management command
docker-compose -f docker-compose.prod.yml exec -d backend python manage.py start_signals --interval 60

echo "✅ AI Signal Generation started!"
echo ""
echo "Signals will be generated every 60 seconds"
echo "View signals at: http://localhost"
echo "View signal history at: http://localhost/history"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f backend | grep 'AI Signal'"
echo ""
echo "To stop signal generation:"
echo "  docker-compose -f docker-compose.prod.yml restart backend"

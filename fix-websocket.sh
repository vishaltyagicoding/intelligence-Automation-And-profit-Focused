#!/bin/bash
# WebSocket Fix - Rebuild and Restart Script

echo "========================================"
echo "WebSocket Connection Fix"
echo "========================================"
echo ""

# Step 1: Check if .env has Binance credentials
echo "[1/5] Checking Binance API credentials..."
if grep -q "BINANCE_API_KEY=your-binance-api-key" .env || grep -q "BINANCE_API_SECRET=your-binance-api-secret" .env; then
    echo "WARNING: Binance API credentials are not set!"
    echo "Please update .env file with your real Binance API credentials."
    echo "See WEBSOCKET_FIX_GUIDE.md for instructions."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please set up Binance API credentials first."
        exit 1
    fi
else
    echo "✓ Binance API credentials found"
fi
echo ""

# Step 2: Stop containers
echo "[2/5] Stopping containers..."
docker-compose -f docker-compose.prod.yml stop backend
echo "✓ Backend stopped"
echo ""

# Step 3: Rebuild backend
echo "[3/5] Rebuilding backend with WebSocket fixes..."
docker-compose -f docker-compose.prod.yml build backend
if [ $? -ne 0 ]; then
    echo "ERROR: Backend build failed!"
    exit 1
fi
echo "✓ Backend rebuilt successfully"
echo ""

# Step 4: Rebuild frontend
echo "[4/5] Rebuilding frontend with ping/pong handlers..."
docker-compose -f docker-compose.prod.yml build frontend
if [ $? -ne 0 ]; then
    echo "ERROR: Frontend build failed!"
    exit 1
fi
echo "✓ Frontend rebuilt successfully"
echo ""

# Step 5: Start containers
echo "[5/5] Starting containers..."
docker-compose -f docker-compose.prod.yml up -d backend frontend
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start containers!"
    exit 1
fi
echo "✓ Containers started"
echo ""

# Show status
echo "========================================"
echo "Deployment Status"
echo "========================================"
docker-compose -f docker-compose.prod.yml ps
echo ""

# Show logs
echo "========================================"
echo "Recent Backend Logs"
echo "========================================"
docker-compose -f docker-compose.prod.yml logs --tail=20 backend
echo ""

echo "========================================"
echo "WebSocket Fix Applied Successfully!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Check that prices are updating (not \$0.0000)"
echo "3. Open browser DevTools (F12) and check Console for WebSocket messages"
echo "4. Monitor for 10-15 minutes to ensure stability"
echo ""
echo "To view live logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f backend"
echo ""
echo "If you see 'Invalid API-key' errors, update .env with real Binance credentials."
echo "See WEBSOCKET_FIX_GUIDE.md for detailed instructions."

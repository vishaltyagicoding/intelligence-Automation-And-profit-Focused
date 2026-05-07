#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP SCRIPT - Remove Unnecessary Files Before AWS Deployment
# ═══════════════════════════════════════════════════════════════════════════════
# Run this script BEFORE uploading your project to AWS
# This removes all unnecessary files that are not needed in production
# ═══════════════════════════════════════════════════════════════════════════════

echo "🧹 Starting cleanup process..."
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove Python cache files
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type f -name "*.pyd" -delete 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type f -name ".coverage" -delete 2>/dev/null
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null
echo "✅ Python cache files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove Node.js files (will be rebuilt on server)
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing Node.js build files..."
rm -rf node_modules 2>/dev/null
rm -rf .next 2>/dev/null
rm -rf out 2>/dev/null
rm -rf build 2>/dev/null
rm -rf dist 2>/dev/null
echo "✅ Node.js build files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove OS-specific files
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing OS-specific files..."
find . -type f -name ".DS_Store" -delete 2>/dev/null
find . -type f -name "Thumbs.db" -delete 2>/dev/null
find . -type f -name "desktop.ini" -delete 2>/dev/null
find . -type f -name "*.swp" -delete 2>/dev/null
find . -type f -name "*.swo" -delete 2>/dev/null
find . -type f -name "*~" -delete 2>/dev/null
echo "✅ OS-specific files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove IDE files
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing IDE files..."
rm -rf .idea 2>/dev/null
rm -rf .vscode 2>/dev/null
rm -rf .vs 2>/dev/null
rm -rf *.sublime-* 2>/dev/null
echo "✅ IDE files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove log files
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing log files..."
find ./logs -type f -name "*.log" -delete 2>/dev/null
find . -type f -name "*.log" -not -path "./logs/*" -not -path "./.git/*" -delete 2>/dev/null
echo "✅ Log files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove temporary files
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing temporary files..."
rm -rf tmp 2>/dev/null
rm -rf temp 2>/dev/null
rm -rf .tmp 2>/dev/null
find . -type f -name "*.tmp" -delete 2>/dev/null
find . -type f -name "*.temp" -delete 2>/dev/null
echo "✅ Temporary files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove development database files
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing development database files..."
rm -f db.sqlite3 2>/dev/null
rm -f *.db 2>/dev/null
echo "✅ Development database files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove unnecessary documentation (keep essential ones)
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing unnecessary documentation..."
rm -f KAGGLE_*.md 2>/dev/null
rm -f MODEL_*.md 2>/dev/null
rm -f PHASE*.md 2>/dev/null
rm -f QUICK_*.md 2>/dev/null
rm -f FINAL_*.md 2>/dev/null
rm -f FIX_*.txt 2>/dev/null
rm -f *_SUMMARY.md 2>/dev/null
rm -f *_GUIDE.md 2>/dev/null
rm -f WEBSOCKET_*.md 2>/dev/null
rm -f SIGNAL_*.md 2>/dev/null
rm -f TRAINING_*.md 2>/dev/null
rm -f TRADINGVIEW_*.md 2>/dev/null
rm -f DELTA_*.md 2>/dev/null
rm -f COPY_PASTE_COMMANDS.txt 2>/dev/null
rm -f SETUP_COMMANDS.ps1 2>/dev/null
rm -f kaggle_*.py 2>/dev/null
rm -f test_*.py 2>/dev/null
rm -f verify_*.ps1 2>/dev/null
rm -f fix-*.sh 2>/dev/null
rm -f fix-*.ps1 2>/dev/null
rm -f start_*.sh 2>/dev/null
rm -f start_*.ps1 2>/dev/null
rm -f START_*.md 2>/dev/null
rm -f START_*.ps1 2>/dev/null
rm -f build-and-run.ps1 2>/dev/null
rm -f build-and-run.sh 2>/dev/null
echo "✅ Unnecessary documentation removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove test files
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing test files..."
rm -f create_test_signals.py 2>/dev/null
rm -f test_signal_replacement.py 2>/dev/null
rm -f test_websocket_signal.py 2>/dev/null
echo "✅ Test files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove Git files (optional - uncomment if you don't want .git folder)
# ───────────────────────────────────────────────────────────────────────────────
# echo "📦 Removing Git files..."
# rm -rf .git 2>/dev/null
# rm -f .gitignore 2>/dev/null
# rm -f .gitattributes 2>/dev/null
# echo "✅ Git files removed"
# echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove Docker development files
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing Docker development files..."
rm -f docker-compose.yml 2>/dev/null
rm -f Dockerfile.backend 2>/dev/null
echo "✅ Docker development files removed (keeping docker-compose.prod.yml)"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove local environment files (keep .env.example and .env.production)
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing local environment files..."
rm -f .env 2>/dev/null
rm -f .env.local 2>/dev/null
echo "✅ Local environment files removed (keeping .env.example and .env.production)"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove media and static files (will be regenerated)
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing generated static files..."
rm -rf staticfiles/* 2>/dev/null
rm -rf media/* 2>/dev/null
echo "✅ Generated static files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Remove model files (if not needed in production)
# ───────────────────────────────────────────────────────────────────────────────
echo "📦 Removing model files..."
rm -rf models/production/* 2>/dev/null
rm -rf models/backups/* 2>/dev/null
echo "✅ Model files removed"
echo ""

# ───────────────────────────────────────────────────────────────────────────────
# Show disk space saved
# ───────────────────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "✅ CLEANUP COMPLETE!"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Current directory size:"
du -sh .
echo ""
echo "📦 Files remaining:"
find . -type f | wc -l
echo ""
echo "🚀 Your project is now ready for AWS deployment!"
echo ""
echo "Next steps:"
echo "1. Review the remaining files to ensure nothing important was deleted"
echo "2. Upload to AWS using: scp -i YOUR_KEY.pem -r . ubuntu@YOUR_EC2_IP:~/neuraltrade"
echo "3. Or commit to Git and clone on AWS: git clone YOUR_REPO"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"

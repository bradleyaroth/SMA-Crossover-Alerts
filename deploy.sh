#!/bin/bash

# SMA Crossover Alerts - Deployment Script
# This script sets up automated daily execution via cron

set -e

echo "🚀 Deploying SMA Crossover Alerts..."

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python3"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"

# Verify files exist
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Virtual environment not found. Run ./install.sh first"
    exit 1
fi

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ Main script not found: $MAIN_SCRIPT"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/config/config.ini" ]; then
    echo "❌ Configuration file not found. Copy config.sample.ini to config.ini and configure"
    exit 1
fi

# Test the application
echo "🧪 Testing application..."
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 main.py --dry-run

if [ $? -ne 0 ]; then
    echo "❌ Application test failed. Please check configuration"
    exit 1
fi

echo "✅ Application test passed"

# Create cron job
CRON_JOB="0 7 * * 1-5 cd $SCRIPT_DIR && $PYTHON_PATH $MAIN_SCRIPT >> logs/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$MAIN_SCRIPT"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove existing job
    crontab -l 2>/dev/null | grep -v "$MAIN_SCRIPT" | crontab -
fi

# Add new cron job
echo "📅 Adding cron job..."
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Deployment complete!"
echo ""
echo "Cron job scheduled:"
echo "  - Runs weekdays at 7:00 AM"
echo "  - Logs to: logs/cron.log"
echo ""
echo "Manual execution:"
echo "  cd $SCRIPT_DIR && python3 main.py"
echo ""
echo "View cron jobs: crontab -l"
echo "Remove cron job: crontab -e"
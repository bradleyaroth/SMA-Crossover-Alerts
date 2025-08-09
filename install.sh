#!/bin/bash

# SMA Crossover Alerts - Installation Script
# This script installs and configures the SMA Crossover Alerts system

set -e  # Exit on any error

echo "🚀 Installing SMA Crossover Alerts..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p config

# Copy sample configuration if config.ini doesn't exist
if [ ! -f "config/config.ini" ]; then
    echo "📋 Creating configuration file..."
    cp config/config.sample.ini config/config.ini
    echo "⚠️  Please edit config/config.ini with your settings before running"
else
    echo "✅ Configuration file already exists"
fi

# Make scripts executable
chmod +x deploy.sh
chmod +x main.py

echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit config/config.ini with your settings"
echo "2. Test the application: python3 main.py --dry-run"
echo "3. Deploy with cron: ./deploy.sh"
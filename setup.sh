#!/bin/bash

# V1b Trading Strategy Bot Setup Script

echo "🚀 Setting up V1b Trading Strategy Alert Bot..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
chmod +x trading_alert_bot.py
chmod +x dashboard.py

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit alert_config.json with your email settings"
echo "2. Run: source venv/bin/activate"
echo "3. Test: python trading_alert_bot.py --mode once"
echo "4. Dashboard: streamlit run dashboard.py"
echo "5. Continuous: python trading_alert_bot.py --mode continuous"
echo ""
echo "📧 Email Setup:"
echo "- Use Gmail app password (not regular password)"
echo "- Enable 2FA and generate app password in Google Account settings"
echo ""
echo "Happy Trading! 📈"

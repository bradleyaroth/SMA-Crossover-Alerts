# SMA Crossover Alerts

A professional automated stock analysis tool that monitors any stock ticker against its 200-day Simple Moving Average (SMA) and sends email alerts when crossovers occur.

## 🎯 Features

- ✅ **Universal Stock Support**: Works with any stock ticker (AAPL, SPY, QQQ, TQQQ, MSFT, etc.)
- ✅ **Free Data Source**: Uses Yahoo Finance API (no API keys required)
- ✅ **Professional Email Alerts**: HTML/text notifications with detailed analysis
- ✅ **Automated Scheduling**: Cron-ready for daily execution
- ✅ **Robust Error Handling**: Comprehensive logging and error recovery
- ✅ **Easy Configuration**: Simple INI file configuration
- ✅ **Fallback Support**: Optional Alpha Vantage API support

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/bradleyaroth/sma-crossover-alerts.git
cd sma-crossover-alerts
```

### 2. Install
```bash
./install.sh
```

### 3. Configure
```bash
cp config/config.sample.ini config/config.ini
nano config/config.ini  # Edit with your settings
```

### 4. Test
```bash
python3 main.py --dry-run
```

### 5. Deploy
```bash
./deploy.sh
```

## 📊 Configuration Examples

### Apple Stock (AAPL)
```ini
[analysis]
symbol = AAPL
```

### S&P 500 ETF (SPY)
```ini
[analysis]
symbol = SPY
```

### ProShares UltraPro QQQ (TQQQ)
```ini
[analysis]
symbol = TQQQ
```

### Microsoft (MSFT)
```ini
[analysis]
symbol = MSFT
```

## ⚙️ Configuration

### Required Settings

Edit `config/config.ini` with your settings:

```ini
[analysis]
# Stock ticker symbol to analyze
symbol = AAPL
sma_period = 200

[email]
# SMTP server configuration
smtp_server = smtp.gmail.com
smtp_port = 587
username = your-email@gmail.com
password = your-app-password
use_tls = true
from_name = SMA Crossover Alerts
from_address = your-email@gmail.com
to_addresses = recipient1@example.com,recipient2@example.com
```

### Email Setup (Gmail Example)

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated password in `config.ini`

### Email Setup (Other Providers)

**Outlook/Hotmail:**
```ini
smtp_server = smtp-mail.outlook.com
smtp_port = 587
```

**Yahoo Mail:**
```ini
smtp_server = smtp.mail.yahoo.com
smtp_port = 587
```

**Custom SMTP:**
```ini
smtp_server = your-smtp-server.com
smtp_port = 587
```

## 🔧 Usage

### Command Line Options

```bash
# Run analysis with email notification
python3 main.py

# Run analysis without sending email (test mode)
python3 main.py --dry-run

# Test email configuration
python3 main.py --test-email

# Test API connectivity
python3 main.py --test-api

# Use custom configuration file
python3 main.py --config /path/to/config.ini

# Enable verbose logging
python3 main.py --verbose
```

### Automated Execution

The `deploy.sh` script sets up a cron job for automated daily execution:

```bash
./deploy.sh
```

This creates a cron job that runs weekdays at 7:00 AM:
```
0 7 * * 1-5 cd /path/to/sma-crossover-alerts && python3 main.py >> logs/cron.log 2>&1
```

### Manual Cron Setup

```bash
# Edit crontab
crontab -e

# Add line for daily execution at 7 AM (weekdays only)
0 7 * * 1-5 cd /path/to/sma-crossover-alerts && python3 main.py >> logs/cron.log 2>&1

# View current cron jobs
crontab -l
```

## 📧 Email Notifications

### Crossover Alert Example

**Subject:** SMA Crossover Alert: AAPL Above 200-day SMA

**Content:**
- Current Price: $150.25
- 200-day SMA: $148.50
- Status: Above SMA (+1.18%)
- Analysis Date: 2024-01-15
- Trend Signal: Bullish

### Error Notification Example

**Subject:** SMA Crossover Alert Error

**Content:**
- Error Type: API Error
- Error Message: Rate limit exceeded
- Timestamp: 2024-01-15 07:00:00
- Symbol: AAPL

## 📁 Project Structure

```
sma-crossover-alerts/
├── main.py                 # Main application entry point
├── install.sh             # Installation script
├── deploy.sh              # Deployment script
├── requirements.txt       # Python dependencies
├── config/
│   ├── config.ini         # Your configuration (created from sample)
│   └── config.sample.ini  # Sample configuration template
├── src/
│   └── sma_crossover_alerts/
│       ├── api/           # API clients and data providers
│       ├── analysis/      # Data processing and analysis
│       ├── config/        # Configuration management
│       ├── notification/  # Email notifications
│       └── utils/         # Utilities and error handling
├── tests/                 # Test suite
├── logs/                  # Application logs
└── README.md             # This file
```

## 🔍 Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Email Authentication Failed:**
- Verify SMTP settings
- Check app password (not regular password)
- Test with: `python3 main.py --test-email`

**API Errors:**
- Yahoo Finance is free but may have rate limits
- Consider using Alpha Vantage as fallback
- Test with: `python3 main.py --test-api`

**Cron Job Not Running:**
```bash
# Check cron service
sudo systemctl status cron

# View cron logs
tail -f logs/cron.log

# Verify cron job exists
crontab -l
```

### Log Files

- **Application logs:** `logs/sma_crossover_alerts.log`
- **Cron execution logs:** `logs/cron.log`
- **Error logs:** Check application logs for detailed error information

### Debug Mode

```bash
# Run with verbose logging
python3 main.py --verbose

# Check specific log entries
tail -f logs/sma_crossover_alerts.log
```

## 🧪 Testing

### Run Test Suite
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/sma_crossover_alerts
```

### Manual Testing
```bash
# Test configuration
python3 main.py --dry-run

# Test email setup
python3 main.py --test-email

# Test API connectivity
python3 main.py --test-api
```

## 🔧 Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/bradleyaroth/sma-crossover-alerts.git
cd sma-crossover-alerts

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## 📋 Requirements

- **Python:** 3.8 or higher
- **Operating System:** Linux, macOS, Windows
- **Dependencies:** See `requirements.txt`
- **Email:** SMTP server access (Gmail, Outlook, etc.)
- **Internet:** For stock data API access

## 🔒 Security

- Store sensitive credentials in `config/config.ini` (not version controlled)
- Use app passwords instead of regular passwords
- Restrict file permissions: `chmod 600 config/config.ini`
- Keep API keys secure and rotate regularly

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/bradleyaroth/sma-crossover-alerts/issues)
- **Documentation:** This README and inline code comments
- **Email:** For private inquiries

## 🔄 Updates

### Version History

- **v1.0.0:** Initial release with universal stock support
- **v0.9.0:** Beta release with TQQQ-specific functionality

### Upgrade Instructions

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Update configuration if needed
cp config/config.sample.ini config/config.new.ini
# Merge your settings from config.ini to config.new.ini
```

## 🎯 Roadmap

- [ ] Web dashboard for monitoring multiple stocks
- [ ] Mobile app notifications
- [ ] Advanced technical indicators
- [ ] Portfolio-level analysis
- [ ] Real-time alerts (intraday)
- [ ] Integration with trading platforms

---

**Made with ❤️ for stock market enthusiasts**# SMA-Crossover-Alerts

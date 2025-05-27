# Network Monitor

A professional network monitoring tool built with Python that provides real-time monitoring of hosts and services with comprehensive alerting and dashboard capabilities.

## 🌟 Features

- **Real-time Host Monitoring** - ICMP ping monitoring with response time tracking
- **Service Port Monitoring** - TCP port connectivity testing for critical services  
- **Live Dashboard** - Real-time status display with colored output and statistics
- **Flexible Alerting** - Console and email notifications for service state changes
- **Comprehensive Logging** - Rotating log files with configurable levels
- **JSON Configuration** - Easy-to-modify configuration for monitoring targets
- **Professional Architecture** - Modular design following Python best practices
- **Cross-platform** - Works on Windows, Linux, and macOS
- **Lightweight** - Minimal resource usage, perfect for low-spec machines

## 📋 Requirements

- Python 3.7+
- 7.7GB RAM (lightweight and efficient)
- Network connectivity to monitored targets

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd network-monitor
pip install -r requirements.txt
```

### 2. Create Configuration

```bash
python -m src.main --create-config
```

### 3. Start Monitoring

```bash
python -m src.main
```

## 📁 Project Structure

```
network-monitor/
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── config.json              # Configuration file
├── src/                     # Source code
│   ├── main.py              # Entry point
│   ├── monitor.py           # Main orchestrator
│   ├── ping_checker.py      # Host ping functionality
│   ├── port_checker.py      # Port connectivity testing
│   ├── alert_system.py      # Notification system
│   ├── logger.py            # Logging system
│   ├── config_manager.py    # Configuration management
│   └── dashboard.py         # Real-time dashboard
├── logs/                    # Log files
├── data/                    # Status history data
└── tests/                   # Unit tests
```

## ⚙️ Configuration

Edit `config.json` to customize your monitoring setup:

### Monitoring Settings
```json
{
  "monitoring": {
    "interval": 30,        # Check interval in seconds
    "timeout": 5,          # Connection timeout
    "max_retries": 3       # Retry attempts
  }
}
```

### Host Monitoring
```json
{
  "targets": {
    "hosts": [
      {
        "name": "localhost",
        "ip": "127.0.0.1",
        "enabled": true
      }
    ]
  }
}
```

### Service Monitoring
```json
{
  "services": [
    {
      "name": "HTTP Server",
      "host": "127.0.0.1",
      "port": 80,
      "enabled": true
    }
  ]
}
```

### Alert Configuration
```json
{
  "alerts": {
    "enabled": true,
    "console": true,
    "email": false,
    "email_settings": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your-email@gmail.com",
      "password": "your-app-password",
      "to_email": "alerts@yourcompany.com"
    }
  }
}
```

## 🎯 Usage Examples

### Basic Monitoring
```bash
# Start with default configuration
python -m src.main

# Use custom configuration file
python -m src.main -c custom_config.json
```

### Single Check Mode
```bash
# Run one check cycle and exit
python -m src.main --check
```

### Testing
```bash
# Test alert system
python -m src.main --test-alerts

# Create sample configuration
python -m src.main --create-config
```

### Command Line Options
```bash
python -m src.main --help
```

## 📊 Dashboard Features

The live dashboard displays:

- **System Summary** - Uptime, check counts, success rates
- **Host Status** - Real-time ping results with response times
- **Service Status** - Port connectivity with connection times  
- **Recent Alerts** - Last 10 alerts with timestamps
- **Configuration Info** - Current monitoring settings

### Dashboard Controls
- **Ctrl+C** - Stop monitoring gracefully
- **Auto-refresh** - Updates every 30 seconds
- **Color-coded status** - Green (UP), Red (DOWN), Yellow (WARNING)

## 🔔 Alert System

### Alert Types
- **Service Down** - When a monitored port becomes unreachable
- **Service Up** - When a service recovers from downtime
- **Host Down** - When ping to a host fails
- **Host Up** - When a host becomes reachable again

### Alert Methods
1. **Console Alerts** - Colored terminal notifications
2. **Email Alerts** - HTML email notifications (configurable)
3. **Log Alerts** - Detailed logging of all events

### Alert Features
- **Cooldown Period** - Prevents alert spam (5-minute default)
- **Rich Formatting** - Color-coded console output
- **Email Templates** - Professional HTML email alerts
- **Alert History** - Track recent alerts in dashboard

## 📝 Logging

### Log Levels
- **DEBUG** - Detailed diagnostic information
- **INFO** - General information and successful operations
- **WARNING** - Warning messages and failed checks
- **ERROR** - Error conditions and service failures
- **CRITICAL** - Critical system errors

### Log Features
- **Rotating Files** - Automatic log rotation by size
- **Structured Format** - Timestamp, level, and detailed messages
- **Console Output** - Real-time log display
- **Configurable** - Adjust levels and file locations

## 🔧 Development Setup

### Running Tests
```bash
# Run unit tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_ping_checker.py
```

### Code Structure
The project follows clean architecture principles:

- **Separation of Concerns** - Each module has a single responsibility
- **
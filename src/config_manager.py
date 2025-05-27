"""
Configuration Manager for Network Monitor
Handles loading and validating configuration settings
"""
import json
import os
from typing import Dict, List, Any


class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from JSON file"""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Configuration file {self.config_path} not found")
            
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            self._validate_config()
            print(f"✓ Configuration loaded from {self.config_path}")
            
        except Exception as e:
            print(f"✗ Error loading configuration: {e}")
            self._create_default_config()

    def _validate_config(self) -> None:
        """Validate required configuration sections"""
        required_sections = ['monitoring', 'targets', 'alerts', 'logging']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")

    def _create_default_config(self) -> None:
        """Create default configuration if none exists"""
        default_config = {
            "monitoring": {
                "interval": 30,
                "timeout": 5,
                "max_retries": 3
            },
            "targets": {
                "hosts": [
                    {"name": "localhost", "ip": "127.0.0.1", "enabled": True}
                ],
                "services": [
                    {"name": "HTTP Server", "host": "127.0.0.1", "port": 80, "enabled": True}
                ]
            },
            "alerts": {
                "enabled": True,
                "console": True,
                "email": False
            },
            "logging": {
                "level": "INFO",
                "file": "logs/network_monitor.log"
            }
        }
        
        self.config = default_config
        self.save_config()
        print("✓ Default configuration created")

    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"✗ Error saving configuration: {e}")

    def get_monitoring_interval(self) -> int:
        """Get monitoring interval in seconds"""
        return self.config.get('monitoring', {}).get('interval', 30)

    def get_timeout(self) -> int:
        """Get connection timeout in seconds"""
        return self.config.get('monitoring', {}).get('timeout', 5)

    def get_max_retries(self) -> int:
        """Get maximum retry attempts"""
        return self.config.get('monitoring', {}).get('max_retries', 3)

    def get_hosts(self) -> List[Dict[str, Any]]:
        """Get list of hosts to monitor"""
        hosts = self.config.get('targets', {}).get('hosts', [])
        return [host for host in hosts if host.get('enabled', True)]

    def get_services(self) -> List[Dict[str, Any]]:
        """Get list of services to monitor"""
        services = self.config.get('targets', {}).get('services', [])
        return [service for service in services if service.get('enabled', True)]

    def is_alerts_enabled(self) -> bool:
        """Check if alerts are enabled"""
        return self.config.get('alerts', {}).get('enabled', True)

    def is_console_alerts_enabled(self) -> bool:
        """Check if console alerts are enabled"""
        return self.config.get('alerts', {}).get('console', True)

    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get('logging', {})

    def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration"""
        return self.config.get('alerts', {}).get('email_settings', {})

    def is_email_alerts_enabled(self) -> bool:
        """Check if email alerts are enabled"""
        return self.config.get('alerts', {}).get('email', False)
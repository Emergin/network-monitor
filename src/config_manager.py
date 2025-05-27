import json
import os
from typing import Dict, List, Any

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self._create_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self._create_default_config()
    
    def save_config(self) -> None:
        """Save current configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key (supports dot notation)"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_hosts(self) -> List[Dict]:
        """Get list of hosts to monitor"""
        return self.get('hosts', [])
    
    def get_enabled_hosts(self) -> List[Dict]:
        """Get list of enabled hosts to monitor"""
        return [host for host in self.get_hosts() if host.get('enabled', True)]
    
    def get_ports(self) -> List[Dict]:
        """Get list of ports to monitor"""
        return self.get('ports', [])
    
    def get_monitoring_config(self) -> Dict:
        """Get monitoring configuration"""
        return self.get('monitoring', {})
    
    def get_alert_config(self) -> Dict:
        """Get alert configuration"""
        return self.get('alerts', {})
    
    def get_logging_config(self) -> Dict:
        """Get logging configuration"""
        return self.get('logging', {})
    
    def get_dashboard_config(self) -> Dict:
        """Get dashboard configuration"""
        return self.get('dashboard', {})
    
    def add_host(self, name: str, address: str, enabled: bool = True) -> None:
        """Add a new host to monitor"""
        hosts = self.get_hosts()
        hosts.append({
            'name': name,
            'address': address,
            'enabled': enabled
        })
        self.set('hosts', hosts)
    
    def remove_host(self, name: str) -> bool:
        """Remove a host from monitoring"""
        hosts = self.get_hosts()
        original_length = len(hosts)
        hosts = [host for host in hosts if host.get('name') != name]
        
        if len(hosts) < original_length:
            self.set('hosts', hosts)
            return True
        return False
    
    def toggle_host(self, name: str) -> bool:
        """Toggle host enabled/disabled status"""
        hosts = self.get_hosts()
        for host in hosts:
            if host.get('name') == name:
                host['enabled'] = not host.get('enabled', True)
                self.set('hosts', hosts)
                return True
        return False
    
    def _create_default_config(self) -> None:
        """Create default configuration"""
        self.config = {
            "hosts": [
                {"name": "Google DNS", "address": "8.8.8.8", "enabled": True},
                {"name": "Localhost", "address": "127.0.0.1", "enabled": True}
            ],
            "ports": [
                {"port": 80, "name": "HTTP", "protocol": "tcp"},
                {"port": 443, "name": "HTTPS", "protocol": "tcp"},
                {"port": 22, "name": "SSH", "protocol": "tcp"}
            ],
            "monitoring": {
                "ping_interval": 30,
                "port_check_interval": 60,
                "timeout": 5,
                "max_retries": 3,
                "alert_threshold": 3
            },
            "alerts": {
                "email": {"enabled": False},
                "console": {"enabled": True}
            },
            "logging": {
                "level": "INFO",
                "max_file_size": "10MB",
                "backup_count": 5
            },
            "dashboard": {
                "refresh_interval": 30,
                "show_offline_only": False,
                "max_history_days": 30
            }
        }
        self.save_config()
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from config_manager import ConfigManager

class NetworkLogger:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.loggers = {}
        self._setup_directories()
        self._setup_loggers()
    
    def _setup_directories(self) -> None:
        """Create necessary directories"""
        os.makedirs('logs', exist_ok=True)
    
    def _setup_loggers(self) -> None:
        """Setup different loggers for different components"""
        log_config = self.config.get_logging_config()
        
        # Main logger
        self.loggers['main'] = self._create_logger(
            'NetworkMonitor',
            'logs/network_monitor.log',
            log_config
        )
        
        # Ping logger
        self.loggers['ping'] = self._create_logger(
            'PingChecker',
            'logs/ping_checks.log',
            log_config
        )
        
        # Port logger
        self.loggers['port'] = self._create_logger(
            'PortChecker',
            'logs/port_checks.log',
            log_config
        )
        
        # Alert logger
        self.loggers['alert'] = self._create_logger(
            'AlertSystem',
            'logs/alerts.log',
            log_config
        )
        
        # Dashboard logger
        self.loggers['dashboard'] = self._create_logger(
            'Dashboard',
            'logs/dashboard.log',
            log_config
        )
    
    def _create_logger(self, name: str, filename: str, config: dict) -> logging.Logger:
        """Create a configured logger"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, config.get('level', 'INFO')))
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # File handler with rotation
        max_bytes = self._parse_size(config.get('max_file_size', '10MB'))
        file_handler = RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=config.get('backup_count', 5)
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Formatter
        formatter = logging.Formatter(
            config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '10MB') to bytes"""
        size_str = size_str.upper().strip()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def get_logger(self, name: str = 'main') -> logging.Logger:
        """Get logger by name"""
        return self.loggers.get(name, self.loggers['main'])
    
    def log_ping_result(self, host: str, success: bool, response_time: Optional[float] = None):
        """Log ping result"""
        logger = self.get_logger('ping')
        if success:
            logger.info(f"Ping to {host} successful - Response time: {response_time:.2f}ms")
        else:
            logger.warning(f"Ping to {host} failed")
    
    def log_port_result(self, host: str, port: int, success: bool, response_time: Optional[float] = None):
        """Log port check result"""
        logger = self.get_logger('port')
        if success:
            logger.info(f"Port {port} on {host} is open - Response time: {response_time:.2f}ms")
        else:
            logger.warning(f"Port {port} on {host} is closed or unreachable")
    
    def log_alert(self, message: str, level: str = 'INFO'):
        """Log alert message"""
        logger = self.get_logger('alert')
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"ALERT: {message}")
    
    def log_dashboard_activity(self, message: str):
        """Log dashboard activity"""
        logger = self.get_logger('dashboard')
        logger.info(message)
    
    def log_error(self, component: str, error: Exception):
        """Log error with component context"""
        logger = self.get_logger(component)
        logger.error(f"Error in {component}: {str(error)}", exc_info=True)
    
    def log_system_info(self, message: str):
        """Log system information"""
        logger = self.get_logger('main')
        logger.info(f"SYSTEM: {message}")
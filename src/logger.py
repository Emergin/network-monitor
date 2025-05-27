"""
Centralized Logging System for Network Monitor
Handles all logging operations with rotation and formatting
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict, Any


class NetworkLogger:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('NetworkMonitor')
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Setup logger with file and console handlers"""
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set logging level
        level = getattr(logging, self.config.get('level', 'INFO').upper(), logging.INFO)
        self.logger.setLevel(level)

        # Create logs directory if it doesn't exist
        log_file = self.config.get('file', 'logs/network_monitor.log')
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.get('max_size_mb', 10) * 1024 * 1024,  # Convert MB to bytes
            backupCount=self.config.get('backup_count', 5)
        )

        # Console handler
        console_handler = logging.StreamHandler()

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        # Set formatters
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(message)

    def critical(self, message: str) -> None:
        """Log critical message"""
        self.logger.critical(message)

    def log_ping_result(self, host: str, success: bool, response_time: float = None) -> None:
        """Log ping test result"""
        if success:
            msg = f"PING {host}: SUCCESS - Response time: {response_time:.2f}ms"
            self.info(msg)
        else:
            msg = f"PING {host}: FAILED - Host unreachable"
            self.warning(msg)

    def log_port_result(self, host: str, port: int, success: bool, response_time: float = None) -> None:
        """Log port check result"""
        if success:
            msg = f"PORT {host}:{port}: OPEN - Connection time: {response_time:.2f}ms"
            self.info(msg)
        else:
            msg = f"PORT {host}:{port}: CLOSED - Connection failed"
            self.warning(msg)

    def log_service_down(self, service_name: str, host: str, port: int = None) -> None:
        """Log service downtime event"""
        if port:
            msg = f"SERVICE DOWN: {service_name} on {host}:{port}"
        else:
            msg = f"HOST DOWN: {service_name} ({host})"
        self.error(msg)

    def log_service_up(self, service_name: str, host: str, port: int = None) -> None:
        """Log service recovery event"""
        if port:
            msg = f"SERVICE RECOVERED: {service_name} on {host}:{port}"
        else:
            msg = f"HOST RECOVERED: {service_name} ({host})"
        self.info(msg)

    def log_monitor_start(self) -> None:
        """Log monitoring session start"""
        self.info("=" * 50)
        self.info("Network Monitor started")
        self.info(f"Session started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("=" * 50)

    def log_monitor_stop(self) -> None:
        """Log monitoring session stop"""
        self.info("=" * 50)
        self.info("Network Monitor stopped")
        self.info(f"Session ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("=" * 50)
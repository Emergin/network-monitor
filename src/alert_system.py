"""
Alert System Module
Handles notifications and alerts for network monitoring events
"""
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class AlertSystem:
    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.logger = logger
        self.alert_history = {}  # Track alert history to prevent spam
        self.cooldown_period = 300  # 5 minutes cooldown between same alerts
        
    def send_alert(self, alert_type: str, service_name: str, host: str, port: Optional[int] = None, 
                   message: str = None) -> None:
        """
        Send alert notification
        
        Args:
            alert_type: Type of alert ('service_down', 'service_up', 'host_down', 'host_up')
            service_name: Name of the service or host
            host: IP address or hostname
            port: Port number (if applicable)
            message: Custom alert message
        """
        # Create alert key for cooldown tracking
        alert_key = f"{alert_type}_{service_name}_{host}_{port}"
        current_time = time.time()
        
        # Check cooldown period
        if self._is_in_cooldown(alert_key, current_time):
            return
        
        # Update alert history
        self.alert_history[alert_key] = current_time
        
        # Generate alert message
        if not message:
            message = self._generate_alert_message(alert_type, service_name, host, port)
        
        # Send console alert
        if self.config.get('console', True):
            self._send_console_alert(alert_type, message)
        
        # Send email alert
        if self.config.get('email', False):
            self._send_email_alert(alert_type, message, service_name)
        
        # Log the alert
        if self.logger:
            if 'down' in alert_type.lower():
                self.logger.error(f"ALERT: {message}")
            else:
                self.logger.info(f"ALERT: {message}")
    
    def _is_in_cooldown(self, alert_key: str, current_time: float) -> bool:
        """Check if alert is in cooldown period"""
        if alert_key in self.alert_history:
            time_diff = current_time - self.alert_history[alert_key]
            return time_diff < self.cooldown_period
        return False
    
    def _generate_alert_message(self, alert_type: str, service_name: str, 
                              host: str, port: Optional[int] = None) -> str:
        """Generate formatted alert message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if alert_type == 'service_down':
            return f"[{timestamp}] SERVICE DOWN: {service_name} on {host}:{port} is not responding"
        elif alert_type == 'service_up':
            return f"[{timestamp}] SERVICE RECOVERED: {service_name} on {host}:{port} is back online"
        elif alert_type == 'host_down':
            return f"[{timestamp}] HOST DOWN: {service_name} ({host}) is unreachable"
        elif alert_type == 'host_up':
            return f"[{timestamp}] HOST RECOVERED: {service_name} ({host}) is back online"
        else:
            return f"[{timestamp}] ALERT: {service_name} - {alert_type}"
    
    def _send_console_alert(self, alert_type: str, message: str) -> None:
        """Send alert to console with colors"""
        try:
            if 'down' in alert_type.lower():
                # Red for down alerts
                print(f"{Fore.RED}{'🔴 ' + message}{Style.RESET_ALL}")
            elif 'up' in alert_type.lower() or 'recover' in alert_type.lower():
                # Green for recovery alerts
                print(f"{Fore.GREEN}{'🟢 ' + message}{Style.RESET_ALL}")
            else:
                # Yellow for other alerts
                print(f"{Fore.YELLOW}{'🟡 ' + message}{Style.RESET_ALL}")
        except Exception as e:
            print(f"Error sending console alert: {e}")
    
    def _send_email_alert(self, alert_type: str, message: str, service_name: str) -> None:
        """Send alert via email"""
        try:
            email_config = self.config.get('email_settings', {})
            
            # Check if email is properly configured
            if not all([email_config.get('smtp_server'), 
                       email_config.get('username'), 
                       email_config.get('password'),
                       email_config.get('to_email')]):
                if self.logger:
                    self.logger.warning("Email alerts enabled but configuration incomplete")
                return
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_config['username']
            msg['To'] = email_config['to_email']
            
            # Set subject based on alert type
            if 'down' in alert_type.lower():
                msg['Subject'] = f"🔴 ALERT: {service_name} is DOWN"
            else:
                msg['Subject'] = f"🟢 RECOVERY: {service_name} is UP"
            
            # Create email body
            body = self._create_email_body(alert_type, message, service_name)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config.get('smtp_port', 587))
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            
            text = msg.as_string()
            server.sendmail(email_config['username'], email_config['to_email'], text)
            server.quit()
            
            if self.logger:
                self.logger.info(f"Email alert sent for {service_name}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to send email alert: {e}")
    
    def _create_email_body(self, alert_type: str, message: str, service_name: str) -> str:
        """Create HTML email body"""
        color = "#dc3545" if 'down' in alert_type.lower() else "#28a745"
        icon = "🔴" if 'down' in alert_type.lower() else "🟢"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="border-left: 4px solid {color}; padding-left: 20px;">
                <h2 style="color: {color}; margin-top: 0;">
                    {icon} Network Monitor Alert
                </h2>
                <p style="font-size: 16px; margin: 10px 0;">
                    <strong>Service:</strong> {service_name}
                </p>
                <p style="font-size: 16px; margin: 10px 0;">
                    <strong>Status:</strong> {alert_type.replace('_', ' ').title()}
                </p>
                <p style="font-size: 16px; margin: 10px 0;">
                    <strong>Details:</strong> {message}
                </p>
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    This alert was generated by Network Monitor at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
    
    def send_test_alert(self) -> None:
        """Send test alert to verify alert system is working"""
        test_message = f"Network Monitor test alert - System is working properly"
        
        if self.config.get('console', True):
            print(f"{Fore.CYAN}🔵 TEST ALERT: {test_message}{Style.RESET_ALL}")
        
        if self.config.get('email', False):
            self._send_email_alert('test_alert', test_message, 'Network Monitor')
        
        if self.logger:
            self.logger.info(f"TEST ALERT: {test_message}")
    
    def send_summary_alert(self, summary_data: Dict[str, Any]) -> None:
        """Send periodic summary alert"""
        total_hosts = summary_data.get('total_hosts', 0)
        up_hosts = summary_data.get('up_hosts', 0)
        total_services = summary_data.get('total_services', 0)
        up_services = summary_data.get('up_services', 0)
        
        message = (f"Network Monitor Summary - "
                  f"Hosts: {up_hosts}/{total_hosts} UP, "
                  f"Services: {up_services}/{total_services} UP")
        
        if self.config.get('console', True):
            if up_hosts == total_hosts and up_services == total_services:
                print(f"{Fore.GREEN}📊 {message}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}📊 {message}{Style.RESET_ALL}")
        
        if self.logger:
            self.logger.info(f"SUMMARY: {message}")
    
    def clear_alert_history(self) -> None:
        """Clear alert history (useful for testing)"""
        self.alert_history.clear()
        if self.logger:
            self.logger.info("Alert history cleared")
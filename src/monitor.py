"""
Main Monitor Module
Orchestrates all monitoring activities and coordinates components
"""
import time
import threading
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from .config_manager import ConfigManager
from .logger import NetworkLogger
from .ping_checker import PingChecker
from .port_checker import PortChecker
from .alert_system import AlertSystem
from .dashboard import Dashboard


class NetworkMonitor:
    def __init__(self, config_path: str = "config.json"):
        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.logger = NetworkLogger(self.config_manager.get_log_config())
        self.ping_checker = PingChecker(timeout=self.config_manager.get_timeout())
        self.port_checker = PortChecker(timeout=self.config_manager.get_timeout())
        self.alert_system = AlertSystem(
            self.config_manager.config.get('alerts', {}), 
            self.logger
        )
        self.dashboard = Dashboard(self.config_manager)
        
        # Monitoring state
        self.is_running = False
        self.monitor_thread = None
        self.last_results = {
            'hosts': {},
            'services': {}
        }
        self.previous_status = {
            'hosts': {},
            'services': {}
        }
        self.alert_history = []
        self.status_history_file = "data/status_history.json"
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        self.logger.log_monitor_start()
    
    def start_monitoring(self) -> None:
        """Start the monitoring process"""
        if self.is_running:
            self.logger.warning("Monitoring is already running")
            return
        
        self.is_running = True
        self.dashboard.display_startup_message()
        time.sleep(3)  # Give user time to read startup message
        
        # Start monitoring in separate thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start dashboard updates
        self._dashboard_loop()
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring process"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.log_monitor_stop()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Save final status
        self._save_status_history()
        
        print("\n" + "="*50)
        print("Network Monitor stopped gracefully")
        print("="*50)
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        interval = self.config_manager.get_monitoring_interval()
        
        while self.is_running:
            try:
                # Perform checks
                self._perform_checks()
                
                # Wait for next interval
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _perform_checks(self) -> None:
        """Perform all monitoring checks"""
        # Get targets from configuration
        hosts = self.config_manager.get_hosts()
        services = self.config_manager.get_services()
        
        # Perform ping checks
        if hosts:
            host_results = self.ping_checker.ping_multiple_hosts(hosts)
            self._process_host_results(host_results)
            self.last_results['hosts'] = host_results
        
        # Perform port checks
        if services:
            service_results = self.port_checker.check_multiple_ports(services)
            self._process_service_results(service_results)
            self.last_results['services'] = service_results
        
        # Update dashboard stats
        self.dashboard.update_stats(
            self.last_results.get('hosts', {}),
            self.last_results.get('services', {})
        )
        
        # Save status history
        self._save_status_history()
    
    def _process_host_results(self, host_results: Dict[str, Any]) -> None:
        """Process host ping results and generate alerts"""
        for host_name, result in host_results.items():
            current_status = result.get('success', False)
            previous_status = self.previous_status.get('hosts', {}).get(host_name, {}).get('success')
            
            # Log result
            if current_status:
                self.logger.log_ping_result(
                    result.get('ip', host_name), 
                    True, 
                    result.get('response_time')
                )
            else:
                self.logger.log_ping_result(result.get('ip', host_name), False)
            
            # Check for status changes
            if previous_status is not None and current_status != previous_status:
                if current_status:
                    # Host came back up
                    self.alert_system.send_alert(
                        'host_up', host_name, result.get('ip', host_name)
                    )
                    self.logger.log_service_up(host_name, result.get('ip', host_name))
                    self._add_alert_to_history('host_up', host_name, f"Host {host_name} recovered")
                else:
                    # Host went down
                    self.alert_system.send_alert(
                        'host_down', host_name, result.get('ip', host_name)
                    )
                    self.logger.log_service_down(host_name, result.get('ip', host_name))
                    self._add_alert_to_history('host_down', host_name, f"Host {host_name} is unreachable")
        
        # Update previous status
        if 'hosts' not in self.previous_status:
            self.previous_status['hosts'] = {}
        self.previous_status['hosts'].update(host_results)
    
    def _process_service_results(self, service_results: Dict[str, Any]) -> None:
        """Process service port results and generate alerts"""
        for service_name, result in service_results.items():
            current_status = result.get('success', False)
            previous_status = self.previous_status.get('services', {}).get(service_name, {}).get('success')
            
            # Log result
            if current_status:
                self.logger.log_port_result(
                    result.get('host', 'unknown'),
                    result.get('port', 0),
                    True,
                    result.get('response_time')
                )
            else:
                self.logger.log_port_result(
                    result.get('host', 'unknown'),
                    result.get('port', 0),
                    False
                )
            
            # Check for status changes
            if previous_status is not None and current_status != previous_status:
                if current_status:
                    # Service came back up
                    self.alert_system.send_alert(
                        'service_up', service_name, 
                        result.get('host', 'unknown'), 
                        result.get('port')
                    )
                    self.logger.log_service_up(
                        service_name, 
                        result.get('host', 'unknown'), 
                        result.get('port')
                    )
                    self._add_alert_to_history(
                        'service_up', service_name, 
                        f"Service {service_name} recovered"
                    )
                else:
                    # Service went down
                    self.alert_system.send_alert(
                        'service_down', service_name,
                        result.get('host', 'unknown'),
                        result.get('port')
                    )
                    self.logger.log_service_down(
                        service_name,
                        result.get('host', 'unknown'),
                        result.get('port')
                    )
                    self._add_alert_to_history(
                        'service_down', service_name,
                        f"Service {service_name} is not responding"
                    )
        
        # Update previous status
        if 'services' not in self.previous_status:
            self.previous_status['services'] = {}
        self.previous_status['services'].update(service_results)
    
    def _add_alert_to_history(self, alert_type: str, service: str, message: str) -> None:
        """Add alert to history for dashboard display"""
        alert = {
            'timestamp': time.time(),
            'type': alert_type,
            'service': service,
            'message': message
        }
        
        self.alert_history.append(alert)
        
        # Keep only last 50 alerts
        if len(self.alert_history) > 50:
            self.alert_history = self.alert_history[-50:]
    
    def _dashboard_loop(self) -> None:
        """Dashboard update loop"""
        try:
            while self.is_running:
                # Update dashboard
                self.dashboard.display_full_dashboard(
                    self.last_results.get('hosts', {}),
                    self.last_results.get('services', {}),
                    self.alert_history[-10:]  # Show last 10 alerts
                )
                
                # Wait before next update
                time.sleep(30)  # Update dashboard every 30 seconds
                
        except KeyboardInterrupt:
            self.stop_monitoring()
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")
    
    def _save_status_history(self) -> None:
        """Save current status to history file"""
        try:
            history_data = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'hosts': self.last_results.get('hosts', {}),
                'services': self.last_results.get('services', {}),
                'summary': self.dashboard.get_status_overview(
                    self.last_results.get('hosts', {}),
                    self.last_results.get('services', {})
                )
            }
            
            # Load existing history
            history = []
            if os.path.exists(self.status_history_file):
                try:
                    with open(self.status_history_file, 'r') as f:
                        history = json.load(f)
                except:
                    history = []
            
            # Add new entry
            history.append(history_data)
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            # Save back to file
            with open(self.status_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving status history: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'last_check': self.dashboard.last_update,
            'hosts': self.last_results.get('hosts', {}),
            'services': self.last_results.get('services', {}),
            'recent_alerts': self.alert_history[-5:],
            'stats': self.dashboard.stats
        }
    
    def send_test_alert(self) -> None:
        """Send test alert"""
        self.alert_system.send_test_alert()
    
    def generate_summary_report(self) -> str:
        """Generate summary report"""
        overview = self.dashboard.get_status_overview(
            self.last_results.get('hosts', {}),
            self.last_results.get('services', {})
        )
        
        report = f"""
Network Monitor Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

HOST STATUS:
- Total Hosts: {overview['total_hosts']}
- Online: {overview['up_hosts']}
- Offline: {overview['down_hosts']}

SERVICE STATUS:
- Total Services: {overview['total_services']}
- Running: {overview['up_services']}
- Stopped: {overview['down_services']}

MONITORING STATS:
- Total Checks: {self.dashboard.stats['total_checks']}
- Successful: {self.dashboard.stats['successful_checks']}
- Failed: {self.dashboard.stats['failed_checks']}
- Success Rate: {(self.dashboard.stats['successful_checks'] / self.dashboard.stats['total_checks'] * 100) if self.dashboard.stats['total_checks'] > 0 else 0:.1f}%

RECENT ALERTS: {len(self.alert_history)}
        """
        
        return report
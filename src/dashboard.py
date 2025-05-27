"""
Dashboard Module
Real-time status display for network monitoring
"""
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from colorama import Fore, Back, Style, init
from tabulate import tabulate

# Initialize colorama
init(autoreset=True)


class Dashboard:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.last_update = None
        self.stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'uptime_start': datetime.now()
        }
        
    def clear_screen(self) -> None:
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self) -> None:
        """Display dashboard header"""
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("=" * 80)
        print("🌐 NETWORK MONITOR DASHBOARD".center(80))
        print("=" * 80)
        print(f"{Style.RESET_ALL}")
        
        # Display current time and uptime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        uptime = datetime.now() - self.stats['uptime_start']
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        print(f"{Fore.WHITE}Current Time: {Fore.YELLOW}{current_time}")
        print(f"{Fore.WHITE}Uptime: {Fore.GREEN}{uptime_str}")
        if self.last_update:
            print(f"{Fore.WHITE}Last Check: {Fore.CYAN}{self.last_update.strftime('%H:%M:%S')}")
        print()
    
    def display_summary_stats(self) -> None:
        """Display summary statistics"""
        total = self.stats['total_checks']
        success = self.stats['successful_checks']
        failed = self.stats['failed_checks']
        success_rate = (success / total * 100) if total > 0 else 0
        
        print(f"{Fore.WHITE}{Style.BRIGHT}📊 SUMMARY STATISTICS")
        print("-" * 40)
        
        stats_data = [
            ["Total Checks", f"{Fore.CYAN}{total}{Style.RESET_ALL}"],
            ["Successful", f"{Fore.GREEN}{success}{Style.RESET_ALL}"],
            ["Failed", f"{Fore.RED}{failed}{Style.RESET_ALL}"],
            ["Success Rate", f"{Fore.YELLOW}{success_rate:.1f}%{Style.RESET_ALL}"]
        ]
        
        print(tabulate(stats_data, tablefmt="simple"))
        print()
    
    def display_host_status(self, host_results: Dict[str, Any]) -> None:
        """Display host ping status"""
        if not host_results:
            return
            
        print(f"{Fore.WHITE}{Style.BRIGHT}🏠 HOST STATUS")
        print("-" * 60)
        
        headers = ["Host", "IP Address", "Status", "Response Time", "Last Check"]
        table_data = []
        
        for host_name, result in host_results.items():
            # Status with color
            if result.get('success', False):
                status = f"{Fore.GREEN}● UP{Style.RESET_ALL}"
                response_time = f"{result.get('response_time', 0):.1f}ms"
            else:
                status = f"{Fore.RED}● DOWN{Style.RESET_ALL}"
                response_time = "N/A"
            
            # Format timestamp
            timestamp = result.get('timestamp', time.time())
            last_check = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            
            table_data.append([
                host_name,
                result.get('ip', 'Unknown'),
                status,
                response_time,
                last_check
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()
    
    def display_service_status(self, service_results: Dict[str, Any]) -> None:
        """Display service port status"""
        if not service_results:
            return
            
        print(f"{Fore.WHITE}{Style.BRIGHT}🔧 SERVICE STATUS")
        print("-" * 80)
        
        headers = ["Service", "Host:Port", "Status", "Response Time", "Last Check"]
        table_data = []
        
        for service_name, result in service_results.items():
            # Status with color
            if result.get('success', False):
                status = f"{Fore.GREEN}● RUNNING{Style.RESET_ALL}"
                response_time = f"{result.get('response_time', 0):.1f}ms"
            else:
                status = f"{Fore.RED}● STOPPED{Style.RESET_ALL}"
                response_time = "N/A"
            
            # Format host:port
            host_port = f"{result.get('host', 'Unknown')}:{result.get('port', 'N/A')}"
            
            # Format timestamp
            timestamp = result.get('timestamp', time.time())
            last_check = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            
            table_data.append([
                service_name,
                host_port,
                status,
                response_time,
                last_check
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()
    
    def display_alerts_summary(self, recent_alerts: List[Dict[str, Any]]) -> None:
        """Display recent alerts"""
        if not recent_alerts:
            print(f"{Fore.GREEN}✅ No recent alerts - All systems operational{Style.RESET_ALL}")
            print()
            return
            
        print(f"{Fore.WHITE}{Style.BRIGHT}🚨 RECENT ALERTS")
        print("-" * 60)
        
        headers = ["Time", "Type", "Service", "Message"]
        table_data = []
        
        # Show last 5 alerts
        for alert in recent_alerts[-5:]:
            alert_time = alert.get('timestamp', time.time())
            time_str = datetime.fromtimestamp(alert_time).strftime('%H:%M:%S')
            
            alert_type = alert.get('type', 'Unknown')
            if 'down' in alert_type.lower():
                type_colored = f"{Fore.RED}{alert_type}{Style.RESET_ALL}"
            else:
                type_colored = f"{Fore.GREEN}{alert_type}{Style.RESET_ALL}"
            
            table_data.append([
                time_str,
                type_colored,
                alert.get('service', 'Unknown'),
                alert.get('message', '')[:40] + "..." if len(alert.get('message', '')) > 40 else alert.get('message', '')
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
        print()
    
    def display_configuration_info(self) -> None:
        """Display current configuration"""
        if not self.config_manager:
            return
            
        print(f"{Fore.WHITE}{Style.BRIGHT}⚙️ CONFIGURATION")
        print("-" * 40)
        
        interval = self.config_manager.get_monitoring_interval()
        timeout = self.config_manager.get_timeout()
        hosts_count = len(self.config_manager.get_hosts())
        services_count = len(self.config_manager.get_services())
        
        config_data = [
            ["Check Interval", f"{interval}s"],
            ["Timeout", f"{timeout}s"],
            ["Monitored Hosts", str(hosts_count)],
            ["Monitored Services", str(services_count)],
            ["Console Alerts", "Enabled" if self.config_manager.is_console_alerts_enabled() else "Disabled"],
            ["Email Alerts", "Enabled" if self.config_manager.is_email_alerts_enabled() else "Disabled"]
        ]
        
        print(tabulate(config_data, tablefmt="simple"))
        print()
    
    def display_footer(self) -> None:
        """Display dashboard footer"""
        print(f"{Fore.WHITE}{Style.DIM}")
        print("-" * 80)
        print("Press Ctrl+C to stop monitoring".center(80))
        print("Refreshing every 30 seconds...".center(80))
        print(f"{Style.RESET_ALL}")
    
    def update_stats(self, host_results: Dict[str, Any], service_results: Dict[str, Any]) -> None:
        """Update dashboard statistics"""
        self.last_update = datetime.now()
        
        # Count successful and failed checks
        for result in host_results.values():
            self.stats['total_checks'] += 1
            if result.get('success', False):
                self.stats['successful_checks'] += 1
            else:
                self.stats['failed_checks'] += 1
        
        for result in service_results.values():
            self.stats['total_checks'] += 1
            if result.get('success', False):
                self.stats['successful_checks'] += 1
            else:
                self.stats['failed_checks'] += 1
    
    def display_full_dashboard(self, host_results: Dict[str, Any], 
                             service_results: Dict[str, Any], 
                             recent_alerts: List[Dict[str, Any]] = None) -> None:
        """Display complete dashboard"""
        try:
            self.clear_screen()
            self.display_header()
            self.display_summary_stats()
            self.display_host_status(host_results)
            self.display_service_status(service_results)
            
            if recent_alerts:
                self.display_alerts_summary(recent_alerts)
            else:
                print(f"{Fore.GREEN}✅ No recent alerts - All systems operational{Style.RESET_ALL}")
                print()
            
            self.display_configuration_info()
            self.display_footer()
            
        except Exception as e:
            print(f"{Fore.RED}Error updating dashboard: {e}{Style.RESET_ALL}")
    
    def display_startup_message(self) -> None:
        """Display startup message"""
        self.clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("=" * 80)
        print("🚀 NETWORK MONITOR STARTING UP".center(80))
        print("=" * 80)
        print(f"{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Initializing monitoring system...")
        print(f"{Fore.YELLOW}Loading configuration...")
        print(f"{Fore.YELLOW}Starting checks in 3 seconds...")
        print(f"{Style.RESET_ALL}")
    
    def display_error_message(self, error: str) -> None:
        """Display error message"""
        print(f"{Fore.RED}{Style.BRIGHT}❌ ERROR: {error}{Style.RESET_ALL}")
    
    def display_success_message(self, message: str) -> None:
        """Display success message"""
        print(f"{Fore.GREEN}{Style.BRIGHT}✅ {message}{Style.RESET_ALL}")
    
    def get_status_overview(self, host_results: Dict[str, Any], 
                           service_results: Dict[str, Any]) -> Dict[str, int]:
        """Get overview statistics"""
        total_hosts = len(host_results)
        up_hosts = sum(1 for result in host_results.values() if result.get('success', False))
        
        total_services = len(service_results)
        up_services = sum(1 for result in service_results.values() if result.get('success', False))
        
        return {
            'total_hosts': total_hosts,
            'up_hosts': up_hosts,
            'down_hosts': total_hosts - up_hosts,
            'total_services': total_services,
            'up_services': up_services,
            'down_services': total_services - up_services
        }
#!/usr/bin/env python3
"""
Network Monitor - Main Entry Point
A comprehensive network monitoring tool for checking host availability and port status.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from monitor import NetworkMonitor

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = ['logs', 'data']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def create_default_config():
    """Create a default configuration file"""
    config = {
        "hosts": [
            "127.0.0.1",
            "8.8.8.8", 
            "1.1.1.1",
            "google.com",
            "github.com"
        ],
        "ports": [
            # Web services
            80, 443, 8080, 8443, 3000, 3001, 4200, 5173,
            # Databases
            3306, 5432, 27017, 6379, 1433, 1521,
            # Email
            25, 110, 143, 465, 587, 993, 995,
            # File sharing & Remote access
            21, 22, 23, 135, 139, 445, 3389, 5900,
            # Development
            5000, 5001, 8000, 8001, 9000, 4000, 6000, 7000,
            # System services
            53, 67, 68, 161, 162, 514,
            # Common application ports
            8096, 32400, 5050, 8989, 7878, 631, 1883, 8883, 8123
        ],
        "ping_timeout": 3,
        "port_timeout": 5,
        "check_interval": 60,
        "max_workers": 50,
        "alerts": {
            "enabled": True,
            "methods": ["console"],
            "email": {
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "to_addresses": []
            }
        }
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Default configuration file created: config.json")
    return config

def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           🌐 NETWORK MONITOR 🌐                              ║  
║                                                                               ║
║  A comprehensive network monitoring tool for checking host availability       ║
║  and port status across multiple systems and services.                       ║
║                                                                               ║
║  Features:                                                                    ║
║  • Multi-host ping monitoring                                                ║
║  • Comprehensive port scanning (80+ common ports)                            ║
║  • Real-time status dashboard                                                ║
║  • Alert system for downtime detection                                       ║
║  • Historical data tracking                                                   ║
║  • Web interface with Streamlit                                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_status_summary(monitor: NetworkMonitor):
    """Print a formatted status summary"""
    summary = monitor.get_status_summary()
    
    if summary.get("status") == "No data available":
        print("❌ No monitoring data available. Run a scan first.")
        return
    
    print("\n" + "="*80)
    print("📊 NETWORK STATUS SUMMARY")
    print("="*80)
    
    # Hosts status
    total_hosts = summary["total_hosts"]
    hosts_up = summary["hosts_up"]
    hosts_down = summary["hosts_down"]
    host_percentage = (hosts_up / total_hosts * 100) if total_hosts > 0 else 0
    
    print(f"🖥️  HOSTS:     {hosts_up}/{total_hosts} UP ({host_percentage:.1f}%)")
    if hosts_down > 0:
        print(f"❌ HOSTS DOWN: {hosts_down}")
    
    # Services status
    total_services = summary["total_services"]
    services_up = summary["services_up"]
    services_down = summary["services_down"]
    service_percentage = (services_up / total_services * 100) if total_services > 0 else 0
    
    print(f"🔌 SERVICES:  {services_up}/{total_services} UP ({service_percentage:.1f}%)")
    if services_down > 0:
        print(f"❌ SERVICES DOWN: {services_down}")
    
    # Recent alerts
    recent_alerts = summary["recent_alerts"]
    if recent_alerts > 0:
        print(f"🚨 RECENT ALERTS: {recent_alerts} (last hour)")
    else:
        print("✅ NO RECENT ALERTS")
    
    print(f"⏰ LAST SCAN: {summary['last_scan']}")
    print("="*80)

def print_detailed_status(monitor: NetworkMonitor):
    """Print detailed status for all hosts and services"""
    if not monitor.results:
        print("❌ No monitoring data available. Run a scan first.")
        return
    
    print("\n" + "="*100)
    print("📋 DETAILED NETWORK STATUS")
    print("="*100)
    
    for host, host_data in monitor.results["hosts"].items():
        print(f"\n🖥️  HOST: {host}")
        print("-" * 50)
        
        # Ping status
        ping_status = "✅ UP" if host_data["ping"]["status"] else "❌ DOWN"
        ping_time = host_data["ping"]["response_time"]
        print(f"   PING: {ping_status} ({ping_time:.1f}ms)")
        
        # Port status
        up_ports = []
        down_ports = []
        
        for port, port_data in host_data["ports"].items():
            if port_data["status"]:
                up_ports.append((port, port_data["service"], port_data["response_time"]))
            else:
                down_ports.append((port, port_data["service"]))
        
        if up_ports:
            print(f"   SERVICES UP ({len(up_ports)}):")
            for port, service, response_time in sorted(up_ports):
                print(f"      ✅ {service} ({port}) - {response_time:.1f}ms")
        
        if down_ports:
            print(f"   SERVICES DOWN ({len(down_ports)}):")
            for port, service in sorted(down_ports):
                print(f"      ❌ {service} ({port})")
        
        if not up_ports and not down_ports:
            print("   No port data available")

def run_single_scan(config_file: str):
    """Run a single network scan"""
    print("🔍 Starting single network scan...")
    monitor = NetworkMonitor(config_file)
    
    start_time = time.time()
    results = monitor.perform_full_scan()
    scan_time = time.time() - start_time
    
    print(f"✅ Scan completed in {scan_time:.2f} seconds")
    print_status_summary(monitor)
    
    return monitor

def run_continuous_monitoring(config_file: str):
    """Run continuous network monitoring"""
    print("🔄 Starting continuous network monitoring...")
    monitor = NetworkMonitor(config_file)
    
    # Perform initial scan
    monitor.perform_full_scan()
    print_status_summary(monitor)
    
    # Start continuous monitoring
    monitor.start_monitoring()
    
    try:
        print(f"🚀 Monitoring started. Checking every {monitor.config['check_interval']} seconds.")
        print("Press Ctrl+C to stop monitoring...")
        
        while True:
            time.sleep(5)  # Check every 5 seconds for updates
            
            # Print periodic status updates
            if int(time.time()) % 300 == 0:  # Every 5 minutes
                print_status_summary(monitor)
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping network monitoring...")
        monitor.stop_monitoring()
        print("✅ Monitoring stopped successfully")

def run_web_dashboard():
    """Launch the web dashboard"""
    print("🌐 Starting web dashboard...")
    try:
        import subprocess
        import sys
        
        # Try to run the dashboard
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
        subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])
        
    except ImportError:
        print("❌ Streamlit is not installed. Please install it with:")
        print("   pip install streamlit")
    except Exception as e:
        print(f"❌ Failed to start web dashboard: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Network Monitor - A comprehensive network monitoring tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --scan                     # Run a single scan
  python main.py --monitor                  # Start continuous monitoring
  python main.py --dashboard                # Launch web dashboard
  python main.py --scan --detailed         # Run scan with detailed output
  python main.py --config custom.json      # Use custom config file
        """
    )
    
    parser.add_argument("--config", "-c", 
                       default="config.json",
                       help="Configuration file path (default: config.json)")
    
    parser.add_argument("--scan", "-s", 
                       action="store_true",
                       help="Run a single network scan")
    
    parser.add_argument("--monitor", "-m", 
                       action="store_true",
                       help="Start continuous monitoring")
    
    parser.add_argument("--dashboard", "-d", 
                       action="store_true",
                       help="Launch web dashboard")
    
    parser.add_argument("--detailed", 
                       action="store_true",
                       help="Show detailed status output")
    
    parser.add_argument("--setup", 
                       action="store_true",
                       help="Create default configuration and directories")
    
    parser.add_argument("--version", "-v", 
                       action="version", 
                       version="Network Monitor v1.0.0")
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Setup directories
    create_directories()
    
    # Create default config if it doesn't exist
    if not os.path.exists(args.config):
        print(f"⚠️  Configuration file not found: {args.config}")
        create_default_config()
    
    # Setup command
    if args.setup:
        create_default_config()
        print("✅ Setup completed successfully!")
        return
    
    # Dashboard command
    if args.dashboard:
        run_web_dashboard()
        return
    
    # Default to scan if no specific command
    if not args.scan and not args.monitor:
        args.scan = True
    
    # Run scan
    if args.scan:
        monitor = run_single_scan(args.config)
        if args.detailed:
            print_detailed_status(monitor)
    
    # Run continuous monitoring
    if args.monitor:
        run_continuous_monitoring(args.config)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
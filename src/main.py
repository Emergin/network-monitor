#!/usr/bin/env python3
"""
Network Monitor - Main Entry Point
Professional network monitoring tool for tracking host and service availability
"""
import sys
import os
import argparse
import signal
from .monitor import NetworkMonitor

# Global monitor instance for signal handling
monitor_instance = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global monitor_instance
    print("\n\nReceived shutdown signal...")
    if monitor_instance:
        monitor_instance.stop_monitoring()
    sys.exit(0)


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                             NETWORK MONITOR                                  ║
║                    Professional Network Monitoring Tool                      ║
║                                                                              ║
║  Features:                                                                   ║
║  • Real-time host ping monitoring                                           ║
║  • TCP port connectivity testing                                            ║
║  • Configurable alerts (console & email)                                    ║
║  • Live dashboard with statistics                                           ║
║  • Comprehensive logging system                                             ║
║  • JSON-based configuration                                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import psutil
    except ImportError:
        missing_deps.append('psutil')
    
    try:
        import colorama
    except ImportError:
        missing_deps.append('colorama')
    
    try:
        import tabulate
    except ImportError:
        missing_deps.append('tabulate')
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nInstall them with: pip install -r requirements.txt")
        return False
    
    return True


def create_sample_config():
    """Create sample configuration file"""
    config_content = """{
  "monitoring": {
    "interval": 30,
    "timeout": 5,
    "max_retries": 3
  },
  "targets": {
    "hosts": [
      {
        "name": "localhost",
        "ip": "127.0.0.1",
        "enabled": true
      },
      {
        "name": "local-gateway",
        "ip": "192.168.1.1",
        "enabled": true
      }
    ],
    "services": [
      {
        "name": "HTTP Server",
        "host": "127.0.0.1",
        "port": 80,
        "enabled": true
      },
      {
        "name": "SSH Service",
        "host": "127.0.0.1",
        "port": 22,
        "enabled": true
      },
      {
        "name": "Development Server",
        "host": "127.0.0.1",
        "port": 3000,
        "enabled": false
      }
    ]
  },
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
  },
  "logging": {
    "level": "INFO",
    "file": "logs/network_monitor.log",
    "max_size_mb": 10,
    "backup_count": 5
  }
}"""
    
    try:
        with open("config.json", "w") as f:
            f.write(config_content)
        print("✅ Sample configuration created: config.json")
        print("   Edit this file to customize your monitoring targets")
        return True
    except Exception as e:
        print(f"❌ Error creating configuration: {e}")
        return False


def run_single_check(config_path):
    """Run a single monitoring check and exit"""
    try:
        monitor = NetworkMonitor(config_path)
        
        print("Running single monitoring check...")
        print("-" * 50)
        
        # Perform one check cycle
        monitor._perform_checks()
        
        # Display results
        status = monitor.get_current_status()
        
        print("\nHOST RESULTS:")
        for host_name, result in status['hosts'].items():
            status_str = "UP" if result.get('success') else "DOWN"
            response_time = f" ({result.get('response_time', 0):.1f}ms)" if result.get('success') else ""
            print(f"  {host_name} ({result.get('ip')}): {status_str}{response_time}")
        
        print("\nSERVICE RESULTS:")
        for service_name, result in status['services'].items():
            status_str = "RUNNING" if result.get('success') else "STOPPED"
            response_time = f" ({result.get('response_time', 0):.1f}ms)" if result.get('success') else ""
            print(f"  {service_name} ({result.get('host')}:{result.get('port')}): {status_str}{response_time}")
        
        print("\n" + "="*50)
        print("Single check completed successfully")
        
    except Exception as e:
        print(f"❌ Error during single check: {e}")
        sys.exit(1)


def main():
    """Main application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Network Monitor - Professional network monitoring tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                    # Start monitoring with default config
  python -m src.main -c custom.json     # Use custom configuration file
  python -m src.main --check            # Run single check and exit
  python -m src.main --create-config    # Create sample configuration
  python -m src.main --test-alerts      # Test alert system
        """
    )
    
    parser.add_argument('-c', '--config', 
                       default='config.json',
                       help='Configuration file path (default: config.json)')
    
    parser.add_argument('--check', 
                       action='store_true',
                       help='Run single check and exit')
    
    parser.add_argument('--create-config', 
                       action='store_true',
                       help='Create sample configuration file')
    
    parser.add_argument('--test-alerts', 
                       action='store_true',
                       help='Test alert system')
    
    parser.add_argument('--version', 
                       action='version', 
                       version='Network Monitor v1.0.0')
    
    parser.add_argument('--no-banner', 
                       action='store_true',
                       help='Skip banner display')
    
    args = parser.parse_args()
    
    # Display banner
    if not args.no_banner:
        print_banner()
    
    # Handle create-config command
    if args.create_config:
        create_sample_config()
        return
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if configuration file exists
    if not os.path.exists(args.config) and not args.create_config:
        print(f"❌ Configuration file '{args.config}' not found")
        print("   Create one with: python -m src.main --create-config")
        sys.exit(1)
    
    # Handle single check command
    if args.check:
        run_single_check(args.config)
        return
    
    # Setup signal handlers
    setup_signal_handlers()
    
    try:
        # Create monitor instance
        global monitor_instance
        monitor_instance = NetworkMonitor(args.config)
        
        # Handle test alerts command
        if args.test_alerts:
            print("Sending test alert...")
            monitor_instance.send_test_alert()
            print("✅ Test alert sent")
            return
        
        # Start monitoring
        print("🚀 Starting Network Monitor...")
        print("   Press Ctrl+C to stop monitoring\n")
        
        monitor_instance.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
        if monitor_instance:
            monitor_instance.stop_monitoring()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if monitor_instance:
            monitor_instance.stop_monitoring()
        sys.exit(1)


if __name__ == "__main__":
    main()
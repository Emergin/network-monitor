import socket
import subprocess
import threading
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import concurrent.futures
import platform

class NetworkMonitor:
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.monitoring_active = False
        self.results = {}
        self.alert_history = []
        self.setup_logging()
        
        # Common ports to monitor on laptops
        self.default_ports = {
            # Web services
            80: "HTTP",
            443: "HTTPS",
            8080: "HTTP Alt",
            8443: "HTTPS Alt",
            3000: "Development Server",
            3001: "React Dev",
            4200: "Angular Dev",
            5173: "Vite Dev",
            
            # Database services
            3306: "MySQL",
            5432: "PostgreSQL",
            27017: "MongoDB",
            6379: "Redis",
            1433: "SQL Server",
            1521: "Oracle",
            
            # Email services
            25: "SMTP",
            110: "POP3",
            143: "IMAP",
            465: "SMTP SSL",
            587: "SMTP TLS",
            993: "IMAP SSL",
            995: "POP3 SSL",
            
            # File sharing
            21: "FTP",
            22: "SSH/SFTP",
            23: "Telnet",
            69: "TFTP",
            135: "RPC",
            139: "NetBIOS",
            445: "SMB",
            548: "AFP",
            2049: "NFS",
            
            # Remote access
            3389: "RDP",
            5900: "VNC",
            5901: "VNC Alt",
            5902: "VNC Alt2",
            4899: "Radmin",
            
            # Development & APIs
            8000: "Python Dev",
            8001: "Python Alt",
            5000: "Flask Default",
            5001: "Flask Alt",
            9000: "Development",
            9001: "Development Alt",
            7000: "Development",
            6000: "Development",
            4000: "Development",
            
            # Gaming & Streaming
            25565: "Minecraft",
            7777: "Gaming",
            27015: "Steam",
            1935: "RTMP",
            
            # System services
            53: "DNS",
            67: "DHCP Server",
            68: "DHCP Client",
            161: "SNMP",
            162: "SNMP Trap",
            514: "Syslog",
            
            # Media & Entertainment
            8096: "Jellyfin",
            32400: "Plex",
            5050: "Couchpotato",
            8989: "Sonarr",
            7878: "Radarr",
            
            # Virtualization
            902: "VMware",
            903: "VMware SSL",
            8006: "Proxmox",
            
            # Chat & Communication
            6667: "IRC",
            5222: "XMPP",
            1863: "MSN",
            
            # Backup & Sync
            873: "Rsync",
            2222: "SSH Alt",
            
            # Printers
            631: "IPP",
            515: "LPR",
            9100: "HP JetDirect",
            
            # IoT & Smart Home
            1883: "MQTT",
            8883: "MQTT SSL",
            8123: "Home Assistant",
            
            # Container services
            2375: "Docker",
            2376: "Docker SSL",
            8080: "Jenkins",
            9090: "Prometheus",
            3000: "Grafana",
            
            # Security
            1194: "OpenVPN",
            500: "IPSec",
            4500: "IPSec NAT"
        }
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file or use defaults"""
        default_config = {
            "hosts": ["127.0.0.1", "8.8.8.8", "1.1.1.1"],
            "ports": list(self.default_ports.keys()) if hasattr(self, 'default_ports') else [],
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
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            # Handle different host formats (string or dict)
            if "hosts" in config:
                normalized_hosts = []
                for host in config["hosts"]:
                    if isinstance(host, dict):
                        # Extract address from dict format
                        if "address" in host and host.get("enabled", True):
                            normalized_hosts.append(host["address"])
                    elif isinstance(host, str):
                        # Use string directly
                        normalized_hosts.append(host)
                config["hosts"] = normalized_hosts
            
            return config
        except FileNotFoundError:
            return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/network_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ping_host(self, host: str) -> Tuple[str, bool, float]:
        """Ping a host and return status"""
        try:
            # Use different ping commands based on OS
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(self.config["ping_timeout"] * 1000), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(self.config["ping_timeout"]), host]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config["ping_timeout"] + 1)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            success = result.returncode == 0
            return host, success, response_time if success else 0
            
        except (subprocess.TimeoutExpired, Exception) as e:
            self.logger.warning(f"Ping failed for {host}: {e}")
            return host, False, 0
    
    def check_port(self, host: str, port: int) -> Tuple[str, int, bool, float]:
        """Check if a port is open on a host"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config["port_timeout"])
            
            result = sock.connect_ex((host, port))
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            sock.close()
            success = result == 0
            return host, port, success, response_time if success else 0
            
        except Exception as e:
            self.logger.warning(f"Port check failed for {host}:{port}: {e}")
            return host, port, False, 0
    
    def scan_host_ports(self, host: str, ports: List[int] = None) -> Dict:
        """Scan multiple ports on a single host"""
        if ports is None:
            ports = list(self.default_ports.keys())
        
        host_results = {
            "host": host,
            "timestamp": datetime.now().isoformat(),
            "ping": {"status": False, "response_time": 0},
            "ports": {}
        }
        
        # First ping the host
        _, ping_status, ping_time = self.ping_host(host)
        host_results["ping"] = {"status": ping_status, "response_time": ping_time}
        
        # Only check ports if host is reachable or if it's localhost
        if ping_status or host in ["127.0.0.1", "localhost"]:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
                port_futures = {executor.submit(self.check_port, host, port): port for port in ports}
                
                for future in concurrent.futures.as_completed(port_futures):
                    _, port, status, response_time = future.result()
                    service_name = self.default_ports.get(port, f"Port {port}")
                    host_results["ports"][port] = {
                        "status": status,
                        "response_time": response_time,
                        "service": service_name
                    }
        
        return host_results
    
    def perform_full_scan(self) -> Dict:
        """Perform a full network scan of all configured hosts and ports"""
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "hosts": {}
        }
        
        self.logger.info("Starting full network scan...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.config["hosts"])) as executor:
            host_futures = {
                executor.submit(self.scan_host_ports, host, self.config.get("ports", list(self.default_ports.keys()))): host 
                for host in self.config["hosts"]
            }
            
            for future in concurrent.futures.as_completed(host_futures):
                host_result = future.result()
                host = host_result["host"]
                scan_results["hosts"][host] = host_result
        
        self.results = scan_results
        self.check_alerts(scan_results)
        self.logger.info("Full network scan completed")
        
        return scan_results
    
    def check_alerts(self, scan_results: Dict):
        """Check for alert conditions and trigger notifications"""
        if not self.config["alerts"]["enabled"]:
            return
        
        current_time = datetime.now()
        alerts = []
        
        for host, host_data in scan_results["hosts"].items():
            # Check ping alerts
            if not host_data["ping"]["status"]:
                alerts.append({
                    "type": "ping_down",
                    "host": host,
                    "message": f"Host {host} is not responding to ping",
                    "timestamp": current_time.isoformat()
                })
            
            # Check port alerts
            for port, port_data in host_data["ports"].items():
                if not port_data["status"]:
                    service_name = port_data["service"]
                    alerts.append({
                        "type": "port_down",
                        "host": host,
                        "port": port,
                        "service": service_name,
                        "message": f"Service {service_name} on {host}:{port} is down",
                        "timestamp": current_time.isoformat()
                    })
        
        # Process alerts
        for alert in alerts:
            self.process_alert(alert)
            self.alert_history.append(alert)
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = current_time - timedelta(hours=24)
        self.alert_history = [
            alert for alert in self.alert_history 
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]
    
    def process_alert(self, alert: Dict):
        """Process and send an alert"""
        self.logger.warning(f"ALERT: {alert['message']}")
        
        # Console alert (always enabled)
        print(f"🚨 ALERT [{alert['timestamp']}]: {alert['message']}")
        
        # Additional alert methods can be implemented here
        # Email, Slack, Discord, etc.
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring_active = True
        self.logger.info("Network monitoring started")
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    self.perform_full_scan()
                    time.sleep(self.config["check_interval"])
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(10)  # Wait 10 seconds before retrying
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        self.logger.info("Network monitoring stopped")
    
    def get_status_summary(self) -> Dict:
        """Get a summary of current network status"""
        if not self.results:
            return {"status": "No data available"}
        
        summary = {
            "last_scan": self.results.get("timestamp"),
            "total_hosts": len(self.results.get("hosts", {})),
            "hosts_up": 0,
            "hosts_down": 0,
            "total_services": 0,
            "services_up": 0,
            "services_down": 0,
            "recent_alerts": len([
                alert for alert in self.alert_history 
                if datetime.fromisoformat(alert["timestamp"]) > datetime.now() - timedelta(hours=1)
            ])
        }
        
        for host_data in self.results.get("hosts", {}).values():
            if host_data["ping"]["status"]:
                summary["hosts_up"] += 1
            else:
                summary["hosts_down"] += 1
            
            for port_data in host_data["ports"].values():
                summary["total_services"] += 1
                if port_data["status"]:
                    summary["services_up"] += 1
                else:
                    summary["services_down"] += 1
        
        return summary
    
    def get_host_details(self, host: str) -> Optional[Dict]:
        """Get detailed information for a specific host"""
        if not self.results or host not in self.results.get("hosts", {}):
            return None
        
        return self.results["hosts"][host]
    
    def get_service_status(self, service_name: str = None, port: int = None) -> List[Dict]:
        """Get status of specific service across all hosts"""
        if not self.results:
            return []
        
        service_status = []
        
        for host, host_data in self.results["hosts"].items():
            for port_num, port_data in host_data["ports"].items():
                if (service_name and service_name.lower() in port_data["service"].lower()) or \
                   (port and port == port_num):
                    service_status.append({
                        "host": host,
                        "port": port_num,
                        "service": port_data["service"],
                        "status": port_data["status"],
                        "response_time": port_data["response_time"]
                    })
        
        return service_status
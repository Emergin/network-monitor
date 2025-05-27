"""
Port Checker Module
Handles TCP port connectivity testing to verify services are running
"""
import socket
import time
import threading
from typing import Tuple, Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


class PortChecker:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
    
    def check_port(self, host: str, port: int) -> Tuple[bool, Optional[float]]:
        """
        Check if a specific port is open on a host
        
        Args:
            host: IP address or hostname
            port: Port number to check
            
        Returns:
            Tuple of (is_open: bool, response_time: float in ms)
        """
        try:
            start_time = time.time()
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Attempt connection
            result = sock.connect_ex((host, port))
            end_time = time.time()
            
            # Close socket
            sock.close()
            
            # Calculate response time
            response_time = (end_time - start_time) * 1000
            
            # Check if connection was successful
            is_open = result == 0
            
            return is_open, response_time if is_open else None
            
        except socket.gaierror:
            # DNS resolution failed
            return False, None
        except Exception as e:
            return False, None
    
    def check_port_with_banner(self, host: str, port: int) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Check port and attempt to grab service banner
        
        Args:
            host: IP address or hostname
            port: Port number to check
            
        Returns:
            Tuple of (is_open: bool, response_time: float, banner: str)
        """
        try:
            start_time = time.time()
            
            # Create socket with timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect to port
            result = sock.connect_ex((host, port))
            
            if result == 0:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                # Try to grab banner for common services
                banner = self._grab_banner(sock, port)
                sock.close()
                
                return True, response_time, banner
            else:
                sock.close()
                return False, None, None
                
        except Exception:
            return False, None, None
    
    def _grab_banner(self, sock: socket.socket, port: int) -> Optional[str]:
        """
        Attempt to grab service banner from socket
        
        Args:
            sock: Connected socket
            port: Port number (used to determine service type)
            
        Returns:
            Service banner string or None
        """
        try:
            # Set a short timeout for banner grabbing
            sock.settimeout(2)
            
            # Send appropriate request based on port
            if port == 80:
                sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
            elif port == 25:  # SMTP
                pass  # SMTP sends banner automatically
            elif port == 21:  # FTP
                pass  # FTP sends banner automatically
            elif port == 22:  # SSH
                pass  # SSH sends banner automatically
            
            # Try to receive banner
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner[:200] if banner else None  # Limit banner length
            
        except:
            return None
    
    def check_multiple_ports(self, services: List[Dict[str, Any]], max_workers: int = 10) -> Dict[str, Any]:
        """
        Check multiple services concurrently
        
        Args:
            services: List of service dictionaries with 'name', 'host', 'port' keys
            max_workers: Maximum number of concurrent checks
            
        Returns:
            Dictionary with service check results
        """
        results = {}
        
        # Use ThreadPoolExecutor for concurrent port checks
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all port check tasks
            future_to_service = {
                executor.submit(self.check_port, service['host'], service['port']): service
                for service in services
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_service):
                service = future_to_service[future]
                service_name = service.get('name', f"{service['host']}:{service['port']}")
                
                try:
                    is_open, response_time = future.result()
                    results[service_name] = {
                        'success': is_open,
                        'response_time': response_time,
                        'host': service['host'],
                        'port': service['port'],
                        'timestamp': time.time()
                    }
                except Exception as e:
                    results[service_name] = {
                        'success': False,
                        'response_time': None,
                        'host': service['host'],
                        'port': service['port'],
                        'error': str(e),
                        'timestamp': time.time()
                    }
        
        return results
    
    def scan_port_range(self, host: str, start_port: int, end_port: int, max_workers: int = 50) -> List[int]:
        """
        Scan a range of ports on a host
        
        Args:
            host: IP address or hostname
            start_port: Starting port number
            end_port: Ending port number
            max_workers: Maximum concurrent scans
            
        Returns:
            List of open port numbers
        """
        open_ports = []
        ports_to_scan = range(start_port, end_port + 1)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all port scans
            future_to_port = {
                executor.submit(self.check_port, host, port): port
                for port in ports_to_scan
            }
            
            # Collect results
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    is_open, _ = future.result()
                    if is_open:
                        open_ports.append(port)
                except Exception:
                    pass  # Skip failed checks
        
        return sorted(open_ports)
    
    def is_service_running(self, host: str, port: int, retries: int = 3) -> bool:
        """
        Check if a service is running with retry logic
        
        Args:
            host: IP address or hostname
            port: Port number
            retries: Number of retry attempts
            
        Returns:
            True if service is running, False otherwise
        """
        for attempt in range(retries):
            is_open, _ = self.check_port(host, port)
            if is_open:
                return True
            
            if attempt < retries - 1:  # Don't sleep on last attempt
                time.sleep(1)
        
        return False
    
    def get_service_info(self, host: str, port: int) -> Dict[str, Any]:
        """
        Get detailed information about a service
        
        Args:
            host: IP address or hostname
            port: Port number
            
        Returns:
            Dictionary with service information
        """
        is_open, response_time, banner = self.check_port_with_banner(host, port)
        
        # Common service identification
        service_name = self._identify_service(port, banner)
        
        return {
            'host': host,
            'port': port,
            'is_open': is_open,
            'response_time': response_time,
            'service': service_name,
            'banner': banner,
            'timestamp': time.time()
        }
    
    def _identify_service(self, port: int, banner: Optional[str] = None) -> str:
        """
        Identify service type based on port and banner
        
        Args:
            port: Port number
            banner: Service banner (if available)
            
        Returns:
            Service name string
        """
        # Common port to service mapping
        common_services = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            3000: "Development Server",
            3306: "MySQL",
            5432: "PostgreSQL",
            6379: "Redis",
            27017: "MongoDB"
        }
        
        service = common_services.get(port, f"Unknown Service")
        
        # Refine based on banner if available
        if banner:
            banner_lower = banner.lower()
            if "http" in banner_lower:
                service = "HTTP Server"
            elif "ssh" in banner_lower:
                service = "SSH Server"
            elif "ftp" in banner_lower:
                service = "FTP Server"
            elif "mysql" in banner_lower:
                service = "MySQL Database"
            elif "postgresql" in banner_lower or "postgres" in banner_lower:
                service = "PostgreSQL Database"
        
        return service
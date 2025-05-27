"""
Ping Checker Module
Handles ICMP ping functionality to test host reachability
"""
import subprocess
import platform
import re
import time
from typing import Tuple, Optional


class PingChecker:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.system = platform.system().lower()
        
    def ping_host(self, host: str, count: int = 1) -> Tuple[bool, Optional[float]]:
        """
        Ping a host and return success status and response time
        
        Args:
            host: IP address or hostname to ping
            count: Number of ping packets to send
            
        Returns:
            Tuple of (success: bool, response_time: float in ms)
        """
        try:
            # Build ping command based on operating system
            if self.system == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(self.timeout * 1000), host]
            else:  # Linux/Unix/macOS
                cmd = ["ping", "-c", str(count), "-W", str(self.timeout), host]
            
            # Execute ping command
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 5  # Add buffer to subprocess timeout
            )
            end_time = time.time()
            
            # Check if ping was successful
            if result.returncode == 0:
                response_time = self._extract_response_time(result.stdout)
                if response_time is None:
                    # If we can't parse response time, calculate it manually
                    response_time = (end_time - start_time) * 1000
                return True, response_time
            else:
                return False, None
                
        except subprocess.TimeoutExpired:
            return False, None
        except Exception as e:
            print(f"Error pinging {host}: {e}")
            return False, None
    
    def _extract_response_time(self, ping_output: str) -> Optional[float]:
        """
        Extract response time from ping output
        
        Args:
            ping_output: Raw output from ping command
            
        Returns:
            Response time in milliseconds or None if not found
        """
        try:
            if self.system == "windows":
                # Windows ping output format: "time=XXXms" or "time<1ms"
                time_match = re.search(r'time[<=](\d+(?:\.\d+)?)ms', ping_output)
                if time_match:
                    return float(time_match.group(1))
                
                # Handle "time<1ms" case
                if "time<1ms" in ping_output:
                    return 0.5
                    
            else:  # Linux/Unix/macOS
                # Unix ping output format: "time=XXX ms" or "time=XXX.XXX ms"
                time_match = re.search(r'time=(\d+(?:\.\d+)?)\s*ms', ping_output)
                if time_match:
                    return float(time_match.group(1))
            
            return None
            
        except Exception:
            return None
    
    def ping_multiple_hosts(self, hosts: list) -> dict:
        """
        Ping multiple hosts and return results
        
        Args:
            hosts: List of host dictionaries with 'name' and 'ip' keys
            
        Returns:
            Dictionary with host results
        """
        results = {}
        
        for host_info in hosts:
            host_name = host_info.get('name', host_info.get('ip'))
            host_ip = host_info.get('ip')
            
            if not host_ip:
                results[host_name] = {'success': False, 'response_time': None, 'error': 'No IP specified'}
                continue
            
            success, response_time = self.ping_host(host_ip)
            results[host_name] = {
                'success': success,
                'response_time': response_time,
                'ip': host_ip,
                'timestamp': time.time()
            }
        
        return results
    
    def is_host_reachable(self, host: str, retries: int = 3) -> bool:
        """
        Check if host is reachable with retry logic
        
        Args:
            host: IP address or hostname
            retries: Number of retry attempts
            
        Returns:
            True if host is reachable, False otherwise
        """
        for attempt in range(retries):
            success, _ = self.ping_host(host)
            if success:
                return True
            
            if attempt < retries - 1:  # Don't sleep on last attempt
                time.sleep(1)
        
        return False
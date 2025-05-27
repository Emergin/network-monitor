import asyncio
import subprocess
import platform
import socket
import time
from typing import Dict, List, Optional, Tuple
from ping3 import ping
from config_manager import ConfigManager
from logger import NetworkLogger

class PingChecker:
    def __init__(self, config_manager: ConfigManager, logger: NetworkLogger):
        self.config = config_manager
        self.logger = logger
        self.system = platform.system().lower()
        self.ping_results = {}
        
    async def ping_host(self, host: str, timeout: int = 5) -> Tuple[bool, Optional[float]]:
        """
        Ping a single host and return success status and response time
        """
        try:
            # Try ping3 first (more reliable)
            response_time = ping(host, timeout=timeout, unit='ms')
            
            if response_time is not None:
                self.logger.log_ping_result(host, True, response_time)
                return True, response_time
            else:
                # Fallback to subprocess ping
                return await self._subprocess_ping(host, timeout)
                
        except Exception as e:
            self.logger.get_logger('ping').error(f"Error pinging {host}: {str(e)}")
            return False, None
    
    async def _subprocess_ping(self, host: str, timeout: int) -> Tuple[bool, Optional[float]]:
        """
        Fallback ping using subprocess
        """
        try:
            if self.system == 'windows':
                cmd = ['ping', '-n', '1', '-w', str(timeout * 1000), host]
            else:
                cmd = ['ping', '-c', '1', '-W', str(timeout), host]
            
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout + 1
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if process.returncode == 0:
                self.logger.log_ping_result(host, True, response_time)
                return True, response_time
            else:
                self.logger.log_ping_result(host, False)
                return False, None
                
        except asyncio.TimeoutError:
            self.logger.log_ping_result(host, False)
            return False, None
        except Exception as e:
            self.logger.get_logger('ping').error(f"Subprocess ping error for {host}: {str(e)}")
            return False, None
    
    async def ping_multiple_hosts(self, hosts: List[Dict]) -> Dict[str, Dict]:
        """
        Ping multiple hosts concurrently
        """
        timeout = self.config.get('monitoring.timeout', 5)
        tasks = []
        host_info = {}
        
        for host in hosts:
            if host.get('enabled', True):
                host_name = host.get('name', host.get('address'))
                host_address = host.get('address')
                
                task = asyncio.create_task(
                    self.ping_host(host_address, timeout),
                    name=host_name
                )
                tasks.append(task)
                host_info[host_name] = {
                    'address': host_address,
                    'task': task
                }
        
        # Wait for all pings to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        ping_results = {}
        for i, (host_name, info) in enumerate(host_info.items()):
            if i < len(results):
                result = results[i]
                if isinstance(result, Exception):
                    ping_results[host_name] = {
                        'address': info['address'],
                        'success': False,
                        'response_time': None,
                        'error': str(result),
                        'timestamp': time.time()
                    }
                else:
                    success, response_time = result
                    ping_results[host_name] = {
                        'address': info['address'],
                        'success': success,
                        'response_time': response_time,
                        'error': None,
                        'timestamp': time.time()
                    }
        
        self.ping_results = ping_results
        return ping_results
    
    def get_ping_statistics(self) -> Dict:
        """
        Get ping statistics
        """
        if not self.ping_results:
            return {}
        
        total_hosts = len(self.ping_results)
        successful_pings = sum(1 for result in self.ping_results.values() if result['success'])
        failed_pings = total_hosts - successful_pings
        
        response_times = [
            result['response_time'] for result in self.ping_results.values() 
            if result['success'] and result['response_time'] is not None
        ]
        
        stats = {
            'total_hosts': total_hosts,
            'successful_pings': successful_pings,
            'failed_pings': failed_pings,
            'success_rate': (successful_pings / total_hosts * 100) if total_hosts > 0 else 0,
            'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0
        }
        
        return stats
    
    def get_failed_hosts(self) -> List[str]:
        """
        Get list of hosts that failed ping
        """
        return [
            host_name for host_name, result in self.ping_results.items()
            if not result['success']
        ]
    
    async def continuous_ping_check(self, interval: int = 30):
        """
        Continuously ping hosts at specified interval
        """
        self.logger.log_system_info(f"Starting continuous ping monitoring (interval: {interval}s)")
        
        while True:
            try:
                hosts = self.config.get_enabled_hosts()
                await self.ping_multiple_hosts(hosts)
                
                # Log summary
                stats = self.get_ping_statistics()
                self.logger.get_logger('ping').info(
                    f"Ping check completed - Success rate: {stats.get('success_rate', 0):.1f}% "
                    f"({stats.get('successful_pings', 0)}/{stats.get('total_hosts', 0)})"
                )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.log_error('ping', e)
                await asyncio.sleep(interval)
    
    def resolve_hostname(self, hostname: str) -> Optional[str]:
        """
        Resolve hostname to IP address
        """
        try:
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except socket.gaierror:
            return None
    
    def is_valid_ip(self, ip: str) -> bool:
        """
        Check if string is a valid IP address
        """
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False    
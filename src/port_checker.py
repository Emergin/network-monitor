import asyncio
import socket
import time
from typing import Dict, List, Optional, Tuple
from config_manager import ConfigManager
from logger import NetworkLogger

class PortChecker:
    def __init__(self, config_manager: ConfigManager, logger: NetworkLogger):
        self.config = config_manager
        self.logger = logger
        self.port_results = {}
        
    async def check_tcp_port(self, host: str, port: int, timeout: int = 5) -> Tuple[bool, Optional[float]]:
        """
        Check if a TCP port is open on a host
        """
        try:
            start_time = time.time()
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # Try to connect
            future = asyncio.get_event_loop().run_in_executor(
                None, sock.connect, (host, port)
            )
            
            await asyncio.wait_for(future, timeout=timeout)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            sock.close()
            self.logger.log_port_result(host, port, True, response_time)
            return True, response_time
            
        except (socket.timeout, asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            if 'sock' in locals():
                sock.close()
            self.logger.log_port_result(host, port, False)
            return False, None
        except Exception as e:
            if 'sock' in locals():
                sock.close()
            self.logger.get_logger('port').error(f"Error checking TCP port {port} on {host}: {str(e)}")
            return False, None
    
    async def check_udp_port(self, host: str, port: int, timeout: int = 5) -> Tuple[bool, Optional[float]]:
        """
        Check if a UDP port is responding on a host
        Note: UDP is connectionless, so this sends a packet and waits for any response
        """
        try:
            start_time = time.time()
            
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # Send a test packet
            test_data = b"test"
            future = asyncio.get_event_loop().run_in_executor(
                None, sock.sendto, test_data, (host, port)
            )
            
            await asyncio.wait_for(future, timeout=timeout)
            
            # Try to receive response (this may timeout, which is normal for UDP)
            try:
                recv_future = asyncio.get_event_loop().run_in_executor(
                    None, sock.recv, 1024
                )
                await asyncio.wait_for(recv_future, timeout=1)  # Short timeout for UDP
                response_time = (time.time() - start_time) * 1000
                sock.close()
                self.logger.log_port_result(host, port, True, response_time)
                return True, response_time
            except asyncio.TimeoutError:
                # No response doesn't necessarily mean the port is closed for UDP
                response_time = (time.time() - start_time) * 1000
                sock.close()
                self.logger.log_port_result(host, port, True, response_time)
                return True, response_time
                
        except Exception as e:
            if 'sock' in locals():
                sock.close()
            self.logger.log_port_result(host, port, False)
            return False, None
    
    async def check_port(self, host: str, port_info: Dict, timeout: int = 5) -> Tuple[bool, Optional[float]]:
        """
        Check a port (TCP or UDP) on a host
        """
        port = port_info.get('port')
        protocol = port_info.get('protocol', 'tcp').lower()
        
        if protocol == 'tcp':
            return await self.check_tcp_port(host, port, timeout)
        elif protocol == 'udp':
            return await self.check_udp_port(host, port, timeout)
        else:
            self.logger.get_logger('port').warning(f"Unknown protocol {protocol} for port {port}")
            return False, None
    
    async def check_multiple_ports(self, host: str, ports: List[Dict]) -> Dict[int, Dict]:
        """
        Check multiple ports on a single host concurrently
        """
        timeout = self.config.get('monitoring.timeout', 5)
        tasks = []
        port_info = {}
        
        for port_config in ports:
            port = port_config.get('port')
            task = asyncio.create_task(
                self.check_port(host, port_config, timeout),
                name=f"{host}:{port}"
            )
            tasks.append(task)
            port_info[port] = {
                'config': port_config,
                'task': task
            }
        
        # Wait for all port checks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        port_results = {}
        for i, (port, info) in enumerate(port_info.items()):
            if i < len(results):
                result = results[i]
                if isinstance(result, Exception):
                    port_results[port] = {
                        'port': port,
                        'name': info['config'].get('name', f'Port {port}'),
                        'protocol': info['config'].get('protocol', 'tcp'),
                        'success': False,
                        'response_time': None,
                        'error': str(result),
                        'timestamp': time.time()
                    }
                else:
                    success, response_time = result
                    port_results[port] = {
                        'port': port,
                        'name': info['config'].get('name', f'Port {port}'),
                        'protocol': info['config'].get('protocol', 'tcp'),
                        'success': success,
                        'response_time': response_time,
                        'error': None,
                        'timestamp': time.time()
                    }
        
        return port_results
    
    async def check_all_hosts_ports(self, hosts: List[Dict], ports: List[Dict]) -> Dict[str, Dict]:
        """
        Check all ports on all hosts
        """
        all_results = {}
        
        for host in hosts:
            if not host.get('enabled', True):
                continue
                
            host_name = host.get('name', host.get('address'))
            host_address = host.get('address')
            
            try:
                port_results = await self.check_multiple_ports(host_address, ports)
                all_results[host_name] = {
                    'address': host_address,
                    'ports': port_results,
                    'timestamp': time.time()
                }
            except Exception as e:
                self.logger.log_error('port', e)
                all_results[host_name] = {
                    'address': host_address,
                    'ports': {},
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        self.port_results = all_results
        return all_results
    
    def get_port_statistics(self) -> Dict:
        """
        Get port check statistics
        """
        if not self.port_results:
            return {}
        
        total_checks = 0
        successful_checks = 0
        response_times = []
        
        for host_result in self.port_results.values():
            for port_result in host_result.get('ports', {}).values():
                total_checks += 1
                if port_result['success']:
                    successful_checks += 1
                    if port_result['response_time'] is not None:
                        response_times.append(port_result['response_time'])
        
        stats = {
            'total_checks': total_checks,
            'successful_checks': successful_checks,
            'failed_checks': total_checks - successful_checks,
            'success_rate': (successful_checks / total_checks * 100) if total_checks > 0 else 0,
            'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0
        }
        
        return stats
    
    def get_failed_ports(self) -> List[Dict]:
        """
        Get list of failed port checks
        """
        failed_ports = []
        
        for host_name, host_result in self.port_results.items():
            for port_result in host_result.get('ports', {}).values():
                if not port_result['success']:
                    failed_ports.append({
                        'host': host_name,
                        'address': host_result['address'],
                        'port': port_result['port'],
                        'name': port_result['name'],
                        'protocol': port_result['protocol']
                    })
        
        return failed_ports
    
    def get_open_ports(self, host: str) -> List[int]:
        """
        Get list of open ports for a specific host
        """
        if host not in self.port_results:
            return []
        
        return [
            port_result['port'] for port_result in self.port_results[host].get('ports', {}).values()
            if port_result['success']
        ]
    
    async def continuous_port_check(self, interval: int = 60):
        """
        Continuously check ports at specified interval
        """
        self.logger.log_system_info(f"Starting continuous port monitoring (interval: {interval}s)")
        
        while True:
            try:
                hosts = self.config.get_enabled_hosts()
                ports = self.config.get_ports()
                
                await self.check_all_hosts_ports(hosts, ports)
                
                # Log summary
                stats = self.get_port_statistics()
                self.logger.get_logger('port').info(
                    f"Port check completed - Success rate: {stats.get('success_rate', 0):.1f}% "
                    f"({stats.get('successful_checks', 0)}/{stats.get('total_checks', 0)})"
                )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.log_error('port', e)
                await asyncio.sleep(interval)
    
    async def scan_host_ports(self, host: str, port_range: Tuple[int, int] = (1, 1024)) -> Dict[int, bool]:
        """
        Scan a range of ports on a host to find open ports
        """
        start_port, end_port = port_range
        results = {}
        
        self.logger.get_logger('port').info(f"Scanning ports {start_port}-{end_port} on {host}")
        
        # Create tasks for port scanning
        tasks = []
        for port in range(start_port, end_port + 1):
            port_config = {'port': port, 'protocol': 'tcp'}
            task = asyncio.create_task(
                self.check_port(host, port_config, 1),  # Short timeout for scanning
                name=f"scan_{host}:{port}"
            )
            tasks.append((port, task))
        
        # Process results in batches to avoid overwhelming the system
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*[task for _, task in batch], return_exceptions=True)
            
            for j, result in enumerate(batch_results):
                port = batch[j][0]
                if isinstance(result, Exception):
                    results[port] = False
                else:
                    success, _ = result
                    results[port] = success
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        open_ports = [port for port, is_open in results.items() if is_open]
        self.logger.get_logger('port').info(f"Port scan complete - Found {len(open_ports)} open ports on {host}")
        
        return results
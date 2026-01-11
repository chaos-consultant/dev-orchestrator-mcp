"""Health monitoring system for MCP servers."""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result."""
    plugin_id: str
    status: HealthStatus
    response_time_ms: Optional[float]
    error_message: Optional[str]
    tools_count: Optional[int]
    last_checked: float

    def to_dict(self) -> Dict:
        return {
            'plugin_id': self.plugin_id,
            'status': self.status.value,
            'response_time_ms': self.response_time_ms,
            'error_message': self.error_message,
            'tools_count': self.tools_count,
            'last_checked': self.last_checked,
        }


class PluginHealthMonitor:
    """Monitors health of installed MCP servers."""

    def __init__(self):
        self.health_cache: Dict[str, HealthCheck] = {}
        self.cache_ttl = 60  # Cache health checks for 60 seconds

    async def check_plugin_health(self, plugin_info: Dict) -> HealthCheck:
        """Check health of a single plugin.

        Args:
            plugin_info: Plugin information dict from detector

        Returns:
            HealthCheck result
        """
        plugin_id = plugin_info['id']

        # Check cache first
        if plugin_id in self.health_cache:
            cached = self.health_cache[plugin_id]
            if time.time() - cached.last_checked < self.cache_ttl:
                return cached

        # Perform health check
        start_time = time.time()

        try:
            # Strategy 1: Check if plugin has a health endpoint
            if 'install_path' in plugin_info:
                health = await self._check_mcp_server_health(plugin_info)
            else:
                health = HealthCheck(
                    plugin_id=plugin_id,
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=None,
                    error_message="No install path found",
                    tools_count=None,
                    last_checked=time.time(),
                )

            # Cache result
            self.health_cache[plugin_id] = health
            return health

        except Exception as e:
            health = HealthCheck(
                plugin_id=plugin_id,
                status=HealthStatus.DOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
                tools_count=None,
                last_checked=time.time(),
            )
            self.health_cache[plugin_id] = health
            return health

    async def _check_mcp_server_health(self, plugin_info: Dict) -> HealthCheck:
        """Check MCP server health by attempting to list tools.

        This executes the MCP server and sends a list_tools request.
        """
        plugin_id = plugin_info['id']
        start_time = time.time()

        try:
            # Check if plugin has explicit command and args (from system configs like Claude Desktop)
            if 'command' in plugin_info and 'args' in plugin_info:
                command = plugin_info['command']
                args = plugin_info['args']
                env = plugin_info.get('env', {})

                # Merge env with current environment
                full_env = {**os.environ, **env}

                # Run the MCP server with its configured command
                process = await asyncio.create_subprocess_exec(
                    command,
                    *args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=full_env
                )
            else:
                # Fall back to detecting runtime from install_path
                install_path = Path(plugin_info['install_path'])
                runtime = plugin_info.get('runtime', 'python')

                if runtime == 'python':
                    # Python MCP server
                    server_file = self._find_server_file(install_path, ['server.py', 'main.py', '__main__.py'])
                    if not server_file:
                        raise FileNotFoundError("No Python server file found")

                    # Run server with test request
                    process = await asyncio.create_subprocess_exec(
                        'python3', str(server_file),
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=str(install_path)
                    )

                elif runtime == 'node':
                    # Node.js MCP server
                    package_json = install_path / "package.json"
                    if not package_json.exists():
                        raise FileNotFoundError("No package.json found")

                    # Run via npm or node
                    process = await asyncio.create_subprocess_exec(
                        'npm', 'start',
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=str(install_path)
                    )
                else:
                    raise ValueError(f"Unknown runtime: {runtime}")

            # Send list_tools request via stdio
            list_tools_request = json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }) + "\n"

            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(list_tools_request.encode()),
                    timeout=5.0
                )

                response_time = (time.time() - start_time) * 1000

                # Parse response
                if stdout:
                    try:
                        response = json.loads(stdout.decode())
                        if 'result' in response and 'tools' in response['result']:
                            tools_count = len(response['result']['tools'])
                            return HealthCheck(
                                plugin_id=plugin_id,
                                status=HealthStatus.HEALTHY,
                                response_time_ms=response_time,
                                error_message=None,
                                tools_count=tools_count,
                                last_checked=time.time(),
                            )
                    except json.JSONDecodeError:
                        pass

                # Server responded but didn't return valid tools
                return HealthCheck(
                    plugin_id=plugin_id,
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    error_message="Server responded but no tools found",
                    tools_count=0,
                    last_checked=time.time(),
                )

            except asyncio.TimeoutError:
                process.kill()
                return HealthCheck(
                    plugin_id=plugin_id,
                    status=HealthStatus.DOWN,
                    response_time_ms=(time.time() - start_time) * 1000,
                    error_message="Server timeout (>5s)",
                    tools_count=None,
                    last_checked=time.time(),
                )

        except FileNotFoundError as e:
            return HealthCheck(
                plugin_id=plugin_id,
                status=HealthStatus.DOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=f"Server file not found: {e}",
                tools_count=None,
                last_checked=time.time(),
            )
        except Exception as e:
            return HealthCheck(
                plugin_id=plugin_id,
                status=HealthStatus.DOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
                tools_count=None,
                last_checked=time.time(),
            )

    def _find_server_file(self, base_path: Path, candidates: List[str]) -> Optional[Path]:
        """Find server entry point file."""
        for candidate in candidates:
            server_file = base_path / candidate
            if server_file.exists():
                return server_file

        # Check in src/ subdirectory
        src_path = base_path / "src"
        if src_path.exists():
            for candidate in candidates:
                server_file = src_path / candidate
                if server_file.exists():
                    return server_file

        return None

    async def check_all_plugins_health(self, plugins: List[Dict]) -> List[HealthCheck]:
        """Check health of all plugins concurrently.

        Args:
            plugins: List of plugin info dicts from detector

        Returns:
            List of HealthCheck results
        """
        tasks = [self.check_plugin_health(plugin) for plugin in plugins]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def get_cached_health(self, plugin_id: str) -> Optional[HealthCheck]:
        """Get cached health status if available and not stale."""
        if plugin_id not in self.health_cache:
            return None

        cached = self.health_cache[plugin_id]
        if time.time() - cached.last_checked > self.cache_ttl:
            return None

        return cached

    def clear_cache(self, plugin_id: Optional[str] = None):
        """Clear health check cache."""
        if plugin_id:
            self.health_cache.pop(plugin_id, None)
        else:
            self.health_cache.clear()

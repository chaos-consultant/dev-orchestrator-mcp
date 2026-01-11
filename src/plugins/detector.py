"""Plugin detection system to identify already-installed MCP servers."""

import json
import platform
from pathlib import Path
from typing import Dict, List, Optional


class PluginDetector:
    """Detects installed MCP servers across various locations."""

    def __init__(self):
        self.home = Path.home()
        self.dev_orchestrator_dir = self.home / ".dev-orchestrator"
        self.plugins_dir = self.dev_orchestrator_dir / "plugins"
        self.config_locations = self._get_config_locations()

    def _get_config_locations(self) -> List[Path]:
        """Get platform-specific MCP config file locations."""
        locations = []
        system = platform.system()

        if system == "Darwin":  # macOS
            locations.extend([
                self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
                self.home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "mcp.json",
                self.home / ".config" / "claude" / "claude_desktop_config.json",
                self.home / ".config" / "cursor" / "mcp.json",
            ])
        elif system == "Windows":  # Windows
            appdata = Path.home() / "AppData"
            locations.extend([
                appdata / "Roaming" / "Claude" / "claude_desktop_config.json",
                appdata / "Roaming" / "Cursor" / "User" / "globalStorage" / "mcp.json",
            ])
        else:  # Linux and others
            locations.extend([
                self.home / ".config" / "claude" / "claude_desktop_config.json",
                self.home / ".config" / "Claude" / "claude_desktop_config.json",
                self.home / ".config" / "cursor" / "mcp.json",
                self.home / ".config" / "Cursor" / "mcp.json",
            ])

        # Generic MCP config location (all platforms)
        locations.append(self.home / ".config" / "mcp" / "config.json")

        return locations

    async def detect_installed_plugins(self) -> List[Dict]:
        """Detect all installed MCP servers.

        Returns:
            List of dicts with plugin info including:
            - id: plugin identifier
            - name: plugin name
            - install_path: where it's installed
            - source: 'dev-orchestrator' | 'system' | 'user'
            - config_file: config file path if found
            - git_url: git origin if available
        """
        installed = []

        # 1. Check dev-orchestrator plugins directory
        dev_orch_plugins = await self._scan_dev_orchestrator_plugins()
        installed.extend(dev_orch_plugins)

        # 2. Check system/user MCP configurations
        system_plugins = await self._scan_system_mcp_configs()
        installed.extend(system_plugins)

        return installed

    async def _scan_dev_orchestrator_plugins(self) -> List[Dict]:
        """Scan ~/.dev-orchestrator/plugins/ directory."""
        plugins = []

        if not self.plugins_dir.exists():
            return plugins

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('.'):
                continue

            plugin_info = await self._analyze_plugin_directory(plugin_dir, source='dev-orchestrator')
            if plugin_info:
                plugins.append(plugin_info)

        return plugins

    async def _scan_system_mcp_configs(self) -> List[Dict]:
        """Scan system MCP configuration files."""
        plugins = []

        for config_path in self.config_locations:
            if not config_path.exists():
                continue

            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Parse MCP config structure
                mcp_servers = config.get('mcpServers', {})
                for server_name, server_config in mcp_servers.items():
                    command = server_config.get('command', '')
                    args = server_config.get('args', [])

                    # Determine install path from command and args
                    install_path = command
                    if args:
                        # If using npx, the package name is usually after -y flag
                        if command == 'npx' and len(args) > 0:
                            # Find the package name (skip flags like -y)
                            for arg in args:
                                if not arg.startswith('-'):
                                    install_path = f"npx {arg}"
                                    break
                        # If using node, the script path is the first arg
                        elif command == 'node' and len(args) > 0:
                            install_path = args[0]

                    plugin_info = {
                        'id': server_name,
                        'name': server_name,
                        'install_path': install_path,
                        'source': 'system',
                        'config_file': str(config_path),
                        'env': server_config.get('env', {}),
                        'command': command,
                        'args': args,
                        'runtime': 'node' if command in ['node', 'npx'] else 'unknown',
                    }
                    plugins.append(plugin_info)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading config {config_path}: {e}")
                continue

        return plugins

    async def _analyze_plugin_directory(self, plugin_dir: Path, source: str) -> Optional[Dict]:
        """Analyze a plugin directory to extract metadata."""
        plugin_info = {
            'id': plugin_dir.name,
            'name': plugin_dir.name,
            'install_path': str(plugin_dir),
            'source': source,
        }

        # Check for mcp_server.json
        mcp_config = plugin_dir / "mcp_server.json"
        if mcp_config.exists():
            try:
                with open(mcp_config, 'r') as f:
                    config = json.load(f)
                plugin_info['name'] = config.get('name', plugin_dir.name)
                plugin_info['version'] = config.get('version', 'unknown')
                plugin_info['description'] = config.get('description', '')
                plugin_info['config_file'] = str(mcp_config)
            except (json.JSONDecodeError, IOError):
                pass

        # Check for package.json (Node.js plugins)
        package_json = plugin_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    config = json.load(f)
                plugin_info['name'] = config.get('name', plugin_dir.name)
                plugin_info['version'] = config.get('version', 'unknown')
                plugin_info['description'] = config.get('description', '')
                plugin_info['runtime'] = 'node'
            except (json.JSONDecodeError, IOError):
                pass

        # Check for pyproject.toml or setup.py (Python plugins)
        if (plugin_dir / "pyproject.toml").exists() or (plugin_dir / "setup.py").exists():
            plugin_info['runtime'] = 'python'

        # Get git origin if available
        git_dir = plugin_dir / ".git"
        if git_dir.exists():
            try:
                git_config = git_dir / "config"
                if git_config.exists():
                    with open(git_config, 'r') as f:
                        git_content = f.read()
                    # Simple parsing for url
                    for line in git_content.split('\n'):
                        if 'url =' in line:
                            url = line.split('=')[1].strip()
                            plugin_info['git_url'] = url
                            break
            except IOError:
                pass

        return plugin_info

    async def check_plugin_installed(self, plugin_id: str, git_url: Optional[str] = None) -> Dict:
        """Check if a specific plugin is installed.

        Args:
            plugin_id: Plugin identifier
            git_url: Optional git URL to match against

        Returns:
            Dict with:
            - installed: bool
            - location: str if installed
            - source: str if installed
        """
        installed_plugins = await self.detect_installed_plugins()

        for plugin in installed_plugins:
            # Match by ID
            if plugin['id'] == plugin_id:
                return {
                    'installed': True,
                    'location': plugin['install_path'],
                    'source': plugin['source'],
                    'plugin_info': plugin,
                }

            # Match by git URL if provided
            if git_url and plugin.get('git_url') == git_url:
                return {
                    'installed': True,
                    'location': plugin['install_path'],
                    'source': plugin['source'],
                    'plugin_info': plugin,
                }

        return {'installed': False}

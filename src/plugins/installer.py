"""Plugin installation utilities."""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from .models import PluginManifest


class PluginInstaller:
    """Handles plugin installation from git repositories."""

    def __init__(self, plugins_dir: Path):
        """
        Initialize plugin installer.

        Args:
            plugins_dir: Directory where plugins are installed
        """
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    async def install_from_git(
        self, git_url: str, plugin_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Install a plugin from a git repository.

        Args:
            git_url: Git repository URL
            plugin_name: Optional plugin name (derived from repo if not provided)

        Returns:
            Tuple of (success, message, install_path)
        """
        # Derive plugin name from git URL if not provided
        if not plugin_name:
            plugin_name = self._extract_repo_name(git_url)

        install_path = self.plugins_dir / plugin_name

        # Check if already installed
        if install_path.exists():
            return False, f"Plugin already installed at {install_path}", None

        try:
            # Clone repository
            result = await self._run_command(
                ["git", "clone", git_url, str(install_path)]
            )
            if result.returncode != 0:
                return (
                    False,
                    f"Git clone failed: {result.stderr}",
                    None,
                )

            # Read manifest
            manifest = await self._read_manifest(install_path)
            if not manifest:
                return (
                    False,
                    "Could not find or parse plugin manifest (mcp_server.json or package.json)",
                    None,
                )

            # Install dependencies
            dep_result = await self._install_dependencies(install_path, manifest)
            if not dep_result[0]:
                # Cleanup on failure
                shutil.rmtree(install_path, ignore_errors=True)
                return False, f"Dependency installation failed: {dep_result[1]}", None

            return True, f"Successfully installed {manifest.name}", install_path

        except Exception as e:
            # Cleanup on any error
            if install_path.exists():
                shutil.rmtree(install_path, ignore_errors=True)
            return False, f"Installation error: {str(e)}", None

    async def uninstall(self, install_path: Path) -> Tuple[bool, str]:
        """
        Uninstall a plugin by removing its directory.

        Args:
            install_path: Path to the plugin installation

        Returns:
            Tuple of (success, message)
        """
        try:
            if not install_path.exists():
                return False, "Plugin directory not found"

            shutil.rmtree(install_path)
            return True, f"Successfully uninstalled plugin from {install_path}"

        except Exception as e:
            return False, f"Uninstall error: {str(e)}"

    async def _read_manifest(self, plugin_path: Path) -> Optional[PluginManifest]:
        """
        Read plugin manifest from mcp_server.json or package.json.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            PluginManifest or None if not found
        """
        # Try mcp_server.json first
        mcp_manifest_path = plugin_path / "mcp_server.json"
        if mcp_manifest_path.exists():
            try:
                with open(mcp_manifest_path) as f:
                    data = json.load(f)
                return PluginManifest(
                    name=data.get("name", plugin_path.name),
                    version=data.get("version"),
                    author=data.get("author"),
                    description=data.get("description"),
                    tools=data.get("tools", []),
                    entry_point=data.get("entry_point"),
                    dependencies=data.get("dependencies", {}),
                )
            except Exception:
                pass

        # Fallback to package.json
        package_json_path = plugin_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path) as f:
                    data = json.load(f)
                return PluginManifest(
                    name=data.get("name", plugin_path.name),
                    version=data.get("version"),
                    author=data.get("author"),
                    description=data.get("description"),
                    entry_point=data.get("main"),
                    dependencies={"npm": list(data.get("dependencies", {}).keys())},
                )
            except Exception:
                pass

        return None

    async def _install_dependencies(
        self, plugin_path: Path, manifest: PluginManifest
    ) -> Tuple[bool, str]:
        """
        Install plugin dependencies.

        Args:
            plugin_path: Path to plugin directory
            manifest: Plugin manifest with dependency info

        Returns:
            Tuple of (success, message)
        """
        messages = []

        # Install npm dependencies
        if "npm" in manifest.dependencies or (plugin_path / "package.json").exists():
            result = await self._run_command(
                ["npm", "install"], cwd=plugin_path
            )
            if result.returncode != 0:
                return False, f"npm install failed: {result.stderr}"
            messages.append("npm dependencies installed")

        # Install pip dependencies
        if "pip" in manifest.dependencies:
            pip_deps = manifest.dependencies["pip"]
            if pip_deps:
                result = await self._run_command(
                    ["pip", "install"] + pip_deps, cwd=plugin_path
                )
                if result.returncode != 0:
                    return False, f"pip install failed: {result.stderr}"
                messages.append("pip dependencies installed")

        # Check for requirements.txt
        requirements_path = plugin_path / "requirements.txt"
        if requirements_path.exists():
            result = await self._run_command(
                ["pip", "install", "-r", "requirements.txt"], cwd=plugin_path
            )
            if result.returncode != 0:
                return False, f"pip install from requirements.txt failed: {result.stderr}"
            messages.append("pip requirements installed")

        return True, "; ".join(messages) if messages else "No dependencies to install"

    async def _run_command(
        self, cmd: list[str], cwd: Optional[Path] = None
    ) -> subprocess.CompletedProcess:
        """
        Run a command asynchronously.

        Args:
            cmd: Command and arguments
            cwd: Working directory

        Returns:
            CompletedProcess result
        """
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd) if cwd else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode or 0,
            stdout=stdout.decode(),
            stderr=stderr.decode(),
        )

    def _extract_repo_name(self, git_url: str) -> str:
        """
        Extract repository name from git URL.

        Args:
            git_url: Git repository URL

        Returns:
            Repository name
        """
        # Handle both https and git@ URLs
        name = git_url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name

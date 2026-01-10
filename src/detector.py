"""Project auto-detection and profiling."""

import subprocess
import toml
import json
from pathlib import Path
from typing import Optional
from .config import ProjectProfile


class ProjectDetector:
    """Detects project type and configuration from directory contents."""
    
    def __init__(self, project_path: str | Path):
        self.path = Path(project_path).expanduser().resolve()
        self._profile: Optional[ProjectProfile] = None
    
    def detect(self) -> ProjectProfile:
        """Run full project detection and return profile."""
        if self._profile is not None:
            return self._profile
        
        profile = ProjectProfile(
            path=self.path,
            name=self.path.name,
        )
        
        self._detect_python(profile)
        self._detect_node(profile)
        self._detect_git(profile)
        self._infer_ports(profile)
        self._build_project_type(profile)
        
        self._profile = profile
        return profile
    
    def _detect_python(self, profile: ProjectProfile):
        """Detect Python project details."""
        pyproject = self.path / "pyproject.toml"
        requirements = self.path / "requirements.txt"
        setup_py = self.path / "setup.py"
        
        if not any([pyproject.exists(), requirements.exists(), setup_py.exists()]):
            return
        
        profile.has_python = True
        
        # Check for virtual environment
        for venv_name in [".venv", "venv", ".virtualenv", "env"]:
            venv_path = self.path / venv_name
            if venv_path.exists() and (venv_path / "bin" / "python").exists():
                profile.venv_path = venv_path
                break
        
        # Parse pyproject.toml for dependencies
        if pyproject.exists():
            try:
                data = toml.load(pyproject)
                deps = []
                
                # Check various dependency locations
                if "project" in data and "dependencies" in data["project"]:
                    deps.extend(data["project"]["dependencies"])
                if "tool" in data and "poetry" in data["tool"]:
                    poetry = data["tool"]["poetry"]
                    if "dependencies" in poetry:
                        deps.extend(poetry["dependencies"].keys())
                
                deps_lower = [d.lower() for d in deps]
                profile.has_fastapi = any("fastapi" in d for d in deps_lower)
                profile.has_pytest = any("pytest" in d for d in deps_lower)
                
                # Get Python version requirement
                if "project" in data and "requires-python" in data["project"]:
                    profile.python_version = data["project"]["requires-python"]
                    
            except Exception:
                pass
        
        # Fallback: check requirements.txt
        if requirements.exists() and not profile.has_fastapi:
            try:
                content = requirements.read_text().lower()
                profile.has_fastapi = "fastapi" in content
                profile.has_pytest = "pytest" in content
            except Exception:
                pass
    
    def _detect_node(self, profile: ProjectProfile):
        """Detect Node.js project details."""
        package_json = self.path / "package.json"
        
        if not package_json.exists():
            return
        
        profile.has_node = True
        
        # Detect package manager
        if (self.path / "pnpm-lock.yaml").exists():
            profile.package_manager = "pnpm"
        elif (self.path / "yarn.lock").exists():
            profile.package_manager = "yarn"
        elif (self.path / "package-lock.json").exists():
            profile.package_manager = "npm"
        else:
            profile.package_manager = "npm"  # default
        
        try:
            data = json.loads(package_json.read_text())
            
            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))
            
            deps_lower = [k.lower() for k in all_deps.keys()]
            profile.has_react = "react" in deps_lower
            profile.has_vite = "vite" in deps_lower
            
            # Get node version from engines
            if "engines" in data and "node" in data["engines"]:
                profile.node_version = data["engines"]["node"]
                
        except Exception:
            pass
    
    def _detect_git(self, profile: ProjectProfile):
        """Detect Git repository details."""
        git_dir = self.path / ".git"
        
        if not git_dir.exists():
            return
        
        profile.has_git = True
        
        try:
            # Get remote
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                profile.git_remote = result.stdout.strip()
            
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                profile.git_branch = result.stdout.strip()
            
            # Get user email (for profile validation)
            result = subprocess.run(
                ["git", "config", "user.email"],
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                profile.git_user_email = result.stdout.strip()
            
            # Get user name
            result = subprocess.run(
                ["git", "config", "user.name"],
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                profile.git_user_name = result.stdout.strip()
                
        except Exception:
            pass
    
    def _infer_ports(self, profile: ProjectProfile):
        """Infer common ports from project type."""
        if profile.has_fastapi:
            profile.backend_port = 8000
        
        if profile.has_vite:
            profile.frontend_port = 5173
        elif profile.has_react:
            profile.frontend_port = 3000
    
    def _build_project_type(self, profile: ProjectProfile):
        """Build project type list from detected features."""
        types = []
        
        if profile.has_python:
            types.append("python")
        if profile.has_fastapi:
            types.append("fastapi")
        if profile.has_pytest:
            types.append("pytest")
        if profile.has_node:
            types.append("node")
        if profile.has_react:
            types.append("react")
        if profile.has_vite:
            types.append("vite")
        if profile.has_git:
            types.append("git")
        
        profile.project_type = types
    
    def get_start_commands(self) -> dict[str, str]:
        """Get suggested start commands based on project profile."""
        profile = self.detect()
        commands = {}
        
        # Python/FastAPI backend
        if profile.has_fastapi:
            if profile.venv_path:
                activate = f"source {profile.venv_path}/bin/activate && "
            else:
                activate = ""
            commands["backend"] = f"{activate}uvicorn main:app --reload --port {profile.backend_port or 8000}"
        
        # Node/React frontend
        if profile.has_node:
            pm = profile.package_manager or "npm"
            run_cmd = "run dev" if pm == "npm" else "dev"
            commands["frontend"] = f"{pm} {run_cmd}"
        
        # Tests
        if profile.has_pytest:
            if profile.venv_path:
                commands["test"] = f"source {profile.venv_path}/bin/activate && pytest"
            else:
                commands["test"] = "pytest"
        elif profile.has_node:
            pm = profile.package_manager or "npm"
            commands["test"] = f"{pm} test"
        
        return commands
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary for JSON serialization."""
        profile = self.detect()
        return profile.model_dump(mode='json')

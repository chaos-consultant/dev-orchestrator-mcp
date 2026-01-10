"""Shell command executor with guardrails and interactive approval."""

import asyncio
import subprocess
import os
import signal
from pathlib import Path
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import psutil

from .config import get_config, GuardrailsConfig


class CommandStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    cwd: str
    status: CommandStatus
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    approval_reason: Optional[str] = None
    blocked_reason: Optional[str] = None


@dataclass
class PendingApproval:
    """A command awaiting user approval."""
    id: str
    command: str
    cwd: str
    reason: str
    requested_at: datetime
    callback: Optional[Callable[[bool], Awaitable[None]]] = None


class ProcessManager:
    """Manages running processes."""
    
    def __init__(self):
        self.processes: dict[str, subprocess.Popen] = {}
        self._process_counter = 0
    
    def _generate_id(self) -> str:
        self._process_counter += 1
        return f"proc_{self._process_counter}"
    
    async def start_process(
        self,
        command: str,
        cwd: str,
        env: Optional[dict] = None
    ) -> tuple[str, subprocess.Popen]:
        """Start a background process and return its ID."""
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        proc_id = self._generate_id()
        self.processes[proc_id] = proc
        return proc_id, proc
    
    def stop_process(self, proc_id: str) -> bool:
        """Stop a running process by ID."""
        proc = self.processes.get(proc_id)
        if proc is None:
            return False
        
        try:
            # Kill the entire process group
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        
        del self.processes[proc_id]
        return True
    
    def get_process_info(self, proc_id: str) -> Optional[dict]:
        """Get information about a running process."""
        proc = self.processes.get(proc_id)
        if proc is None:
            return None
        
        try:
            ps = psutil.Process(proc.pid)
            return {
                "id": proc_id,
                "pid": proc.pid,
                "status": ps.status(),
                "cpu_percent": ps.cpu_percent(),
                "memory_mb": ps.memory_info().rss / 1024 / 1024,
                "running": proc.poll() is None
            }
        except psutil.NoSuchProcess:
            return {"id": proc_id, "running": False}
    
    def list_processes(self) -> list[dict]:
        """List all managed processes."""
        return [
            self.get_process_info(pid) 
            for pid in list(self.processes.keys())
            if self.get_process_info(pid) is not None
        ]
    
    def cleanup_dead(self):
        """Remove dead processes from tracking."""
        dead = [
            pid for pid, proc in self.processes.items()
            if proc.poll() is not None
        ]
        for pid in dead:
            del self.processes[pid]


class ShellExecutor:
    """Executes shell commands with guardrails."""
    
    def __init__(
        self,
        guardrails: Optional[GuardrailsConfig] = None,
        approval_handler: Optional[Callable[[PendingApproval], Awaitable[bool]]] = None,
        log_handler: Optional[Callable[[str, str], None]] = None
    ):
        self.guardrails = guardrails or get_config().guardrails
        self.approval_handler = approval_handler
        self.log_handler = log_handler
        self.process_manager = ProcessManager()
        self.pending_approvals: dict[str, PendingApproval] = {}
        self._approval_counter = 0
        self.command_history: list[CommandResult] = []
    
    def _log(self, level: str, message: str):
        """Log a message."""
        if self.log_handler:
            self.log_handler(level, message)
    
    def _generate_approval_id(self) -> str:
        self._approval_counter += 1
        return f"approval_{self._approval_counter}"
    
    async def execute(
        self,
        command: str,
        cwd: str = ".",
        timeout: int = 300,
        env: Optional[dict] = None,
        background: bool = False
    ) -> CommandResult:
        """Execute a command with guardrails check."""
        
        cwd = str(Path(cwd).expanduser().resolve())
        result = CommandResult(command=command, cwd=cwd, status=CommandStatus.PENDING)
        
        # Check if blocked
        if self.guardrails.is_blocked(command):
            result.status = CommandStatus.BLOCKED
            result.blocked_reason = "Command matches absolute blocklist"
            self._log("ERROR", f"Blocked command: {command}")
            self.command_history.append(result)
            return result
        
        # Check if directory is allowed
        if not self.guardrails.is_in_allowed_directory(cwd):
            result.status = CommandStatus.BLOCKED
            result.blocked_reason = f"Directory {cwd} is not in allowed directories"
            self._log("ERROR", f"Blocked: directory not allowed: {cwd}")
            self.command_history.append(result)
            return result
        
        # Check if approval required
        needs_approval, reason = self.guardrails.requires_approval(command)
        if needs_approval:
            result.approval_reason = reason
            self._log("WARN", f"Approval required: {command} - {reason}")
            
            if self.approval_handler:
                approval_id = self._generate_approval_id()
                pending = PendingApproval(
                    id=approval_id,
                    command=command,
                    cwd=cwd,
                    reason=reason,
                    requested_at=datetime.now()
                )
                self.pending_approvals[approval_id] = pending
                
                # Wait for approval
                approved = await self.approval_handler(pending)
                del self.pending_approvals[approval_id]
                
                if not approved:
                    result.status = CommandStatus.REJECTED
                    self._log("INFO", f"Command rejected: {command}")
                    self.command_history.append(result)
                    return result
                
                result.status = CommandStatus.APPROVED
            else:
                # No approval handler - reject by default
                result.status = CommandStatus.REJECTED
                result.blocked_reason = "No approval handler configured"
                self.command_history.append(result)
                return result
        
        # Execute the command
        result.status = CommandStatus.RUNNING
        result.started_at = datetime.now()
        self._log("INFO", f"Executing: {command} in {cwd}")
        
        try:
            if background:
                proc_id, proc = await self.process_manager.start_process(command, cwd, env)
                result.status = CommandStatus.COMPLETED
                result.stdout = f"Started background process: {proc_id} (PID: {proc.pid})"
                result.exit_code = 0
            else:
                process_env = os.environ.copy()
                if env:
                    process_env.update(env)
                
                proc = await asyncio.create_subprocess_shell(
                    command,
                    cwd=cwd,
                    env=process_env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=timeout
                    )
                    result.stdout = stdout.decode('utf-8', errors='replace')
                    result.stderr = stderr.decode('utf-8', errors='replace')
                    result.exit_code = proc.returncode
                    result.status = CommandStatus.COMPLETED if proc.returncode == 0 else CommandStatus.FAILED
                except asyncio.TimeoutError:
                    proc.kill()
                    result.status = CommandStatus.TIMEOUT
                    result.stderr = f"Command timed out after {timeout} seconds"
                    
        except Exception as e:
            result.status = CommandStatus.FAILED
            result.stderr = str(e)
        
        result.completed_at = datetime.now()
        self.command_history.append(result)
        self._log("INFO", f"Completed: {command} - {result.status}")
        
        return result
    
    async def execute_with_venv(
        self,
        command: str,
        cwd: str,
        venv_path: str,
        **kwargs
    ) -> CommandResult:
        """Execute a command with virtual environment activated."""
        activate = Path(venv_path) / "bin" / "activate"
        wrapped_command = f"source {activate} && {command}"
        return await self.execute(wrapped_command, cwd, **kwargs)
    
    def get_pending_approvals(self) -> list[PendingApproval]:
        """Get list of commands pending approval."""
        return list(self.pending_approvals.values())
    
    def approve(self, approval_id: str) -> bool:
        """Approve a pending command."""
        if approval_id in self.pending_approvals:
            pending = self.pending_approvals[approval_id]
            if pending.callback:
                asyncio.create_task(pending.callback(True))
            return True
        return False
    
    def reject(self, approval_id: str) -> bool:
        """Reject a pending command."""
        if approval_id in self.pending_approvals:
            pending = self.pending_approvals[approval_id]
            if pending.callback:
                asyncio.create_task(pending.callback(False))
            return True
        return False
    
    def get_history(self, limit: int = 50) -> list[dict]:
        """Get recent command history."""
        return [
            {
                "command": r.command,
                "cwd": r.cwd,
                "status": r.status.value,
                "exit_code": r.exit_code,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in self.command_history[-limit:]
        ]

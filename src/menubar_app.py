"""macOS menubar app for Dev Orchestrator."""

import asyncio
import json
import threading
import webbrowser
from typing import Optional
import rumps
import websockets

from .config import get_config


class DevOrchestratorMenubar(rumps.App):
    """macOS menubar application for Dev Orchestrator status."""
    
    def __init__(self):
        super().__init__(
            "Dev Orchestrator",
            icon=None,  # Will use emoji/text as icon
            title="🔧",
            quit_button=None  # Custom quit
        )
        
        self.config = get_config()
        self.ws_url = f"ws://{self.config.host}:{self.config.websocket_port}"
        self.dashboard_url = f"http://{self.config.host}:{self.config.dashboard_port}"
        
        # State
        self.current_project: Optional[str] = None
        self.services: dict = {}
        self.pending_approvals: list = []
        self.connected = False
        
        # Build menu
        self._build_menu()
        
        # Start WebSocket connection in background
        self.ws_thread = threading.Thread(target=self._run_ws_loop, daemon=True)
        self.ws_thread.start()
    
    def _build_menu(self):
        """Build the menubar menu."""
        self.menu.clear()
        
        # Status section
        if self.connected:
            status_text = "● Connected" 
        else:
            status_text = "○ Disconnected"
        self.menu.add(rumps.MenuItem(status_text, callback=None))
        
        self.menu.add(rumps.separator)
        
        # Project section
        if self.current_project:
            self.menu.add(rumps.MenuItem(f"📁 {self.current_project}", callback=None))
        else:
            self.menu.add(rumps.MenuItem("📁 No project detected", callback=None))
        
        self.menu.add(rumps.separator)
        
        # Services section
        services_menu = rumps.MenuItem("🚀 Services")
        if self.services:
            for svc_id, svc in self.services.items():
                svc_item = rumps.MenuItem(
                    f"{svc.get('name', svc_id)}: port {svc.get('port', '?')}",
                    callback=None
                )
                services_menu.add(svc_item)
        else:
            services_menu.add(rumps.MenuItem("No services running", callback=None))
        self.menu.add(services_menu)
        
        # Pending approvals
        if self.pending_approvals:
            self.menu.add(rumps.separator)
            approvals_menu = rumps.MenuItem(f"⚠️ Pending Approvals ({len(self.pending_approvals)})")
            for approval in self.pending_approvals:
                cmd = approval.get('command', '')[:40]
                item = rumps.MenuItem(
                    f"• {cmd}...",
                    callback=lambda _, a=approval: self._show_approval_dialog(a)
                )
                approvals_menu.add(item)
            self.menu.add(approvals_menu)
        
        self.menu.add(rumps.separator)
        
        # Actions
        self.menu.add(rumps.MenuItem("Open Dashboard", callback=self._open_dashboard))
        self.menu.add(rumps.MenuItem("View Logs", callback=self._view_logs))
        
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit", callback=self._quit))
    
    def _run_ws_loop(self):
        """Run WebSocket connection loop in background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._ws_connect())
    
    async def _ws_connect(self):
        """Connect to WebSocket server and handle messages."""
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.connected = True
                    self._update_icon()
                    self._build_menu()
                    
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            await self._handle_ws_message(data)
                        except json.JSONDecodeError:
                            pass
            except Exception:
                self.connected = False
                self._update_icon()
                self._build_menu()
                await asyncio.sleep(5)  # Retry after 5 seconds
    
    async def _handle_ws_message(self, data: dict):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        
        if msg_type == "state":
            state = data.get("data", {})
            project = state.get("current_project")
            if project:
                self.current_project = project.get("name")
            self.services = state.get("services", {})
            self.pending_approvals = state.get("pending_approvals", [])
            self._build_menu()
            self._update_icon()
        
        elif msg_type == "project_changed":
            self.current_project = data.get("data", {}).get("name")
            self._build_menu()
        
        elif msg_type == "service_started":
            svc = data.get("data", {})
            self.services[svc.get("id")] = svc
            self._build_menu()
            self._update_icon()
        
        elif msg_type == "service_stopped":
            svc_id = data.get("data", {}).get("id")
            self.services.pop(svc_id, None)
            self._build_menu()
            self._update_icon()
        
        elif msg_type == "approval_required":
            self.pending_approvals.append(data.get("data", {}))
            self._build_menu()
            self._update_icon()
            self._notify_approval(data.get("data", {}))
        
        elif msg_type == "approval_resolved":
            approval_id = data.get("data", {}).get("id")
            self.pending_approvals = [
                a for a in self.pending_approvals
                if a.get("id") != approval_id
            ]
            self._build_menu()
            self._update_icon()
    
    def _update_icon(self):
        """Update menubar icon based on state."""
        if not self.connected:
            self.title = "🔧"
        elif self.pending_approvals:
            self.title = "⚠️"
        elif self.services:
            self.title = "🟢"
        else:
            self.title = "🔧"
    
    def _notify_approval(self, approval: dict):
        """Show notification for pending approval."""
        rumps.notification(
            title="Approval Required",
            subtitle=approval.get("reason", ""),
            message=approval.get("command", "")[:50] + "..."
        )
    
    def _show_approval_dialog(self, approval: dict):
        """Show approval dialog."""
        cmd = approval.get("command", "")
        reason = approval.get("reason", "")
        
        response = rumps.alert(
            title="Command Approval Required",
            message=f"Command: {cmd}\n\nReason: {reason}",
            ok="Approve",
            cancel="Reject"
        )
        
        if response == 1:  # Approve
            self._send_approval(approval.get("id"), True)
        else:  # Reject
            self._send_approval(approval.get("id"), False)
    
    def _send_approval(self, approval_id: str, approved: bool):
        """Send approval/rejection via WebSocket."""
        def send():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._ws_send_approval(approval_id, approved))
        
        threading.Thread(target=send, daemon=True).start()
    
    async def _ws_send_approval(self, approval_id: str, approved: bool):
        """Send approval message via WebSocket."""
        try:
            async with websockets.connect(self.ws_url) as ws:
                msg_type = "approve" if approved else "reject"
                await ws.send(json.dumps({
                    "type": msg_type,
                    "approval_id": approval_id
                }))
        except Exception:
            pass
    
    @rumps.clicked("Open Dashboard")
    def _open_dashboard(self, _):
        """Open the web dashboard."""
        webbrowser.open(self.dashboard_url)
    
    @rumps.clicked("View Logs")
    def _view_logs(self, _):
        """Open logs in terminal."""
        import subprocess
        log_file = self.config.log_file
        subprocess.Popen(["open", "-a", "Terminal", str(log_file.parent)])
    
    def _quit(self, _):
        """Quit the application."""
        rumps.quit_application()


def main():
    """Run the menubar app."""
    app = DevOrchestratorMenubar()
    app.run()


if __name__ == "__main__":
    main()

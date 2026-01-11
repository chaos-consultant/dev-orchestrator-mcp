"""
Extension Creator - Template-based scaffolding for widgets, workflows, and integrations
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Literal


class ExtensionCreator:
    """Creates extension templates for widgets, workflows, and integrations."""

    def __init__(self, extensions_dir: Path = None):
        self.extensions_dir = extensions_dir or Path.home() / ".dev-orchestrator" / "extensions"
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        (self.extensions_dir / "widgets").mkdir(exist_ok=True)
        (self.extensions_dir / "workflows").mkdir(exist_ok=True)
        (self.extensions_dir / "integrations").mkdir(exist_ok=True)

    def create_widget(
        self,
        name: str,
        description: str,
        author: str,
        category: str,
        template_type: Literal["basic", "interactive", "realtime"],
        permissions: List[str] = None,
        grid_size: Dict[str, int] = None
    ) -> Dict[str, str]:
        """
        Create a new widget from template.

        Args:
            name: Widget name (kebab-case)
            description: Widget description
            author: Author name
            category: Widget category (monitoring, tools, analytics, etc.)
            template_type: "basic", "interactive", or "realtime"
            permissions: List of permissions (read-state, execute-commands, read-logs)
            grid_size: Grid size config (xs, sm, md, lg, xl)

        Returns:
            Dict with created file paths
        """
        widget_dir = self.extensions_dir / "widgets" / name
        if widget_dir.exists():
            raise ValueError(f"Widget directory already exists: {widget_dir}")

        widget_dir.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # Create manifest
        manifest_path = widget_dir / "manifest.json"
        manifest = self._create_widget_manifest(
            name, description, author, category,
            permissions or ["read-state"],
            grid_size or {"xs": 12, "md": 6, "lg": 4}
        )
        manifest_path.write_text(json.dumps(manifest, indent=2))
        created_files["manifest"] = str(manifest_path)

        # Create Widget.tsx
        widget_path = widget_dir / "Widget.tsx"
        if template_type == "basic":
            content = self._create_basic_widget(name, description)
        elif template_type == "interactive":
            content = self._create_interactive_widget(name, description)
        else:  # realtime
            content = self._create_realtime_widget(name, description)

        widget_path.write_text(content)
        created_files["widget"] = str(widget_path)

        # Create README
        readme_path = widget_dir / "README.md"
        readme_path.write_text(self._create_widget_readme(name, description, author))
        created_files["readme"] = str(readme_path)

        return created_files

    def create_workflow(
        self,
        name: str,
        description: str,
        author: str,
        version: str = "1.0.0",
        parameters: List[Dict] = None,
        steps: List[Dict] = None
    ) -> str:
        """
        Create a new workflow from template.

        Args:
            name: Workflow name
            description: Workflow description
            author: Author name
            version: Workflow version
            parameters: List of parameter definitions
            steps: List of step definitions

        Returns:
            Path to created workflow file
        """
        workflow_path = self.extensions_dir / "workflows" / f"{name}.yaml"
        if workflow_path.exists():
            raise ValueError(f"Workflow already exists: {workflow_path}")

        workflow = {
            "name": name,
            "description": description,
            "version": version,
            "author": author,
            "parameters": parameters or [],
            "steps": steps or [
                {
                    "name": "Example step",
                    "command": "echo 'Hello from workflow'",
                    "cwd": ".",
                    "continue_on_error": False
                }
            ],
            "on_success": [],
            "on_failure": []
        }

        workflow_path.write_text(yaml.dump(workflow, default_flow_style=False, sort_keys=False))
        return str(workflow_path)

    def create_integration(
        self,
        name: str,
        service_type: Literal["slack", "github", "jira", "custom"],
        config: Dict = None
    ) -> Dict[str, str]:
        """
        Create a new integration from template.

        Args:
            name: Integration name (kebab-case)
            service_type: Service type
            config: Integration configuration

        Returns:
            Dict with created file paths
        """
        integration_dir = self.extensions_dir / "integrations" / name
        if integration_dir.exists():
            raise ValueError(f"Integration directory already exists: {integration_dir}")

        integration_dir.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # Create config.json
        config_path = integration_dir / "config.json"
        integration_config = config or self._get_default_config(service_type)
        config_path.write_text(json.dumps(integration_config, indent=2))
        created_files["config"] = str(config_path)

        # Create integration.py
        integration_path = integration_dir / "integration.py"
        if service_type == "slack":
            content = self._create_slack_integration(name)
        elif service_type == "github":
            content = self._create_github_integration(name)
        elif service_type == "jira":
            content = self._create_jira_integration(name)
        else:  # custom
            content = self._create_custom_integration(name)

        integration_path.write_text(content)
        created_files["integration"] = str(integration_path)

        # Create README
        readme_path = integration_dir / "README.md"
        readme_path.write_text(self._create_integration_readme(name, service_type))
        created_files["readme"] = str(readme_path)

        return created_files

    def _create_widget_manifest(
        self, name: str, description: str, author: str, category: str,
        permissions: List[str], grid_size: Dict[str, int]
    ) -> Dict:
        """Create widget manifest."""
        return {
            "id": name,
            "name": name.replace("-", " ").title(),
            "version": "1.0.0",
            "description": description,
            "author": author,
            "entry": "Widget.tsx",
            "permissions": permissions,
            "grid": {
                "defaultSize": grid_size,
                "minSize": {"xs": 12, "md": 6},
                "maxSize": {"xs": 12, "md": 12, "lg": 12}
            },
            "category": category,
            "updateInterval": 5000
        }

    def _create_basic_widget(self, name: str, description: str) -> str:
        """Create basic widget template."""
        component_name = ''.join(word.capitalize() for word in name.split('-'))
        return f'''import React from 'react';
import {{ Card, CardHeader, CardContent, Typography, Box }} from '@mui/material';

interface WidgetProps {{
  state: any;
  sendMessage: (msg: any) => void;
  theme: any;
  config: Record<string, any>;
}}

const {component_name}Widget: React.FC<WidgetProps> = ({{ state }}) => {{
  return (
    <Card>
      <CardHeader title="{name.replace('-', ' ').title()}" />
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body1">
            Current Project: {{state?.current_project?.name || 'None'}}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}};

export default {component_name}Widget;
'''

    def _create_interactive_widget(self, name: str, description: str) -> str:
        """Create interactive widget template with buttons."""
        component_name = ''.join(word.capitalize() for word in name.split('-'))
        return f'''import React, {{ useState }} from 'react';
import {{
  Card,
  CardHeader,
  CardContent,
  Typography,
  Button,
  Stack,
  TextField,
  Alert,
}} from '@mui/material';

interface WidgetProps {{
  state: any;
  sendMessage: (msg: any) => void;
  theme: any;
  config: Record<string, any>;
}}

const {component_name}Widget: React.FC<WidgetProps> = ({{ state, sendMessage }}) => {{
  const [input, setInput] = useState('');
  const [result, setResult] = useState<string | null>(null);

  const handleAction = () => {{
    // Send message to backend
    sendMessage({{
      type: 'custom_action',
      plugin: '{name}',
      data: {{ input }}
    }});
    setResult(`Action executed with: ${{input}}`);
  }};

  return (
    <Card>
      <CardHeader title="{name.replace('-', ' ').title()}" />
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {description}
        </Typography>

        <Stack spacing={2} sx={{ mt: 2 }}>
          <TextField
            size="small"
            label="Input"
            value={{input}}
            onChange={{(e) => setInput(e.target.value)}}
            fullWidth
          />

          <Button
            variant="contained"
            onClick={{handleAction}}
            disabled={{!input}}
          >
            Execute Action
          </Button>

          {{result && (
            <Alert severity="success">{{result}}</Alert>
          )}}
        </Stack>
      </CardContent>
    </Card>
  );
}};

export default {component_name}Widget;
'''

    def _create_realtime_widget(self, name: str, description: str) -> str:
        """Create realtime widget template with auto-refresh."""
        component_name = ''.join(word.capitalize() for word in name.split('-'))
        return f'''import React, {{ useState, useEffect }} from 'react';
import {{
  Card,
  CardHeader,
  CardContent,
  Typography,
  CircularProgress,
  Box,
  Chip,
}} from '@mui/material';

interface WidgetProps {{
  state: any;
  sendMessage: (msg: any) => void;
  theme: any;
  config: Record<string, any>;
}}

const {component_name}Widget: React.FC<WidgetProps> = ({{ state, config }}) => {{
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    // Auto-refresh every config.updateInterval ms
    const interval = setInterval(() => {{
      updateData();
    }}, config.updateInterval || 5000);

    updateData();

    return () => clearInterval(interval);
  }}, [state]);

  const updateData = () => {{
    setLoading(true);
    // Extract data from state
    const newData = {{
      services: state?.services?.length || 0,
      projects: state?.workspace?.total_repos || 0,
      status: state?.services?.some((s: any) => s.status === 'running') ? 'active' : 'idle',
    }};
    setData(newData);
    setLoading(false);
  }};

  if (loading && !data) {{
    return (
      <Card>
        <CardHeader title="{name.replace('-', ' ').title()}" />
        <CardContent>
          <CircularProgress size={{24}} />
        </CardContent>
      </Card>
    );
  }}

  return (
    <Card>
      <CardHeader
        title="{name.replace('-', ' ').title()}"
        subheader="Real-time monitoring"
      />
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {description}
        </Typography>

        <Box sx={{ mt: 2 }}>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Chip label={{`Services: ${{data?.services || 0}}`}} size="small" />
            <Chip label={{`Projects: ${{data?.projects || 0}}`}} size="small" />
            <Chip
              label={{data?.status || 'unknown'}}
              size="small"
              color={{data?.status === 'active' ? 'success' : 'default'}}
            />
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
}};

export default {component_name}Widget;
'''

    def _get_default_config(self, service_type: str) -> Dict:
        """Get default config for service type."""
        configs = {
            "slack": {
                "enabled": True,
                "webhook_url": "",
                "channel": "#dev-notifications",
                "notify_on_failure": True,
                "notify_on_long_running": True,
                "long_running_threshold_seconds": 300
            },
            "github": {
                "enabled": True,
                "token": "",
                "repo": "",
                "auto_create_issues": False
            },
            "jira": {
                "enabled": True,
                "url": "",
                "email": "",
                "api_token": "",
                "default_project": ""
            },
            "custom": {
                "enabled": True
            }
        }
        return configs.get(service_type, configs["custom"])

    def _create_slack_integration(self, name: str) -> str:
        """Create Slack integration template."""
        return '''"""
Slack Integration for Dev Orchestrator
"""
import aiohttp
from typing import Dict, Any


class SlackIntegration:
    """Slack integration for posting notifications."""

    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config["webhook_url"]
        self.channel = config.get("channel", "#dev-notifications")
        self.notify_on_failure = config.get("notify_on_failure", True)
        self.enabled = config.get("enabled", True)

    async def on_command_complete(self, command: dict, result: dict):
        """Called when a command completes."""
        if not self.enabled:
            return

        if result["exit_code"] != 0 and self.notify_on_failure:
            await self.post_failure(command, result)

    async def on_service_start(self, service: dict):
        """Called when a service starts."""
        if not self.enabled:
            return

        await self.post_message(f"🟢 Service started: {service['name']}")

    async def on_service_stop(self, service: dict):
        """Called when a service stops."""
        if not self.enabled:
            return

        await self.post_message(f"🔴 Service stopped: {service['name']}")

    async def on_approval_required(self, command: dict):
        """Called when approval is required."""
        if not self.enabled:
            return

        await self.post_message(
            f"⚠️ Approval required for command: `{command['command']}`"
        )

    async def post_failure(self, command: dict, result: dict):
        """Post failure notification."""
        payload = {
            "channel": self.channel,
            "text": f"❌ Command failed: `{command['command']}`",
            "attachments": [{
                "color": "danger",
                "fields": [
                    {"title": "Exit Code", "value": str(result["exit_code"]), "short": True},
                    {"title": "Directory", "value": command.get("cwd", ""), "short": True},
                    {"title": "Error", "value": result.get("stderr", "")[:500], "short": False}
                ]
            }]
        }
        await self._post_webhook(payload)

    async def post_message(self, text: str):
        """Post simple text message."""
        payload = {
            "channel": self.channel,
            "text": text
        }
        await self._post_webhook(payload)

    async def _post_webhook(self, payload: dict):
        """Post to Slack webhook."""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=payload) as resp:
                if resp.status != 200:
                    print(f"Slack webhook error: {resp.status}")

    async def test_connection(self) -> bool:
        """Test Slack webhook connection."""
        try:
            await self.post_message("✅ Test message from Dev Orchestrator")
            return True
        except Exception as e:
            print(f"Slack test failed: {e}")
            return False
'''

    def _create_github_integration(self, name: str) -> str:
        """Create GitHub integration template."""
        return '''"""
GitHub Integration for Dev Orchestrator
"""
import aiohttp
from typing import Dict, Any


class GitHubIntegration:
    """GitHub integration for creating issues and managing repos."""

    def __init__(self, config: Dict[str, Any]):
        self.token = config["token"]
        self.repo = config["repo"]
        self.auto_create_issues = config.get("auto_create_issues", False)
        self.enabled = config.get("enabled", True)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def on_command_complete(self, command: dict, result: dict):
        """Called when a command completes."""
        if not self.enabled:
            return

        if result["exit_code"] != 0 and self.auto_create_issues:
            await self.create_failure_issue(command, result)

    async def create_failure_issue(self, command: dict, result: dict):
        """Create GitHub issue for command failure."""
        title = f"Command failed: {command['command'][:50]}"
        body = f"""## Command Failed

**Command:** `{command['command']}`
**Directory:** `{command.get('cwd', '')}`
**Exit Code:** {result['exit_code']}

### Error Output

```
{result.get('stderr', '')[:1000]}
```

### Standard Output

```
{result.get('stdout', '')[:1000]}
```

---
*Auto-generated by Dev Orchestrator*
"""

        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/repos/{self.repo}/issues"
            payload = {
                "title": title,
                "body": body,
                "labels": ["bug", "auto-generated"]
            }
            async with session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    print(f"Created issue: {data['html_url']}")
                else:
                    print(f"Failed to create issue: {resp.status}")

    async def test_connection(self) -> bool:
        """Test GitHub API connection."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.github.com/repos/{self.repo}"
                async with session.get(url, headers=self.headers) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"GitHub test failed: {e}")
            return False
'''

    def _create_jira_integration(self, name: str) -> str:
        """Create Jira integration template."""
        return '''"""
Jira Integration for Dev Orchestrator
"""
import aiohttp
import base64
from typing import Dict, Any


class JiraIntegration:
    """Jira integration for creating tickets and managing workflows."""

    def __init__(self, config: Dict[str, Any]):
        self.url = config["url"]
        self.email = config["email"]
        self.api_token = config["api_token"]
        self.default_project = config.get("default_project", "")
        self.enabled = config.get("enabled", True)

        # Basic auth for Jira
        auth_string = f"{self.email}:{self.api_token}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json"
        }

    async def on_command_complete(self, command: dict, result: dict):
        """Called when a command completes."""
        if not self.enabled or not self.default_project:
            return

        # Example: Create ticket for failures
        if result["exit_code"] != 0:
            await self.create_ticket(
                summary=f"Command failed: {command['command'][:50]}",
                description=f"Exit code: {result['exit_code']}\\n\\nError: {result.get('stderr', '')}"
            )

    async def create_ticket(self, summary: str, description: str, issue_type: str = "Bug"):
        """Create Jira ticket."""
        url = f"{self.url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.default_project},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}]
                        }
                    ]
                },
                "issuetype": {"name": issue_type}
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    print(f"Created ticket: {data['key']}")
                else:
                    print(f"Failed to create ticket: {resp.status}")

    async def test_connection(self) -> bool:
        """Test Jira API connection."""
        try:
            url = f"{self.url}/rest/api/3/myself"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"Jira test failed: {e}")
            return False
'''

    def _create_custom_integration(self, name: str) -> str:
        """Create custom integration template."""
        return f'''"""
Custom Integration for Dev Orchestrator
"""
from typing import Dict, Any


class {name.replace('-', '_').title().replace('_', '')}Integration:
    """Custom integration template."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)

    async def on_command_complete(self, command: dict, result: dict):
        """Called when a command completes."""
        if not self.enabled:
            return
        # Implement your logic here
        pass

    async def on_service_start(self, service: dict):
        """Called when a service starts."""
        if not self.enabled:
            return
        # Implement your logic here
        pass

    async def on_service_stop(self, service: dict):
        """Called when a service stops."""
        if not self.enabled:
            return
        # Implement your logic here
        pass

    async def on_approval_required(self, command: dict):
        """Called when approval is required."""
        if not self.enabled:
            return
        # Implement your logic here
        pass

    async def test_connection(self) -> bool:
        """Test integration connection."""
        return True
'''

    def _create_widget_readme(self, name: str, description: str, author: str) -> str:
        """Create widget README."""
        return f'''# {name.replace('-', ' ').title()} Widget

{description}

## Author

{author}

## Installation

The widget is automatically loaded when placed in `~/.dev-orchestrator/extensions/widgets/{name}/`

## Usage

This widget will appear on the dashboard based on its grid configuration in `manifest.json`.

### Configuration

Edit `manifest.json` to customize:
- Grid size (responsive breakpoints)
- Update interval (for real-time widgets)
- Permissions
- Category

### Development

To modify the widget, edit `Widget.tsx` and reload the dashboard.

## License

MIT
'''

    def _create_integration_readme(self, name: str, service_type: str) -> str:
        """Create integration README."""
        return f'''# {name.replace('-', ' ').title()} Integration

{service_type.title()} integration for Dev Orchestrator.

## Setup

1. Edit `config.json` with your credentials
2. Restart Dev Orchestrator to load the integration
3. Test the connection from the dashboard

## Configuration

See `config.json` for available options.

## Events

This integration responds to the following events:

- `on_command_complete`: When a command finishes
- `on_service_start`: When a service starts
- `on_service_stop`: When a service stops
- `on_approval_required`: When a command needs approval

## Testing

Use the dashboard to test the integration connection.

## License

MIT
'''

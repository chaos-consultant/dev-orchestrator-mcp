# Dev Orchestrator MCP

[![CI](https://github.com/chaos-consultant/dev-orchestrator-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/chaos-consultant/dev-orchestrator-mcp/actions/workflows/ci.yml)

A Mac dev environment orchestration MCP server that enables Claude to run and test your development stack with guardrails and interactive approval.

## Features

### 🎯 Core Features

- **Full Shell Control with Guardrails**: Execute commands with automatic blocking of dangerous operations
- **Multi-Provider Natural Language Processing**: AI-powered command translation with multiple backends:
  - **Ollama** (local, privacy-first)
  - **OpenAI GPT-4** (cloud)
  - **Google Gemini** (cloud)
  - **Anthropic Claude** (cloud)
  - Convert natural language to shell commands
  - Intelligent intent detection (shell vs MCP tool)
  - Toggle NLP on/off in dashboard
- **Interactive Approval**: Commands matching dangerous patterns require explicit approval
- **Project Auto-Detection**: Automatically detects FastAPI, React, Python, Node.js, Go, Rust projects
- **Virtual Environment Management**: Auto-activates correct venv per project
- **Git Profile Validation**: Ensures correct git user per project directory
- **WebSocket Connection Management**: Automatic cleanup of dead connections prevents command duplicates

### 🎨 Modern Dashboard UI

- **Side Panel Navigation**: Dedicated views for:
  - 🏠 **Dashboard**: Command execution, project overview, services, recent commands
  - 🔌 **Plugins**: MCP server management and marketplace
  - 🧩 **Extensions**: Custom widgets, workflows, and integrations
  - 📁 **Workspace**: Grid view of all repositories with git status
  - 📋 **Logs**: Full-screen real-time log viewer
  - ⚙️ **Settings**: NLP providers, theme, configuration
- **Compact Design**: 60-70% space reduction with header-only cards and badge-based info
- **Responsive Grid Layout**: Optimized for desktop (3-4 columns), tablet (2 columns), mobile (1 column)
- **Color-coded Status Indicators**:
  - Repository status: 🟢 Clean | 🟡 Changes | 🔵 Ahead | 🔴 Behind
  - Service status: 🟢 Running | 🔴 Stopped | 🟡 Starting
- **Real-time WebSocket Updates**: Live command output, service status, and log streaming
- **Dark/Light Theme**: System preference detection with manual override
- **Interactive Tour Guide**: Step-by-step onboarding with element highlighting (react-joyride)

### 🔌 Plugin System

- **Core Plugins Built-in**:
  - **GitHub**: Repository operations, issues, PRs, search
  - **Slack**: Message posting, file uploads, channel management
  - **Filesystem**: Read, write, search, directory operations
  - **Git**: Status, diff, commit, branch operations
  - **Postgres**: Database queries and management
  - **Puppeteer**: Browser automation and testing
- **Plugin Marketplace**: Browse and install additional MCP servers
- **Install from Git**: Support for custom plugin repositories
- **Interactive Plugin Creator**: Template-based scaffolding:
  - **Basic Template**: Simple tool definitions
  - **Advanced Template**: Full MCP server with async handlers
  - Interactive wizard for beginners
  - Manual scaffolding for power users
- **Granular Tool Control**: Enable/disable individual plugin tools
- **Automatic Dependency Management**: Handles npm/pip installations

### 🧩 Extension System

- **Custom Widgets**: React components for dashboard panels
  - Props: `state`, `sendMessage`, `theme`, `config`
  - Dynamic loading with React.lazy
  - Permission-based access control
- **Workflows**: YAML-based multi-step command sequences
  - Parameter prompts and validation
  - Conditional execution
  - Error handling and rollback
  - Integration hooks (Slack notifications, etc.)
- **External Integrations**: Connect services for automation
  - **Slack**: Post command results, approval requests
  - **GitHub**: Auto-create issues from failures, link commits
  - **Jira**: Create tickets, update status
- **Interactive Extension Creator**: Template wizard
  - Widget scaffolding with TypeScript types
  - Workflow YAML generator
  - Integration boilerplate
  - Power user manual mode

### 📁 Workspace Management

- **Compact Grid View**: Display 12 repositories per page
- **Search & Filter**: Quick repository lookup for large workspaces
- **One-Click Project Switching**: Change active project instantly
- **Real-time Git Status**: Automatic status updates every 30s
- **Repository Summary**: Shows total repos, modified, ahead, behind counts

### 📋 Logs & Monitoring

- **Dedicated Logs Page**: Full-screen log viewer
- **Real-time Streaming**: Live command and service output
- **Log Level Filtering**: INFO, WARN, ERROR categories
- **Search & Export**: Find specific log entries
- **Source Filtering**: Filter by command, service, or system

### 💾 Additional Interfaces

- **macOS Menubar App**: Quick access to commands and services
- **Terminal Log Tailing**: Real-time log monitoring in terminal
- **macOS Notifications**: Desktop alerts for command completion

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Mac Dev Box                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐     ┌────────────────────────────────────────┐│
│  │ Cursor +    │────▶│  MCP Server (Python) - Port stdio      ││
│  │ Claude Code │     │  ├─ Shell executor w/ guardrails       ││
│  └─────────────┘     │  ├─ Project auto-detect                ││
│                      │  ├─ venv management                    ││
│                      │  ├─ Git profile validation             ││
│                      │  ├─ Service lifecycle management       ││
│                      │  └─ WebSocket connection management    ││
│                      └──────────┬─────────────────────────────┘│
│                                 │                               │
│         ┌───────────────────────┼─────────────────────┐        │
│         │                       │                     │        │
│         ▼                       ▼                     ▼        │
│  ┌─────────────────┐   ┌──────────────┐    ┌─────────────┐   │
│  │ Web Dashboard   │   │ Menubar App  │    │  Terminal   │   │
│  │ :3333           │   │   (rumps)    │    │    Tail     │   │
│  │                 │   └──────┬───────┘    └─────────────┘   │
│  │ ┌─────────────┐ │          │                               │
│  │ │  Sidebar    │ │          ▼                               │
│  │ │  ├Dashboard │ │   ┌──────────────┐                      │
│  │ │  ├Plugins   │ │   │macOS Notify  │                      │
│  │ │  ├Extension │ │   └──────────────┘                      │
│  │ │  ├Workspace │ │                                          │
│  │ │  ├Logs      │ │   ┌──────────────────────────────────┐ │
│  │ │  └Settings  │ │   │  WebSocket Server                │ │
│  │ └─────────────┘ │   │  :8766                           │ │
│  │                 │◀──│  ├─ Client connection tracking    │ │
│  │ Main Content    │   │  ├─ Dead connection cleanup      │ │
│  │ ┌─────────────┐ │   │  ├─ Real-time state broadcast   │ │
│  │ │Grid Layout  │ │   │  └─ Ping/pong heartbeat         │ │
│  │ │Responsive   │ │   └──────────────────────────────────┘ │
│  │ └─────────────┘ │                                          │
│  └─────────────────┘                                          │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Plugin & Extension System                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │  │
│  │  │Core Plugins  │  │Add'l Plugins │  │ Extensions  │  │  │
│  │  │ ├GitHub      │  │ ├Jira        │  │ ├Widgets    │  │  │
│  │  │ ├Slack       │  │ ├Docker      │  │ ├Workflows  │  │  │
│  │  │ ├Filesystem  │  │ ├Database    │  │ └Integration│  │  │
│  │  │ ├Git         │  │ └Custom...   │  │             │  │  │
│  │  │ ├Postgres    │  └──────────────┘  └─────────────┘  │  │
│  │  │ └Puppeteer   │                                      │  │
│  │  └──────────────┘                                      │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
1. Claude Code/Cursor ─MCP Protocol─▶ MCP Server
2. MCP Server ◀─WebSocket (port 8766)─▶ Dashboard/Menubar/Terminal
3. Dashboard ◀─HTTP (port 3333)─▶ User Browser
4. Plugins/Extensions ◀─Dynamic Loading─▶ Dashboard
```

## Installation

### 1. Clone and Setup

```bash
cd ~/repos/dev-orchestrator-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -e .

# Install dashboard dependencies
cd dashboard
npm install
cd ..
```

### 2. Configure Claude Code / Cursor

Add to your MCP configuration (`~/.config/claude/mcp.json` or Cursor settings):

```json
{
  "mcpServers": {
    "dev-orchestrator": {
      "command": "/Users/YOUR_USERNAME/repos/dev-orchestrator-mcp/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/YOUR_USERNAME/repos/dev-orchestrator-mcp"
    }
  }
}
```

### 3. Start Services

```bash
# Make launcher executable
chmod +x launch.sh

# Start all services
./launch.sh start

# Or start individually
./launch.sh websocket
./launch.sh dashboard
./launch.sh menubar
```

## Dashboard UI Guide

### First Launch

When you first open the dashboard at `http://localhost:3333`, you'll be greeted with an interactive tour guide that walks you through the main features. You can restart the tour anytime from the Help menu.

### Navigation

The dashboard uses a **collapsible side panel** for navigation:

- 🏠 **Dashboard**: Main view with command input, project overview, running services, and recent commands
- 🔌 **Plugins**: Browse and install MCP server plugins from the marketplace
- 🧩 **Extensions**: Manage custom widgets, workflows, and external integrations
- 📁 **Workspace**: Grid view of all repositories with real-time git status
- 📋 **Logs**: Full-screen log viewer with filtering and search
- ⚙️ **Settings**: Configure NLP providers, theme, and preferences

**Tip**: Click the menu icon to collapse/expand the sidebar for more screen space.

### Command Execution

**Normal Mode** (Direct Shell):
```bash
npm run build
git status
docker ps -a
```

**NLP Mode** (Natural Language):
- "list all folders containing ansible"
- "show me the git status"
- "what processes are using port 8000"

Toggle NLP mode with the switch next to the command input. Configure your preferred NLP provider in Settings:
- **Ollama**: Local, privacy-first (requires Ollama running)
- **OpenAI**: GPT-4 (requires API key)
- **Gemini**: Google's LLM (requires API key)
- **Anthropic**: Claude (requires API key)

### Workspace Panel

The **Workspace** view shows all your repositories in a compact grid:

**Color-coded Git Status**:
- 🟢 **Green border**: Clean, up to date with upstream
- 🟡 **Yellow border**: Uncommitted changes
- 🔵 **Blue border**: Commits ahead of upstream
- 🔴 **Red border**: Behind upstream, needs pull

**Quick Actions**:
- Click any repository card to switch your active project
- Use the search bar to filter repositories by name
- Hover over cards for additional information

### Services Panel

Running services appear in the Dashboard view with:
- Service name and command
- Port number (if applicable)
- Status indicator (🟢 Running | 🔴 Stopped)
- **Stop** button to terminate the service

### Logs Viewer

The **Logs** page provides real-time output from:
- Command executions
- Running services
- System events
- Plugin/extension activity

**Features**:
- Filter by log level: INFO, WARN, ERROR
- Filter by source: command, service, system
- Search for specific text
- Real-time streaming with auto-scroll
- Export logs to file

## Usage

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `detect_project` | Scan directory for project type, venv, git config |
| `run_command` | Execute shell command with guardrails |
| `start_service` | Start backend/frontend/test based on detection |
| `stop_service` | Stop a running service |
| `list_services` | List all managed services |
| `run_tests` | Run project tests (pytest/npm test) |
| `git_status` | Get git status for current project |
| `check_ports` | Check which dev ports are in use |
| `activate_venv` | Get venv activation command |
| `approve_command` | Approve a pending command |
| `reject_command` | Reject a pending command |
| `get_status` | Get full orchestrator status |

### Example Workflow

```
You: Start my FastAPI backend
Claude: [calls detect_project] → Detected aiopsskills-web-ui (fastapi, react)
Claude: [calls start_service backend] → Started uvicorn on port 8000

You: Run the tests
Claude: [calls run_tests] → pytest results...

You: Push to origin
Claude: [calls run_command "git push origin main"]
        ⚠️ This command requires approval: "git push" matches protected pattern
        Waiting for approval...
[You approve via dashboard or menubar]
Claude: → Pushed successfully
```

### Guardrails

**Blocked Commands** (never allowed):
- `rm -rf /`, `rm -rf ~`
- `sudo rm -rf`
- Fork bombs, disk formatting

**Approval Required** (interactive):
- `rm -rf`, `rm -r`
- `git push --force`, `git reset --hard`
- `DROP TABLE`, `DELETE FROM`
- `sudo`, `kill -9`
- `npm publish`, `pip upload`

## Creating Plugins

Dev Orchestrator supports **two types of plugins**:

1. **Core Plugins**: Built into the main repository (GitHub, Slack, Filesystem, Git, Postgres, Puppeteer)
2. **Additional Plugins**: Installed from separate repositories or created by users

### Interactive Plugin Creator

The dashboard includes an **Interactive Plugin Creator** wizard:

1. Navigate to **Plugins** page
2. Click **"Create Plugin"** button
3. Choose your approach:
   - **Interactive Wizard**: Step-by-step guided creation (recommended for beginners)
   - **Manual Scaffolding**: Generate template files for power users

### Interactive Wizard Steps

1. **Plugin Type**:
   - **Basic**: Simple tool definitions with minimal boilerplate
   - **Advanced**: Full MCP server with async handlers, state management

2. **Plugin Metadata**:
   - Name, description, author
   - Version and license
   - Dependencies (npm/pip packages)

3. **Tool Definitions**:
   - Tool name and description
   - Input schema (parameters)
   - Return type
   - Implementation template

4. **Generation**:
   - Creates plugin directory in `~/.dev-orchestrator/plugins/your-plugin/`
   - Generates `mcp_server.json` manifest
   - Creates `server.py` (Python) or `index.js` (Node.js)
   - Sets up `requirements.txt` or `package.json`
   - Includes example tests and README

### Manual Plugin Structure

For power users, create a plugin manually:

```
~/.dev-orchestrator/plugins/my-custom-plugin/
├── mcp_server.json          # Plugin manifest
├── server.py                # MCP server implementation
├── requirements.txt         # Python dependencies
├── README.md               # Documentation
└── tests/                  # Optional tests
    └── test_server.py
```

**Example `mcp_server.json`**:
```json
{
  "name": "my-custom-plugin",
  "version": "1.0.0",
  "description": "My custom MCP plugin",
  "author": "Your Name",
  "entry": "server.py",
  "runtime": "python",
  "dependencies": ["requests", "aiohttp"]
}
```

**Example `server.py`**:
```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-custom-plugin")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="my_tool",
            description="Does something useful",
            inputSchema={
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                },
                "required": ["param"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_tool":
        result = f"Processed: {arguments['param']}"
        return [TextContent(type="text", text=result)]

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

### Publishing Plugins

Share your plugins with the community:

1. Create a GitHub repository: `github.com/your-username/dev-orchestrator-plugin-name`
2. Include `mcp_server.json`, implementation, and README
3. Tag releases with semantic versioning
4. (Optional) Submit to the official plugin marketplace

Users can install your plugin via:
- Dashboard: **Plugins** → **Install from Git** → `https://github.com/your-username/dev-orchestrator-plugin-name`
- Or add to plugin catalog: [plugin-catalog.json](plugin-catalog.json)

## Creating Extensions

Extensions customize the dashboard with **widgets**, **workflows**, and **integrations**.

### Interactive Extension Creator

1. Navigate to **Extensions** page
2. Choose extension type:
   - **Widget**: Custom React dashboard panel
   - **Workflow**: YAML-based command sequence
   - **Integration**: External service connector
3. Select creation mode:
   - **Interactive Wizard**: Guided step-by-step (recommended)
   - **Manual Scaffolding**: Generate template files

### Creating Widgets

**Widgets** are React components that appear as cards on the dashboard.

#### Interactive Widget Wizard

1. **Widget Metadata**:
   - Name, description, author
   - Category (monitoring, tools, analytics, etc.)
   - Icon selection

2. **Widget Configuration**:
   - Grid size (xs, sm, md, lg, xl)
   - Update interval (for real-time data)
   - Permissions required (read-state, execute-commands, read-logs)

3. **Template Selection**:
   - **Basic**: Simple display widget
   - **Interactive**: Widget with buttons and actions
   - **Real-time**: Auto-updating data widget

4. **Generation**: Creates widget in `~/.dev-orchestrator/extensions/widgets/your-widget/`

#### Manual Widget Structure

```
~/.dev-orchestrator/extensions/widgets/my-widget/
├── manifest.json           # Widget configuration
├── Widget.tsx             # React component
├── package.json           # Optional dependencies
└── README.md
```

**Example `manifest.json`**:
```json
{
  "id": "my-widget",
  "name": "My Custom Widget",
  "version": "1.0.0",
  "entry": "Widget.tsx",
  "permissions": ["read-state", "execute-commands"],
  "grid": {
    "defaultSize": { "xs": 12, "md": 6, "lg": 4 }
  },
  "category": "monitoring",
  "updateInterval": 5000
}
```

**Example `Widget.tsx`**:
```typescript
import React from 'react';
import { Card, CardHeader, CardContent, Typography } from '@mui/material';

interface WidgetProps {
  state: any;
  sendMessage: (msg: any) => void;
  theme: any;
  config: Record<string, any>;
}

const MyWidget: React.FC<WidgetProps> = ({ state, sendMessage }) => {
  return (
    <Card>
      <CardHeader title="My Widget" />
      <CardContent>
        <Typography>
          Current Project: {state?.current_project?.name || 'None'}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default MyWidget;
```

### Creating Workflows

**Workflows** are YAML files defining multi-step command sequences.

#### Interactive Workflow Wizard

1. **Workflow Metadata**: Name, description, version
2. **Parameters**: Define user inputs (text, choice, boolean)
3. **Steps**: Add commands with:
   - Command template (supports Jinja2)
   - Working directory
   - Timeout and retry settings
   - Conditional execution
   - Approval requirements
4. **Error Handling**: Define failure and success callbacks
5. **Generation**: Creates YAML in `~/.dev-orchestrator/extensions/workflows/`

#### Manual Workflow Structure

```yaml
# ~/.dev-orchestrator/extensions/workflows/deploy-app.yaml
name: "Deploy Application"
version: "1.0.0"
description: "Build, test, and deploy application"

parameters:
  - name: environment
    type: choice
    choices: ["dev", "staging", "production"]
    default: "dev"

steps:
  - name: "Run tests"
    command: "npm test"
    continue_on_error: false

  - name: "Build application"
    command: "npm run build"

  - name: "Deploy to {{ environment }}"
    command: "npm run deploy:{{ environment }}"
    requires_approval: true

on_success:
  - name: "Notify team"
    plugin: "slack"
    tool: "post_message"
    arguments:
      channel: "#deployments"
      message: "✅ Deployed to {{ environment }}"

on_failure:
  - name: "Notify team"
    plugin: "slack"
    tool: "post_message"
    arguments:
      channel: "#deployments"
      message: "❌ Deployment failed"
```

### Creating Integrations

**Integrations** connect external services (Slack, GitHub, Jira) to receive event notifications.

#### Interactive Integration Wizard

1. **Service Selection**: Slack, GitHub, Jira, or Custom
2. **Authentication**: API keys, OAuth tokens, webhook URLs
3. **Event Subscriptions**: Choose events to trigger:
   - Command completion
   - Command failure
   - Service start/stop
   - Approval required
4. **Generation**: Creates integration config and handler

#### Manual Integration Structure

```python
# ~/.dev-orchestrator/extensions/integrations/my-integration.py
from src.extensions.integrations.base import BaseIntegration

class MyIntegration(BaseIntegration):
    def __init__(self, config):
        super().__init__(config)
        self.webhook_url = config["webhook_url"]

    async def on_command_complete(self, command, result):
        if result["exit_code"] != 0:
            await self.notify_failure(command, result)

    async def notify_failure(self, command, result):
        # Send notification to external service
        pass
```

## Configuration

Edit `~/.dev-orchestrator/config.json`:

```json
{
  "host": "127.0.0.1",
  "dashboard_port": 3333,
  "websocket_port": 8766,
  "guardrails": {
    "allowed_directories": [
      "~/work",
      "~/personal",
      "~/repos"
    ],
    "approval_required_patterns": [
      "rm -rf",
      "git push --force"
    ]
  }
}
```

## Ports

| Service | Port |
|---------|------|
| Dashboard | 3333 |
| WebSocket | 8766 |
| MCP Server | stdio |

## Logs

All logs are stored in `~/.dev-orchestrator/logs/`:
- `websocket.log`
- `dashboard.log`
- `menubar.log`

Tail all logs:
```bash
./launch.sh logs
```

## Development

```bash
# Run tests
pytest

# Run MCP server directly (for debugging)
python -m src.server

# Run dashboard in dev mode
cd dashboard && npm run dev
```

## License

MIT

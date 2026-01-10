# Dev Orchestrator MCP

[![CI](https://github.com/chaos-consultant/dev-orchestrator-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/chaos-consultant/dev-orchestrator-mcp/actions/workflows/ci.yml)

A Mac dev environment orchestration MCP server that enables Claude to run and test your development stack with guardrails and interactive approval.

## Features

- **Full Shell Control with Guardrails**: Execute commands with automatic blocking of dangerous operations
- **Interactive Approval**: Commands matching dangerous patterns require your explicit approval
- **Project Auto-Detection**: Automatically detects FastAPI, React, Python, Node.js projects
- **Virtual Environment Management**: Auto-activates correct venv per project
- **Git Profile Validation**: Ensures correct git user per project directory
- **Multi-Interface Visibility**:
  - Web Dashboard (Material-UI React)
    - Manual command execution
    - Dark/light mode toggle
    - Log filtering by level
    - Command history with detail view
    - Real-time reconnection indicator
  - macOS Menubar App
  - Terminal Log Tailing
  - macOS Notifications

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Mac Dev Box                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐     ┌──────────────────────────────────┐  │
│  │ Cursor +    │────▶│  MCP Server (Python)             │  │
│  │ Claude Code │     │  - Shell executor w/ guardrails  │  │
│  └─────────────┘     │  - Project auto-detect           │  │
│                      │  - venv management               │  │
│                      │  - Git profile validation        │  │
│                      └──────────────┬───────────────────┘  │
│                                     │                       │
│         ┌───────────────────────────┼───────────────────┐  │
│         │                           │                   │  │
│         ▼                           ▼                   ▼  │
│  ┌─────────────┐          ┌──────────────┐    ┌─────────┐ │
│  │ Web Dash    │          │ Menubar App  │    │Terminal │ │
│  │ :3333       │          │ (rumps)      │    │ Tail    │ │
│  └─────────────┘          └──────────────┘    └─────────┘ │
│                                  │                        │
│                                  ▼                        │
│                           ┌──────────────┐               │
│                           │ macOS Notify │               │
│                           └──────────────┘               │
└─────────────────────────────────────────────────────────────┘
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

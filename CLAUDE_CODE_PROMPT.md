# Dev Orchestrator MCP - Implementation Continuation Prompt

## Project Context

I'm building a Mac dev environment orchestration MCP server located at `~/repos/dev-orchestrator-mcp`. The initial scaffolding is complete but needs testing, debugging, and feature completion.

## What's Already Built

```
dev-orchestrator-mcp/
├── src/
│   ├── __init__.py
│   ├── config.py          # Guardrails, settings, ProjectProfile model
│   ├── detector.py        # Project auto-detection (pyproject.toml, package.json, git, venv)
│   ├── executor.py        # Shell execution with guardrails + approval workflow
│   ├── notifications.py   # macOS notifications via osascript
│   ├── state.py           # State management + WebSocket broadcasting
│   ├── server.py          # Main MCP server with tools
│   ├── websocket_server.py# WebSocket server for dashboard
│   └── menubar_app.py     # rumps-based macOS menubar app
├── dashboard/
│   ├── src/
│   │   ├── App.tsx        # PatternFly React dashboard
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.ts
├── launch.sh              # Combined launcher script
├── pyproject.toml
└── README.md
```

## Core Architecture

- **MCP Server** (stdio): Exposes tools to Claude Code for shell execution, project detection, service management
- **WebSocket Server** (port 8766): Broadcasts state updates to dashboard and menubar
- **Dashboard** (port 3333): React + PatternFly web UI showing project, services, logs, pending approvals
- **Menubar App**: Python rumps app showing status, pending approvals, quick actions
- **Notifications**: macOS notification center alerts for approvals, service start/stop

## Key Features Implemented

1. **Guardrails**: Blocklist (always denied) + approval-required patterns (interactive)
2. **Project Auto-Detection**: Scans for pyproject.toml, package.json, .git, venv
3. **Interactive Approval**: Dangerous commands wait for user approval via dashboard/menubar
4. **Service Management**: Start/stop background processes, track ports
5. **State Broadcasting**: WebSocket pushes updates to all connected clients

## What Needs to Be Done

### Phase 1: Testing & Bug Fixes (Priority)
1. Test MCP server starts correctly via Cursor
2. Test each MCP tool works (detect_project, run_command, start_service, etc.)
3. Test WebSocket server connects and broadcasts
4. Test dashboard receives and displays state
5. Test menubar app connects and updates
6. Test approval workflow end-to-end (command triggers approval → user approves in dashboard → command executes)
7. Fix any import errors, missing dependencies, or runtime issues

### Phase 2: Dashboard Enhancements
1. Add "Stop Service" button functionality (currently just UI, needs WebSocket message)
2. Add manual command input field
3. Add project directory selector/browser
4. Add service health checks (ping endpoints)
5. Add command output viewer (expandable stdout/stderr)
6. Improve log filtering (by level, source)
7. Add dark/light mode toggle
8. Add connection retry indicator

### Phase 3: Menubar App Completion
1. Test WebSocket connection stability
2. Add "Open in Cursor" action for current project
3. Add quick-start buttons for common commands
4. Add submenu for each running service with stop option
5. Handle macOS permissions gracefully

### Phase 4: Robustness
1. Add proper async error handling throughout
2. Add reconnection logic for WebSocket clients
3. Add process cleanup on server shutdown
4. Add state persistence (save/restore across restarts)
5. Add health check endpoint for MCP server
6. Add timeout handling for stuck commands

### Phase 5: Testing Suite
1. Create pytest tests for detector.py
2. Create pytest tests for executor.py guardrails
3. Create pytest tests for config validation
4. Create integration test for approval workflow

### Phase 6: Documentation & Polish
1. Update README with actual usage examples
2. Add inline code comments
3. Create troubleshooting guide
4. Add configuration examples for different project types

## Technical Requirements

- Python 3.11+
- Node.js 18+
- PatternFly 6 for dashboard
- rumps for menubar
- MCP SDK for server
- WebSockets for real-time updates

## My Workflow Context

- I use Cursor with Claude Code
- I maintain separate git profiles for work vs personal
- Projects are typically in ~/work/ or ~/personal/ or ~/repos/
- I work on FastAPI + React + Python projects
- I want Claude to be able to autonomously run/test my dev stack with safety guardrails

## Instructions

1. Start by verifying the project structure and checking for any obvious issues
2. Create the venv if not exists and install dependencies
3. Test each component individually before integration testing
4. Fix bugs as you find them
5. Implement missing features in priority order
6. Keep me informed of progress and any decisions you make
7. Ask for clarification if requirements are ambiguous

## Commands Reference

```bash
# Setup
cd ~/repos/dev-orchestrator-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cd dashboard && npm install && cd ..
chmod +x launch.sh

# Run services
./launch.sh start      # Start all
./launch.sh stop       # Stop all
./launch.sh status     # Check status
./launch.sh logs       # Tail logs

# Individual components
python -m src.server              # MCP server (stdio)
python -m src.websocket_server    # WebSocket server
python -m src.menubar_app         # Menubar app
cd dashboard && npm run dev       # Dashboard
```

## Begin

Start by reading the existing source files to understand the current implementation, then proceed with Phase 1 testing. Report what works and what needs fixing.

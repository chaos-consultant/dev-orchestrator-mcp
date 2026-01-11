# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-11

### Added

#### Plugin System
- **Plugin Marketplace:** Curated catalog with 11 plugins (8 Anthropic Official + 3 Dev Orchestrator)
  - GitHub MCP, Filesystem, Postgres, Puppeteer, Slack, Memory, Brave Search, Fetch
  - Dev Orchestrator: Jira Integration, Docker Manager, Database Query Runner
- **Plugin Management:** Install, uninstall, enable/disable plugins from dashboard
- **Tool Management:** Toggle individual tools within plugins
- **Plugin Creator:** 4-step wizard to scaffold custom MCP plugins
  - Template types: Basic and Advanced
  - Runtimes: Python and Node.js
  - Multi-tool support with descriptions
  - Auto-generates: server.py, mcp_server.json, requirements.txt, README.md

#### Extension System
- **Widget Creator:** Custom React dashboard components
  - Templates: Basic (display), Interactive (with actions), Realtime (auto-updating)
  - Categories: Monitoring, Productivity, Analytics, Utility
- **Workflow Creator:** YAML-based multi-step command sequences
  - Jinja2 templating for dynamic parameters
  - Approval gates for critical operations
  - Conditional execution and error handling
- **Integration Creator:** External service connections
  - Event handlers for command lifecycle
  - OAuth2 and webhook support
  - Extensible architecture for custom services

#### Official Plugins
- **Jira Integration Plugin** (v1.0.0)
  - 8 tools: search_issues, get_issue, create_issue, update_issue, add_comment, transition_issue, get_transitions, list_projects
  - JQL (Jira Query Language) support
  - Full CRUD operations for issues
  - Environment variable configuration (JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN)
  - Comprehensive documentation with examples and troubleshooting

#### Database & State Management
- **SQLite Foundation:** Replaced JSON with async SQLAlchemy ORM
  - 10 database tables: commands, saved_commands, tags, command_tags, projects, project_sessions, workflows, workflow_steps, services, logs
  - FTS5 full-text search for command history
  - WAL mode for better concurrency
  - Repository pattern for data access
  - Alembic migrations
- **Data Migration:** Automatic JSON to SQLite migration script
- **Project Sessions:** Track time spent per project
- **Enhanced Logging:** Structured logging with source and level filtering

#### UI/UX Redesign
- **Side Panel Navigation:** Persistent drawer with 6 main sections
  - Dashboard, Plugins, Extensions, Workspace, Logs, Settings
  - Collapsible with icon-only mode
  - Active route highlighting
  - Responsive on mobile (temporary drawer)
- **Compact Design:** 60-70% space reduction in panels
  - Streamlined command input with inline NLP toggle
  - Color-coded git status borders (green/yellow/red)
  - Reduced visual noise and improved hierarchy
- **Interactive Tour Guide:** React Joyride integration
  - Multi-tour support (Basic, Plugin, Extension)
  - Step-by-step element highlighting
  - Progress tracking and completion persistence
  - Skip and restart capabilities
- **NLP Settings UI:** Multi-provider configuration dialog
  - Providers: Ollama (local), OpenAI, Google Gemini, Anthropic Claude
  - Model selection per provider
  - API key management
  - Test connection functionality
  - Provider status indicators

#### Template System
- **PluginCreator:** Generate MCP server scaffolding
  - Basic template: Simple tool definitions
  - Advanced template: State management and resources
  - Python: Async handlers with mcp.server
  - Node.js: ES6 modules with @modelcontextprotocol/sdk
- **ExtensionCreator:** Generate dashboard extensions
  - Widget templates with TypeScript and React
  - Workflow templates with YAML and Jinja2
  - Integration templates with Python event handlers
- **4 New MCP Tools:** create_plugin, create_widget, create_workflow, create_integration

#### Documentation
- **Plugin Catalog:** Comprehensive plugin metadata (plugin-catalog.json)
- **Test Documentation:** Plugin creator test results with 6 scenarios
- **API Documentation:** Updated tool schemas and examples

### Changed
- **Dashboard Architecture:** Single-page app with view routing
- **Command History:** Enhanced with full-text search capability
- **Project Switching:** Improved workspace panel with git status
- **WebSocket Protocol:** Extended message types for plugins and extensions
- **Configuration:** Centralized in ~/.dev-orchestrator/ directory

### Fixed
- **Navigation:** React Hook violations causing blank pages
- **WebSocket:** Duplicate command execution on reconnect
- **TypeScript:** Compilation errors in plugin and extension creators
- **Parameter Validation:** Aligned UI forms with backend template requirements
- **Dashboard Loading:** MUI ThemeProvider and CSS cleanup

### Security
- **Plugin Sandboxing:** Isolated plugin execution environments
- **API Token Storage:** Secure environment variable configuration
- **Approval System:** User confirmation for destructive operations

## [Unreleased]

### Added
- Natural Language Processing integration using Ollama:
  - AI-powered command translation from natural language to shell commands
  - Intent classification (shell command vs MCP tool detection)
  - Toggle switch in dashboard to enable/disable NLP mode
  - Visual indicator (brain icon) when NLP mode is active
  - Confidence scoring and reasoning for translated commands
  - Graceful fallback to shell execution if Ollama unavailable
- Material-UI dashboard with enhanced features:
  - Manual command input field with keyboard shortcut (Enter to execute)
  - Dark/light mode toggle with persistent theme
  - Log filtering by level (All, Info, Warning, Error)
  - Command history with clickable items for detailed view
  - Reconnection indicator showing attempt count
  - Command detail dialog displaying full information
- New `nlp_service.py` module with OllamaNLPService class
- httpx dependency for Ollama API integration

### Changed
- Converted dashboard from PatternFly to Material-UI
- Updated connection status to show reconnection attempts
- Improved command history with interactive list items
- Enhanced log display with filtering capabilities
- WebSocket server now supports NLP translation before command execution
- Command input placeholder changes based on NLP toggle state

### Fixed
- WebSocket server missing run_command handler (dashboard commands now execute properly)

## [0.1.0] - 2026-01-10

### Added
- Initial implementation of dev-orchestrator-mcp
- MCP server with 16 tools for dev orchestration
- Shell executor with guardrails and approval system
- Project auto-detection (FastAPI, React, Python, Node.js)
- WebSocket server for real-time communication (port 8766)
- PatternFly 6 React dashboard (port 3333)
- macOS menubar app using rumps
- Launch script for service management
- Comprehensive README with installation and usage instructions

### Fixed
- Syntax error in check_ports command (f-string escaping issue)

[Unreleased]: https://github.com/chaos-consultant/dev-orchestrator-mcp/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/chaos-consultant/dev-orchestrator-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/chaos-consultant/dev-orchestrator-mcp/releases/tag/v0.1.0

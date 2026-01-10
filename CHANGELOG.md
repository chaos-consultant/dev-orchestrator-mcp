# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[Unreleased]: https://github.com/chaos-consultant/dev-orchestrator-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/chaos-consultant/dev-orchestrator-mcp/releases/tag/v0.1.0

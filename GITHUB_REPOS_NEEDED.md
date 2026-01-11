# GitHub Repositories Needed for Dev Orchestrator

## Overview

Dev Orchestrator now has a comprehensive plugin and extension system with interactive template creation. To complete the ecosystem, separate GitHub repositories should be created for community plugins and extensions.

## Repository Structure

### 1. Main Repository (This Repo)
**Repository:** `chaos-consultant/dev-orchestrator-mcp`

**Contains:**
- Core MCP server
- Dashboard UI
- Built-in core plugins:
  - GitHub MCP server
  - Slack MCP server
  - Filesystem MCP server
  - Git MCP server
  - Postgres MCP server
  - Puppeteer MCP server
- Template creation system
- Documentation

### 2. Additional Plugins Repository (TO BE CREATED)
**Repository:** `chaos-consultant/dev-orchestrator-plugins`

**Purpose:** Community and official additional plugins that extend functionality

**Initial Plugins to Include:**
1. **Jira Plugin** - Issue tracking and workflow management
2. **Docker Plugin** - Container management
3. **Database Query Plugin** - Multi-database query execution
4. **Notion Plugin** - Note-taking and documentation
5. **Calendar Plugin** - Schedule management

**Structure:**
```
dev-orchestrator-plugins/
├── README.md
├── jira/
│   ├── mcp_server.json
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── docker/
│   ├── mcp_server.json
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── database-query/
│   ├── mcp_server.json
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
└── ... (more plugins)
```

**README.md should include:**
- Overview of available plugins
- Installation instructions
- Contributing guidelines
- Plugin submission process

### 3. Extensions Repository (TO BE CREATED)
**Repository:** `chaos-consultant/dev-orchestrator-extensions`

**Purpose:** Community widgets, workflows, and integrations

**Initial Content:**
1. **Example Widgets:**
   - Service Uptime Widget
   - Commit History Widget
   - Resource Monitor Widget
2. **Example Workflows:**
   - Deploy to Production workflow
   - Backup Database workflow
   - Run Test Suite workflow
3. **Example Integrations:**
   - Slack notifications template
   - GitHub issue creator template
   - Jira ticket creator template

**Structure:**
```
dev-orchestrator-extensions/
├── README.md
├── widgets/
│   ├── service-uptime/
│   │   ├── manifest.json
│   │   ├── Widget.tsx
│   │   └── README.md
│   ├── commit-history/
│   └── resource-monitor/
├── workflows/
│   ├── deploy-production.yaml
│   ├── backup-database.yaml
│   └── run-tests.yaml
├── integrations/
│   ├── slack-notifier/
│   ├── github-issue-creator/
│   └── jira-ticket-creator/
└── CONTRIBUTING.md
```

## How to Create the Repositories

### Option 1: Using GitHub CLI (gh)

```bash
# Create plugins repository
gh repo create chaos-consultant/dev-orchestrator-plugins \\
  --public \\
  --description "Official and community plugins for Dev Orchestrator MCP" \\
  --gitignore Python \\
  --license MIT

# Create extensions repository
gh repo create chaos-consultant/dev-orchestrator-extensions \\
  --public \\
  --description "Widgets, workflows, and integrations for Dev Orchestrator" \\
  --gitignore Node \\
  --license MIT
```

### Option 2: Using GitHub Web Interface

1. Go to https://github.com/new
2. Create `dev-orchestrator-plugins`:
   - **Name:** `dev-orchestrator-plugins`
   - **Description:** "Official and community plugins for Dev Orchestrator MCP"
   - **Public repository**
   - **Add .gitignore:** Python
   - **Add license:** MIT
3. Create `dev-orchestrator-extensions`:
   - **Name:** `dev-orchestrator-extensions`
   - **Description:** "Widgets, workflows, and integrations for Dev Orchestrator"
   - **Public repository**
   - **Add .gitignore:** Node
   - **Add license:** MIT

## After Creating Repositories

### 1. Update plugin-catalog.json in Main Repo

Replace placeholder URLs with actual GitHub URLs:

```json
{
  "plugins": [
    {
      "id": "jira",
      "name": "Jira",
      "description": "Jira issue tracking and workflow management",
      "git_url": "https://github.com/chaos-consultant/dev-orchestrator-plugins.git#jira",
      "type": "additional"
    },
    {
      "id": "docker",
      "name": "Docker",
      "description": "Docker container management",
      "git_url": "https://github.com/chaos-consultant/dev-orchestrator-plugins.git#docker",
      "type": "additional"
    }
  ]
}
```

### 2. Clone and Initialize the New Repositories

```bash
# Clone plugins repo
git clone git@github.com:chaos-consultant/dev-orchestrator-plugins.git
cd dev-orchestrator-plugins

# Create initial README
cat > README.md << 'EOF'
# Dev Orchestrator Plugins

Official and community plugins for [Dev Orchestrator MCP](https://github.com/chaos-consultant/dev-orchestrator-mcp).

## Available Plugins

(Plugin list here)

## Installation

Install plugins directly from the Dev Orchestrator dashboard or via:

\`\`\`bash
dev-orchestrator install-plugin <plugin-name>
\`\`\`

## Creating Your Own Plugin

See the [Plugin Development Guide](https://github.com/chaos-consultant/dev-orchestrator-mcp#creating-plugins) in the main repository.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
EOF

# Commit and push
git add .
git commit -m "Initial commit: README"
git push origin main
```

Repeat similar process for extensions repository.

### 3. Add Topics/Tags to Repositories

Add these topics to both repositories for discoverability:
- `mcp-server`
- `model-context-protocol`
- `claude-code`
- `dev-tools`
- `plugins` (for plugins repo)
- `extensions` (for extensions repo)

## Benefits of This Structure

1. **Separation of Concerns**: Core functionality separate from community contributions
2. **Easier Maintenance**: Plugin/extension updates don't require main repo releases
3. **Community Contributions**: Users can submit PRs to plugins/extensions repos
4. **Version Control**: Each plugin/extension can have independent versioning
5. **Marketplace Growth**: Easier to grow the ecosystem with external contributions

## Next Steps

1. Create both repositories on GitHub
2. Initialize with basic structure and README files
3. Update plugin-catalog.json with real URLs
4. Create initial example plugins and extensions
5. Write CONTRIBUTING.md guides for both repos
6. Announce repositories to the community

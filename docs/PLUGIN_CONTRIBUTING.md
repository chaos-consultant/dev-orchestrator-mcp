# Contributing Plugins to Dev Orchestrator

Thank you for your interest in contributing MCP server plugins to the Dev Orchestrator ecosystem!

## Overview

The Dev Orchestrator plugin marketplace allows developers to discover and install MCP (Model Context Protocol) servers. We welcome community contributions that extend the platform's capabilities.

## Plugin Verification Levels

Plugins in the marketplace are organized by trust level:

| Level | Badge | Description |
|-------|-------|-------------|
| **Anthropic Official** | Purple | Maintained and security-audited by Anthropic |
| **Dev Orchestrator Official** | Blue | Built and maintained by Dev Orchestrator team |
| **Verified Community** | Green | Security reviewed and approved by our team |
| **Community** | Gray | Community contributions (use with caution) |

## Prerequisites

Before submitting a plugin, ensure you have:

- ✅ A working MCP server implementation
- ✅ Published to a public Git repository (GitHub, GitLab, etc.)
- ✅ Clear documentation in a README.md
- ✅ `mcp_server.json` or `package.json` manifest file
- ✅ Specified all dependencies and environment variables
- ✅ Tested the plugin with Dev Orchestrator

## Submission Process

### Option 1: Quick Add (For Testing)

Add your plugin directly to your local catalog for testing:

1. **Edit your local catalog**:
```bash
# Edit the catalog file
nano ~/repos/dev-orchestrator-mcp/plugin-catalog.json
```

2. **Add your plugin entry**:
```json
{
  "id": "your-plugin-id",
  "name": "Your Plugin Name",
  "description": "Brief description of what your plugin does",
  "author": "Your Name or Organization",
  "author_url": "https://github.com/your-username",
  "category": "integration",
  "git_url": "https://github.com/your-username/your-plugin.git",
  "subdirectory": "",
  "version": "1.0.0",
  "mcp_version": "1.0",
  "verified": false,
  "verification_level": "community",
  "tools": [
    "tool_name_1",
    "tool_name_2"
  ],
  "dependencies": {
    "python": ">=3.11",
    "pip": ["required-package>=1.0.0"]
  },
  "required_env": [
    "API_KEY",
    "API_SECRET"
  ],
  "documentation_url": "https://github.com/your-username/your-plugin/blob/main/README.md",
  "downloads": 0,
  "rating": 0,
  "security_notes": "Describe what permissions this plugin needs"
}
```

3. **Copy to public directory**:
```bash
cp plugin-catalog.json dashboard/public/plugin-catalog.json
```

4. **Refresh the marketplace** in your browser to see your plugin

### Option 2: Submit to Official Catalog (For Public Release)

To have your plugin included in the official Dev Orchestrator catalog:

1. **Fork the repository**:
```bash
git clone https://github.com/your-org/dev-orchestrator-mcp.git
cd dev-orchestrator-mcp
```

2. **Add your plugin to the catalog**:
Edit `plugin-catalog.json` and add your entry in the appropriate section:
- Community plugins should go in the `plugins` array
- Set `verification_level` to `"community"`
- Set `verified` to `false`

3. **Create a pull request**:
```bash
git checkout -b add-plugin-your-plugin-name
git add plugin-catalog.json
git commit -m "Add plugin: Your Plugin Name"
git push origin add-plugin-your-plugin-name
```

4. **Fill out the PR template**:
   - Plugin name and description
   - Link to plugin repository
   - List of tools provided
   - Required permissions/environment variables
   - Test results and screenshots
   - Link to security documentation

5. **Wait for review**:
   - Our team will review your submission
   - We may request changes or security clarifications
   - Once approved, your plugin will be merged

## Plugin Manifest Requirements

Your plugin must include one of the following manifest files:

### mcp_server.json (Python)
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": "Your Name",
  "mcp_version": "1.0",
  "tools": [
    "tool_name_1",
    "tool_name_2"
  ],
  "entry_point": "server.py",
  "dependencies": {
    "python": ">=3.11",
    "pip": [
      "requests>=2.31.0",
      "pydantic>=2.0.0"
    ]
  },
  "required_env": [
    "API_KEY",
    "API_SECRET"
  ]
}
```

### package.json (Node.js)
```json
{
  "name": "my-mcp-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0"
  },
  "engines": {
    "node": ">=18.0.0"
  },
  "mcpServer": {
    "tools": ["tool1", "tool2"],
    "requiredEnv": ["API_KEY"]
  }
}
```

## Plugin Categories

Choose the most appropriate category for your plugin:

- **version-control**: Git, GitHub, GitLab, Bitbucket
- **integration**: Jira, Slack, Teams, external services
- **communication**: Chat, notifications, messaging
- **infrastructure**: Docker, Kubernetes, cloud providers
- **database**: SQL, NoSQL, database operations
- **web**: HTTP clients, browsers, web scraping
- **filesystem**: File operations, search, management
- **development**: Build tools, testing, CI/CD

## Security Guidelines

### Required Disclosures

Your plugin submission **must** include:

1. **Permissions Required**:
   - File system access
   - Network access
   - Environment variables
   - System commands

2. **Security Notes**:
   - Describe what the plugin can access
   - Explain why permissions are needed
   - Note any potential risks

3. **Environment Variables**:
   - List all required API keys/tokens
   - Document where to obtain them
   - Explain what they're used for

### Example Security Notes

```
✅ Good:
"Requires GITHUB_TOKEN for API access. Read-only access to repositories.
Makes HTTPS requests to api.github.com only."

❌ Bad:
"Needs some environment variables."
```

### Security Review Checklist

Before submitting, verify:

- [ ] No hardcoded credentials in source code
- [ ] All external requests use HTTPS
- [ ] Input validation for all user-provided data
- [ ] Error messages don't leak sensitive information
- [ ] Dependencies are up-to-date and secure
- [ ] README includes security considerations
- [ ] Permissions requested are minimal and justified

## Documentation Requirements

Your plugin repository must include:

### README.md

```markdown
# Your Plugin Name

Brief description of what the plugin does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
# Installation via Dev Orchestrator marketplace
1. Open Dev Orchestrator dashboard
2. Click "Plugins" → "Browse Marketplace"
3. Search for "Your Plugin Name"
4. Click "Install"
```

## Configuration

Required environment variables:
- `API_KEY`: Your API key from [service.com](https://service.com/api-keys)
- `API_SECRET`: Your API secret

## Tools Provided

### tool_name_1
Description of what this tool does.

**Parameters:**
- `param1` (string): Description
- `param2` (number): Description

**Example:**
```json
{
  "name": "tool_name_1",
  "arguments": {
    "param1": "value",
    "param2": 123
  }
}
```

## Security

This plugin requires:
- ⚠️ Network access to api.example.com
- ✅ Read-only access to configuration files

## Development

```bash
# Clone repository
git clone https://github.com/your-username/your-plugin.git
cd your-plugin

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## License

MIT License
```

## Example Plugins

### Simple Example: PatternFly MCP Server

Here's how to add the PatternFly MCP server to the catalog:

```json
{
  "id": "community-patternfly",
  "name": "PatternFly Components",
  "description": "Access PatternFly design system components, documentation, and code examples for building React UIs.",
  "author": "Community Contributor",
  "author_url": "https://github.com/contributor",
  "category": "development",
  "git_url": "https://github.com/patternfly/patternfly-mcp.git",
  "subdirectory": "",
  "version": "1.0.0",
  "mcp_version": "1.0",
  "verified": false,
  "verification_level": "community",
  "tools": [
    "search_components",
    "get_component_docs",
    "get_code_examples"
  ],
  "dependencies": {
    "node": ">=18.0.0",
    "npm": ["@modelcontextprotocol/sdk"]
  },
  "required_env": [],
  "documentation_url": "https://github.com/patternfly/patternfly-mcp/blob/main/README.md",
  "downloads": 0,
  "rating": 0,
  "security_notes": "Read-only access to PatternFly documentation. No external API calls."
}
```

### Steps to Add PatternFly Plugin:

1. **Create the plugin repository** (if it doesn't exist):
```bash
mkdir patternfly-mcp
cd patternfly-mcp
npm init -y
npm install @modelcontextprotocol/sdk
```

2. **Implement the MCP server** with tools for:
   - Searching PatternFly components
   - Getting component documentation
   - Retrieving code examples

3. **Test locally** with Dev Orchestrator:
```bash
# In Dev Orchestrator dashboard
Plugins → Install → file:///path/to/patternfly-mcp
```

4. **Add to catalog** following the submission process above

## Community Plugin Guidelines

### Do's ✅

- Provide clear, comprehensive documentation
- Include examples and usage instructions
- Test thoroughly before submitting
- Keep dependencies minimal and up-to-date
- Respond to issues and feedback promptly
- Follow MCP protocol specifications
- Use semantic versioning

### Don'ts ❌

- Don't request excessive permissions
- Don't include analytics/tracking without disclosure
- Don't hardcode credentials
- Don't make breaking changes without version bump
- Don't include malicious code or backdoors
- Don't violate third-party service ToS
- Don't submit untested plugins

## Getting Help

- **Questions**: Open a discussion on GitHub
- **Bugs**: File an issue in the plugin repository
- **Security Issues**: Email security@your-org.com
- **General Help**: Join our Discord/Slack community

## Verification Process

To become a **Verified Community** plugin:

1. Submit your plugin as described above
2. Pass security review by our team
3. Demonstrate active maintenance (3+ months)
4. Have positive user feedback
5. Include comprehensive tests
6. Follow all guidelines in this document

Verified plugins get:
- ⭐ Green "Verified Community" badge
- Featured placement in marketplace
- Faster support and issue resolution
- Consideration for "Official" status

## License

By submitting a plugin to the Dev Orchestrator marketplace, you agree that:
- Your plugin is open source (MIT, Apache 2.0, or similar)
- You have the rights to distribute all included code
- Users can freely install and use the plugin
- You'll maintain the plugin and respond to security issues

---

**Ready to contribute?** Start by forking the repository and adding your plugin to `plugin-catalog.json`!

Questions? Open an issue or reach out to the maintainers.

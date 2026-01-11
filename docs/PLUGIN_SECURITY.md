# Plugin Security & Safety Guide

## Official MCP Servers from Anthropic

### Overview

Anthropic maintains a collection of **official, verified MCP servers** that are:

✅ **Actively Maintained** - Regular updates and security patches
✅ **Security Audited** - Reviewed by Anthropic's security team
✅ **Open Source** - Full source code available for inspection
✅ **Well Documented** - Comprehensive usage guides and examples
✅ **Community Tested** - Used by thousands of developers

**Official Repository**: https://github.com/modelcontextprotocol/servers

### Security Features

1. **Code Review Process**
   - All changes reviewed by Anthropic engineers
   - Security-focused code reviews
   - Automated security scanning (Dependabot, CodeQL)

2. **Dependency Management**
   - Regular dependency updates
   - Known vulnerability scanning
   - Minimal dependency footprint

3. **Sandboxing & Isolation**
   - Each server runs in its own process
   - Limited file system access
   - No shared state between servers

4. **Authentication & Authorization**
   - Secure credential management
   - OAuth2 support where applicable
   - No plaintext password storage

5. **Network Security**
   - HTTPS for all external requests
   - Certificate validation
   - Rate limiting built-in

### Available Official Servers

| Server | Purpose | Security Level | Use Case |
|--------|---------|---------------|----------|
| **filesystem** | File operations | ⚠️ High Access | Local file management |
| **github** | GitHub API integration | ✅ API Token | Repository management |
| **postgres** | PostgreSQL queries | ⚠️ Database Access | Database operations |
| **puppeteer** | Browser automation | ⚠️ Web Access | Testing & scraping |
| **slack** | Slack integration | ✅ API Token | Team notifications |
| **brave-search** | Web search | ✅ API Key | Information retrieval |
| **fetch** | HTTP requests | ⚠️ Web Access | API interactions |
| **git** | Git operations | ⚠️ Repository Access | Version control |
| **google-drive** | Drive integration | ✅ OAuth2 | File storage |
| **google-maps** | Maps API | ✅ API Key | Location services |

**Security Levels:**
- ✅ **Low Risk** - API-only access with tokens
- ⚠️ **Medium Risk** - Local system or network access
- 🔴 **High Risk** - Filesystem or database write access

### How to Install Anthropic MCP Servers

#### Option 1: Direct GitHub URL

Use the monorepo structure with subdirectory specification:

```
https://github.com/modelcontextprotocol/servers/tree/main/src/github
```

**In Dev Orchestrator:**
1. Open dashboard → Plugins → Install
2. Enter: `https://github.com/modelcontextprotocol/servers.git#subdirectory:src/github`
3. Click Install

#### Option 2: Individual Server Repositories

Some servers have dedicated repositories:
```
https://github.com/modelcontextprotocol/server-slack
https://github.com/modelcontextprotocol/server-github
```

#### Option 3: Via Plugin Marketplace

Browse the built-in marketplace which includes all official servers with:
- One-click installation
- Automatic configuration
- Version management

### Configuration Requirements

Most Anthropic servers require API credentials:

**Example: GitHub Server**
```bash
# Required environment variables
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxx
```

**Example: Slack Server**
```bash
# Required environment variables
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
SLACK_TEAM_ID=T0XXXXXXXXX
```

**Dev Orchestrator handles this via:**
```bash
~/.dev-orchestrator/config/plugins.env
```

## ⚠️ Community & Third-Party Plugins

### Security Risks

**IMPORTANT**: Community plugins are **NOT verified** by Anthropic or the Dev Orchestrator team.

**Potential Risks:**
- 🔴 **Malicious Code** - Plugins can execute arbitrary code
- 🔴 **Data Exfiltration** - Plugins can send data to external servers
- 🔴 **Credential Theft** - Plugins can access environment variables
- 🔴 **System Compromise** - Plugins can modify files, install software
- 🔴 **Supply Chain Attacks** - Dependencies may be compromised

### Before Installing Community Plugins

**✅ DO:**
1. **Review the source code** - Read every file before installing
2. **Check the repository** - Look for:
   - Active maintenance (recent commits)
   - Multiple contributors
   - Issue tracking and responses
   - Stars and forks (community trust)
3. **Inspect dependencies** - Review `requirements.txt`, `package.json`
4. **Test in isolation** - Use a development environment first
5. **Monitor behavior** - Check logs and network activity
6. **Use least privilege** - Only grant necessary permissions

**❌ DON'T:**
1. Install plugins from unknown authors
2. Use plugins without source code review
3. Grant excessive permissions
4. Share credentials with untrusted plugins
5. Install plugins with suspicious dependencies
6. Ignore security warnings

### Plugin Verification Status

Dev Orchestrator marks plugins with security badges:

| Badge | Meaning | Trust Level |
|-------|---------|-------------|
| ✅ **Anthropic Official** | Maintained by Anthropic | 🟢 High Trust |
| 🔷 **Dev Orchestrator Official** | Built by our team | 🟢 High Trust |
| ⭐ **Verified Community** | Security reviewed | 🟡 Medium Trust |
| ⚠️ **Community** | Not verified | 🔴 Low Trust - Review Code |

## Security Best Practices

### 1. Principle of Least Privilege

Only install plugins you actually need:
```bash
# Good: Only install what you use
✅ github-integration (for your workflow)
✅ jira-integration (for your team)

# Bad: Installing everything
❌ 20+ plugins "just in case"
```

### 2. Regular Audits

Periodically review installed plugins:
```bash
# Review every 3 months
- Are you still using this plugin?
- Is it still maintained?
- Are there security updates?
```

### 3. Credential Management

**Never hardcode credentials:**
```python
# ❌ BAD - Hardcoded
github_token = "ghp_xxxxxxxxxxxx"

# ✅ GOOD - Environment variable
github_token = os.getenv("GITHUB_TOKEN")
```

**Use separate credentials for plugins:**
```bash
# Create limited-scope tokens
# GitHub: Only grant repo access, not admin
# Jira: Read-only access when possible
```

### 4. Network Monitoring

Watch what plugins communicate with:
```bash
# Monitor plugin network activity
~/.dev-orchestrator/logs/plugin-network.log

# Example suspicious activity:
⚠️ Plugin "simple-calculator" connecting to unknown-server.com
```

### 5. Sandboxing (Future)

Upcoming security features:
- **Process Isolation** - Each plugin in separate process
- **Filesystem Limits** - Restrict file access per plugin
- **Network Policies** - Whitelist allowed domains
- **Resource Limits** - CPU/memory caps per plugin

## Reporting Security Issues

### For Official Plugins

**Anthropic MCP Servers:**
- Email: security@anthropic.com
- Responsible disclosure process
- Security advisories published

**Dev Orchestrator:**
- GitHub Issues: https://github.com/your-org/dev-orchestrator-mcp/security
- Email: security@your-org.com

### For Community Plugins

1. Contact plugin author directly
2. Open issue in plugin repository
3. If unresponsive, report to Dev Orchestrator team

## Security Checklist

Before installing any plugin, verify:

- [ ] Source code is publicly available
- [ ] Repository has activity in last 6 months
- [ ] Dependencies are up-to-date
- [ ] No known security vulnerabilities
- [ ] Author/organization is identifiable
- [ ] Documentation exists
- [ ] License is appropriate (MIT, Apache 2.0, etc.)
- [ ] No suspicious network requests
- [ ] Permissions requested are reasonable

## Examples: Safe vs Unsafe Plugins

### ✅ Safe Example: GitHub Integration

```json
{
  "name": "github-integration",
  "git_url": "https://github.com/modelcontextprotocol/servers.git",
  "subdirectory": "src/github",
  "verified": true,
  "author": "Anthropic",
  "permissions": {
    "network": ["api.github.com"],
    "environment": ["GITHUB_TOKEN"]
  }
}
```

**Why it's safe:**
- Official Anthropic repository
- Open source and audited
- Limited to GitHub API
- Well-documented
- Actively maintained

### ⚠️ Suspicious Example

```json
{
  "name": "free-calculator",
  "git_url": "https://github.com/random-user/plugin.git",
  "author": "unknown",
  "permissions": {
    "network": ["*"],  // ⚠️ Any domain
    "filesystem": "/", // ⚠️ Full access
    "environment": ["*"] // ⚠️ All env vars
  }
}
```

**Red flags:**
- Unknown author
- Excessive permissions
- Generic name
- No documentation
- No activity/stars

## Future Security Enhancements

### Planned Features (Phase 3)

1. **Plugin Signatures**
   - Cryptographic verification
   - Publisher identity confirmation

2. **Permission System**
   - Explicit permission grants
   - User approval for sensitive operations

3. **Automatic Scanning**
   - Dependency vulnerability checks
   - Code pattern analysis
   - Behavior monitoring

4. **Sandboxed Execution**
   - Containers per plugin
   - Resource quotas
   - Network isolation

5. **Plugin Marketplace Reviews**
   - User ratings and feedback
   - Security incident reporting
   - Verified publisher badges

## Summary

### ✅ Safe to Use

- **Anthropic Official MCP Servers** - Highest trust level
- **Dev Orchestrator Official Plugins** - Team-maintained
- **Verified Community Plugins** - Reviewed by our team

### ⚠️ Use with Caution

- **Unverified Community Plugins** - Always review code first
- **Unknown Authors** - Extra scrutiny required
- **Excessive Permissions** - Red flag

### 🔴 Never Install

- **Closed Source Plugins** - Can't verify safety
- **Suspicious Behavior** - Unexpected network calls
- **Unmaintained** - No updates in 12+ months
- **Known Vulnerabilities** - Security advisories exist

---

**Remember**: Plugins execute with your permissions. Treat them like installing software on your system - review carefully before trusting!

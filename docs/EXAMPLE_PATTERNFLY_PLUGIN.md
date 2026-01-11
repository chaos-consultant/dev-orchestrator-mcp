# Example: Adding PatternFly MCP Server

This guide shows how to add a PatternFly MCP server plugin to the Dev Orchestrator marketplace.

## Quick Add (Local Testing)

1. **Edit your local catalog**:
```bash
cd ~/repos/dev-orchestrator-mcp
nano plugin-catalog.json
```

2. **Add this entry to the `plugins` array**:
```json
{
  "id": "community-patternfly",
  "name": "PatternFly Components",
  "description": "Access PatternFly design system components, documentation, and code examples for building React UIs with enterprise-grade patterns.",
  "author": "PatternFly Community",
  "author_url": "https://www.patternfly.org",
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
    "get_code_examples",
    "list_categories",
    "get_design_tokens"
  ],
  "dependencies": {
    "node": ">=18.0.0",
    "npm": ["@modelcontextprotocol/sdk", "axios"]
  },
  "required_env": [],
  "documentation_url": "https://www.patternfly.org",
  "downloads": 0,
  "rating": 0,
  "security_notes": "Read-only access to PatternFly documentation. No external API calls beyond patternfly.org. No file system access required."
}
```

3. **Copy to public directory**:
```bash
cp plugin-catalog.json dashboard/public/plugin-catalog.json
```

4. **Refresh marketplace** in browser to see the plugin

## What This Plugin Would Provide

If this MCP server exists or when you create it, it would provide:

### Tools

**search_components**
```json
{
  "name": "search_components",
  "description": "Search for PatternFly components by name or description",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search term (e.g., 'button', 'modal', 'form')"
      }
    }
  }
}
```

**get_component_docs**
```json
{
  "name": "get_component_docs",
  "description": "Get full documentation for a specific component",
  "inputSchema": {
    "type": "object",
    "properties": {
      "component": {
        "type": "string",
        "description": "Component name (e.g., 'Button', 'Modal')"
      }
    }
  }
}
```

**get_code_examples**
```json
{
  "name": "get_code_examples",
  "description": "Get code examples for a component",
  "inputSchema": {
    "type": "object",
    "properties": {
      "component": {
        "type": "string",
        "description": "Component name"
      },
      "variant": {
        "type": "string",
        "description": "Specific variant (optional)"
      }
    }
  }
}
```

## Creating the Plugin (If It Doesn't Exist)

If you want to create this plugin from scratch:

### 1. Setup

```bash
mkdir patternfly-mcp
cd patternfly-mcp
npm init -y
npm install @modelcontextprotocol/sdk axios cheerio
```

### 2. Create package.json

```json
{
  "name": "patternfly-mcp",
  "version": "1.0.0",
  "description": "MCP server for PatternFly design system",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "axios": "^1.6.0",
    "cheerio": "^1.0.0-rc.12"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.3.0",
    "tsx": "^4.7.0"
  },
  "mcpServer": {
    "tools": [
      "search_components",
      "get_component_docs",
      "get_code_examples"
    ],
    "requiredEnv": []
  }
}
```

### 3. Create src/index.ts

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

const PATTERNFLY_API = 'https://www.patternfly.org/v4';

class PatternFlyServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'patternfly-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
  }

  private setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_components',
            description: 'Search for PatternFly components',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search term',
                },
              },
              required: ['query'],
            },
          },
          {
            name: 'get_component_docs',
            description: 'Get documentation for a component',
            inputSchema: {
              type: 'object',
              properties: {
                component: {
                  type: 'string',
                  description: 'Component name',
                },
              },
              required: ['component'],
            },
          },
          {
            name: 'get_code_examples',
            description: 'Get code examples for a component',
            inputSchema: {
              type: 'object',
              properties: {
                component: {
                  type: 'string',
                  description: 'Component name',
                },
              },
              required: ['component'],
            },
          },
        ] as Tool[],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case 'search_components':
          return await this.searchComponents(args.query as string);
        case 'get_component_docs':
          return await this.getComponentDocs(args.component as string);
        case 'get_code_examples':
          return await this.getCodeExamples(args.component as string);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  private async searchComponents(query: string) {
    // Implementation would fetch from PatternFly docs
    const response = await axios.get(`${PATTERNFLY_API}/components`);
    // Parse and filter components
    return {
      content: [
        {
          type: 'text',
          text: `Found components matching "${query}"`,
        },
      ],
    };
  }

  private async getComponentDocs(component: string) {
    // Implementation would fetch component documentation
    return {
      content: [
        {
          type: 'text',
          text: `Documentation for ${component}`,
        },
      ],
    };
  }

  private async getCodeExamples(component: string) {
    // Implementation would fetch code examples
    return {
      content: [
        {
          type: 'text',
          text: `Code examples for ${component}`,
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('PatternFly MCP server running on stdio');
  }
}

const server = new PatternFlyServer();
server.run().catch(console.error);
```

### 4. Build and Test

```bash
# Build
npm run build

# Test with Dev Orchestrator
# In dashboard: Plugins → Install → file:///path/to/patternfly-mcp
```

## Alternative: Use Existing MCP Servers

Instead of creating a new plugin, you might want to use existing Anthropic MCP servers:

- **@modelcontextprotocol/server-filesystem**: For reading PatternFly source files locally
- **@modelcontextprotocol/server-fetch**: For fetching PatternFly documentation
- **@modelcontextprotocol/server-puppeteer**: For scraping PatternFly component examples

## Add to Official Catalog

Once your plugin is working and tested:

1. **Create a pull request** to `dev-orchestrator-mcp`
2. **Add your entry** to `plugin-catalog.json`
3. **Include**:
   - Link to plugin repository
   - Test results
   - Screenshots of it working
   - Security review notes

See [PLUGIN_CONTRIBUTING.md](./PLUGIN_CONTRIBUTING.md) for full details.

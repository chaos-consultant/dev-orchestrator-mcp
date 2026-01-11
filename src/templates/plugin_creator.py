"""
Plugin Creator - Template-based scaffolding for MCP plugins
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Literal


class PluginCreator:
    """Creates plugin templates for basic and advanced MCP servers."""

    def __init__(self, plugins_dir: Path = None):
        self.plugins_dir = plugins_dir or Path.home() / ".dev-orchestrator" / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def create_plugin(
        self,
        name: str,
        description: str,
        author: str,
        template_type: Literal["basic", "advanced"],
        runtime: Literal["python", "node"] = "python",
        tools: List[Dict] = None
    ) -> Dict[str, str]:
        """
        Create a new plugin from template.

        Args:
            name: Plugin name (kebab-case)
            description: Plugin description
            author: Author name
            template_type: "basic" or "advanced"
            runtime: "python" or "node"
            tools: List of tool definitions

        Returns:
            Dict with created file paths
        """
        plugin_dir = self.plugins_dir / name
        if plugin_dir.exists():
            raise ValueError(f"Plugin directory already exists: {plugin_dir}")

        plugin_dir.mkdir(parents=True, exist_ok=True)

        created_files = {}

        # Create manifest
        manifest_path = plugin_dir / "mcp_server.json"
        manifest = self._create_manifest(name, description, author, runtime)
        manifest_path.write_text(json.dumps(manifest, indent=2))
        created_files["manifest"] = str(manifest_path)

        # Create implementation based on runtime
        if runtime == "python":
            impl_path = plugin_dir / "server.py"
            if template_type == "basic":
                content = self._create_basic_python(name, tools or [])
            else:
                content = self._create_advanced_python(name, tools or [])
            impl_path.write_text(content)
            created_files["implementation"] = str(impl_path)

            # Create requirements.txt
            req_path = plugin_dir / "requirements.txt"
            req_path.write_text("mcp>=0.9.0\naiohttp>=3.9.0\n")
            created_files["requirements"] = str(req_path)

        elif runtime == "node":
            impl_path = plugin_dir / "index.js"
            if template_type == "basic":
                content = self._create_basic_node(name, tools or [])
            else:
                content = self._create_advanced_node(name, tools or [])
            impl_path.write_text(content)
            created_files["implementation"] = str(impl_path)

            # Create package.json
            pkg_path = plugin_dir / "package.json"
            pkg = {
                "name": name,
                "version": "1.0.0",
                "description": description,
                "main": "index.js",
                "dependencies": {
                    "@modelcontextprotocol/sdk": "^0.5.0"
                }
            }
            pkg_path.write_text(json.dumps(pkg, indent=2))
            created_files["package"] = str(pkg_path)

        # Create README
        readme_path = plugin_dir / "README.md"
        readme_path.write_text(self._create_readme(name, description, author, runtime))
        created_files["readme"] = str(readme_path)

        return created_files

    def _create_manifest(self, name: str, description: str, author: str, runtime: str) -> Dict:
        """Create plugin manifest."""
        return {
            "name": name,
            "version": "1.0.0",
            "description": description,
            "author": author,
            "entry": "server.py" if runtime == "python" else "index.js",
            "runtime": runtime,
            "dependencies": []
        }

    def _create_basic_python(self, name: str, tools: List[Dict]) -> str:
        """Create basic Python plugin template."""
        tools_code = ""
        for tool in tools:
            tool_name = tool["name"]
            tool_desc = tool["description"]
            tools_code += f'''
        Tool(
            name="{tool_name}",
            description="{tool_desc}",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "param": {{"type": "string", "description": "Parameter"}}
                }},
                "required": ["param"]
            }}
        ),'''

        call_tool_code = ""
        for tool in tools:
            tool_name = tool["name"]
            call_tool_code += f'''
    if name == "{tool_name}":
        param = arguments["param"]
        result = f"{{param}} processed by {tool_name}"
        return [TextContent(type="text", text=result)]
    '''

        return f'''"""
{name} - MCP Plugin
"""
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

server = Server("{name}")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [{tools_code}
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Call a tool."""
{call_tool_code}

    return [TextContent(type="text", text=f"Unknown tool: {{name}}")]

if __name__ == "__main__":
    asyncio.run(server.run())
'''

    def _create_advanced_python(self, name: str, tools: List[Dict]) -> str:
        """Create advanced Python plugin template with state management."""
        return f'''"""
{name} - Advanced MCP Plugin with State Management
"""
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
import asyncio
import aiohttp
from typing import Dict, Any

server = Server("{name}")

class PluginState:
    """Plugin state management."""
    def __init__(self):
        self.data: Dict[str, Any] = {{}}
        self.session: aiohttp.ClientSession | None = None

    async def initialize(self):
        """Initialize plugin resources."""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Cleanup plugin resources."""
        if self.session:
            await self.session.close()

# Global state
state = PluginState()

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="example_tool",
            description="Example tool with state",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "action": {{
                        "type": "string",
                        "enum": ["get", "set"],
                        "description": "Action to perform"
                    }},
                    "key": {{"type": "string"}},
                    "value": {{"type": "string"}}
                }},
                "required": ["action", "key"]
            }}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Call a tool with state management."""
    if name == "example_tool":
        action = arguments["action"]
        key = arguments["key"]

        if action == "get":
            value = state.data.get(key, "Not found")
            return [TextContent(type="text", text=f"{{key}}: {{value}}")]
        elif action == "set":
            value = arguments.get("value", "")
            state.data[key] = value
            return [TextContent(type="text", text=f"Set {{key}} = {{value}}")]

    return [TextContent(type="text", text=f"Unknown tool: {{name}}")]

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri=f"{name}://state",
            name="Plugin State",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == f"{name}://state":
        import json
        return json.dumps(state.data, indent=2)
    raise ValueError(f"Unknown resource: {{uri}}")

async def main():
    """Main entry point."""
    await state.initialize()
    try:
        await server.run()
    finally:
        await state.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
'''

    def _create_basic_node(self, name: str, tools: List[Dict]) -> str:
        """Create basic Node.js plugin template."""
        return f'''/**
 * {name} - MCP Plugin (Node.js)
 */
import {{ Server }} from '@modelcontextprotocol/sdk/server/index.js';
import {{ StdioServerTransport }} from '@modelcontextprotocol/sdk/server/stdio.js';
import {{
  ListToolsRequestSchema,
  CallToolRequestSchema,
}} from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
  {{
    name: '{name}',
    version: '1.0.0',
  }},
  {{
    capabilities: {{
      tools: {{}},
    }},
  }}
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({{
  tools: [
    {{
      name: 'example_tool',
      description: 'Example tool',
      inputSchema: {{
        type: 'object',
        properties: {{
          param: {{ type: 'string' }},
        }},
        required: ['param'],
      }},
    }},
  ],
}}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {{
  const {{ name, arguments: args }} = request.params;

  if (name === 'example_tool') {{
    return {{
      content: [
        {{
          type: 'text',
          text: `Processed: ${{args.param}}`,
        }},
      ],
    }};
  }}

  throw new Error(`Unknown tool: ${{name}}`);
}});

const transport = new StdioServerTransport();
await server.connect(transport);
'''

    def _create_advanced_node(self, name: str, tools: List[Dict]) -> str:
        """Create advanced Node.js plugin template."""
        return f'''/**
 * {name} - Advanced MCP Plugin with State (Node.js)
 */
import {{ Server }} from '@modelcontextprotocol/sdk/server/index.js';
import {{ StdioServerTransport }} from '@modelcontextprotocol/sdk/server/stdio.js';
import {{
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
}} from '@modelcontextprotocol/sdk/types.js';

class PluginState {{
  constructor() {{
    this.data = {{}};
  }}

  async initialize() {{
    // Initialize resources
  }}

  async cleanup() {{
    // Cleanup resources
  }}
}}

const state = new PluginState();

const server = new Server(
  {{
    name: '{name}',
    version: '1.0.0',
  }},
  {{
    capabilities: {{
      tools: {{}},
      resources: {{}},
    }},
  }}
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({{
  tools: [
    {{
      name: 'state_tool',
      description: 'Manage plugin state',
      inputSchema: {{
        type: 'object',
        properties: {{
          action: {{ type: 'string', enum: ['get', 'set'] }},
          key: {{ type: 'string' }},
          value: {{ type: 'string' }},
        }},
        required: ['action', 'key'],
      }},
    }},
  ],
}}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {{
  const {{ name, arguments: args }} = request.params;

  if (name === 'state_tool') {{
    if (args.action === 'get') {{
      const value = state.data[args.key] || 'Not found';
      return {{
        content: [{{ type: 'text', text: `${{args.key}}: ${{value}}` }}],
      }};
    }} else if (args.action === 'set') {{
      state.data[args.key] = args.value;
      return {{
        content: [{{ type: 'text', text: `Set ${{args.key}} = ${{args.value}}` }}],
      }};
    }}
  }}

  throw new Error(`Unknown tool: ${{name}}`);
}});

server.setRequestHandler(ListResourcesRequestSchema, async () => ({{
  resources: [
    {{
      uri: '{name}://state',
      name: 'Plugin State',
      mimeType: 'application/json',
    }},
  ],
}}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {{
  if (request.params.uri === '{name}://state') {{
    return {{
      contents: [
        {{
          uri: '{name}://state',
          mimeType: 'application/json',
          text: JSON.stringify(state.data, null, 2),
        }},
      ],
    }};
  }}
  throw new Error(`Unknown resource: ${{request.params.uri}}`);
}});

await state.initialize();
const transport = new StdioServerTransport();
await server.connect(transport);

process.on('SIGINT', async () => {{
  await state.cleanup();
  process.exit(0);
}});
'''

    def _create_readme(self, name: str, description: str, author: str, runtime: str) -> str:
        """Create README template."""
        return f'''# {name}

{description}

## Author

{author}

## Installation

```bash
cd ~/.dev-orchestrator/plugins/{name}

{"pip install -r requirements.txt" if runtime == "python" else "npm install"}
```

## Usage

This plugin provides the following tools:

- `example_tool`: Example tool description

## Development

### Running Tests

```bash
{"pytest" if runtime == "python" else "npm test"}
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT
'''

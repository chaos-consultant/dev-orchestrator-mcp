import { Step } from 'react-joyride';

export const dashboardTourSteps: Step[] = [
  {
    target: 'body',
    content: 'Welcome to Dev Orchestrator! This tour will guide you through the main features of the dashboard.',
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: '.MuiDrawer-root',
    content: 'Use the sidebar to navigate between sections: Dashboard, Plugins, Extensions, Workspace, Logs, and Settings. Click the toggle to collapse or expand.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: 'input[placeholder*="command"]',
    content: 'Enter shell commands here to execute in your project directory. Use normal mode for direct commands or toggle NLP mode for natural language.',
    placement: 'bottom',
    spotlightClicks: true,
  },
  {
    target: '.MuiSwitch-root',
    content: 'Toggle NLP mode to use natural language. Examples: "list folders with ansible", "show git status". Supports Ollama, OpenAI, Gemini, and Anthropic.',
    placement: 'bottom',
  },
  {
    target: '[class*="MuiGrid-root"] [class*="MuiCard-root"]:first-child',
    content: 'Your current project is shown here in a compact view with path, type, git branch, and venv status as badges.',
    placement: 'top',
  },
  {
    target: '[class*="MuiGrid-root"] [class*="MuiCard-root"]:nth-child(2)',
    content: 'Recent commands and saved commands appear here. Save frequently-used commands for quick access.',
    placement: 'top',
  },
  {
    target: '[class*="MuiGrid-root"] [class*="MuiCard-root"]:nth-child(3)',
    content: 'Running services are shown here when active. Click Stop to terminate a service.',
    placement: 'top',
  },
  {
    target: '[class*="MuiGrid-root"] > [class*="MuiGrid-root"]:last-child',
    content: 'Your workspace repositories are displayed in a compact grid. Each card shows git status with colored borders: green=clean, yellow=changes, blue=ahead, red=behind. Click any repo to switch.',
    placement: 'top',
  },
  {
    target: '.MuiDrawer-root [data-testid="ExtensionIcon"]',
    content: 'Visit the Plugins page to install MCP servers from the marketplace or Git URLs. Core plugins like GitHub, Slack, and Filesystem are built-in.',
    placement: 'right',
  },
  {
    target: '.MuiDrawer-root [data-testid="ArticleIcon"]',
    content: 'The Logs page shows real-time output from commands, services, and system events with filtering by level (INFO, WARN, ERROR).',
    placement: 'right',
  },
  {
    target: 'body',
    content: 'That\'s it! You\'re ready to use Dev Orchestrator. Explore Settings to configure NLP providers, dark mode, and more.',
    placement: 'center',
  },
];

export const pluginsTourSteps: Step[] = [
  {
    target: 'body',
    content: 'Manage MCP server plugins here. Core plugins (GitHub, Slack, Filesystem, Git, Postgres, Puppeteer) are built into dev-orchestrator. Install additional plugins from the marketplace.',
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: 'button:has-text("Browse Marketplace")',
    content: 'Browse the official plugin catalog including Jira, Docker, Database Query, and community plugins.',
    placement: 'bottom',
  },
  {
    target: 'button:has-text("Install from Git")',
    content: 'Install custom plugins from Git URLs. Plugins are MCP servers that extend functionality with new tools.',
    placement: 'bottom',
  },
  {
    target: 'button:has-text("Create Plugin")',
    content: 'Use the interactive plugin creator to scaffold a new plugin with templates. Choose Basic (simple tools) or Advanced (full MCP server) templates.',
    placement: 'bottom',
  },
];

export const extensionsTourSteps: Step[] = [
  {
    target: 'body',
    content: 'Extensions customize your dashboard with widgets, workflows, and integrations. Unlike plugins (MCP servers), extensions are React components and YAML configs.',
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: 'button:has-text("Create Widget")',
    content: 'Widgets are custom React dashboard panels. Use the interactive creator to scaffold a widget with props for state and sendMessage.',
    placement: 'bottom',
  },
  {
    target: 'button:has-text("Create Workflow")',
    content: 'Workflows are multi-step command sequences defined in YAML with parameters, conditionals, and error handling.',
    placement: 'bottom',
  },
  {
    target: 'button:has-text("Configure Integration")',
    content: 'Integrations connect external services (Slack, GitHub, Jira) to receive notifications on command completion, failures, or approvals.',
    placement: 'bottom',
  },
];

export const tours = {
  dashboard: dashboardTourSteps,
  plugins: pluginsTourSteps,
  extensions: extensionsTourSteps,
};

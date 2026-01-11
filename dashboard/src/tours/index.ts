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
    content: 'Use the sidebar to navigate between different sections: Dashboard, Plugins, Extensions, Workspace, and Settings. Click the toggle button to collapse or expand it.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: 'input[placeholder*="command"]',
    content: 'Enter shell commands here to execute them in your current project directory. Press Enter or click Run to execute.',
    placement: 'bottom',
    spotlightClicks: true,
  },
  {
    target: '.MuiSwitch-root',
    content: 'Toggle NLP mode to use natural language commands. AI will translate plain English like "show files" into shell commands.',
    placement: 'bottom',
  },
  {
    target: '[class*="MuiGrid-root"] [class*="MuiCard-root"]:first-child',
    content: 'Your current project information is displayed here, including project type, Git branch, and virtual environment status.',
    placement: 'top',
  },
  {
    target: '[class*="MuiGrid-root"] [class*="MuiCard-root"]:nth-child(2)',
    content: 'Monitor and control running background services. You can stop services with the Stop button.',
    placement: 'top',
  },
  {
    target: '[class*="MuiGrid-root"] [class*="MuiCard-root"]:nth-child(3)',
    content: 'Manage MCP server plugins here. Install new plugins from Git URLs or browse the marketplace.',
    placement: 'top',
  },
  {
    target: 'body',
    content: 'That\'s it! You\'re ready to start using Dev Orchestrator. Click the help icon anytime to see detailed documentation.',
    placement: 'center',
  },
];

export const pluginsTourSteps: Step[] = [
  {
    target: 'body',
    content: 'This is the Plugins view where you can manage all your MCP server plugins.',
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: 'button:has-text("Browse Marketplace")',
    content: 'Click here to browse available plugins from the official catalog.',
    placement: 'bottom',
  },
  {
    target: 'button:has-text("Install from Git")',
    content: 'Or install a plugin directly from a Git URL if you have a custom plugin.',
    placement: 'bottom',
  },
];

export const extensionsTourSteps: Step[] = [
  {
    target: 'body',
    content: 'Extensions allow you to customize your dashboard with widgets, workflows, and integrations.',
    placement: 'center',
    disableBeacon: true,
  },
];

export const tours = {
  dashboard: dashboardTourSteps,
  plugins: pluginsTourSteps,
  extensions: extensionsTourSteps,
};

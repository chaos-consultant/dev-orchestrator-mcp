import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Switch,
  Chip,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stack,
  Tooltip,
  styled,
} from '@mui/material';
import {
  Extension as ExtensionIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  GitHub as GitHubIcon,
  Store as StoreIcon,
  Code as CodeIcon,
} from '@mui/icons-material';
import PluginMarketplace from './PluginMarketplace';
import PluginCreator from './PluginCreator';

// Types
interface PluginTool {
  id: string;
  plugin_id: string;
  tool_name: string;
  enabled: boolean;
}

interface Plugin {
  id: string;
  name: string;
  git_url: string;
  version?: string;
  author?: string;
  description?: string;
  installed_at: string;
  enabled: boolean;
  install_path: string;
  tools: PluginTool[];
}

interface PluginsPanelProps {
  plugins: Plugin[];
  onInstallPlugin: (gitUrl: string) => Promise<void>;
  onUninstallPlugin: (pluginId: string) => Promise<void>;
  onTogglePlugin: (pluginId: string, enabled: boolean) => Promise<void>;
  onToggleTool: (pluginId: string, toolName: string, enabled: boolean) => Promise<void>;
  onCreatePlugin: (pluginData: any) => Promise<void>;
}

// Styled components with macOS aesthetic
const PluginCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(1),
  borderRadius: 12,
  border: theme.palette.mode === 'dark'
    ? '1px solid rgba(255, 255, 255, 0.08)'
    : '1px solid rgba(0, 0, 0, 0.06)',
  backgroundColor: theme.palette.mode === 'dark'
    ? 'rgba(255, 255, 255, 0.03)'
    : 'rgba(0, 0, 0, 0.02)',
  boxShadow: theme.palette.mode === 'dark'
    ? '0 2px 8px rgba(0, 0, 0, 0.3)'
    : '0 2px 8px rgba(0, 0, 0, 0.1)',
}));

const PluginsPanel: React.FC<PluginsPanelProps> = ({
  plugins,
  onInstallPlugin,
  onUninstallPlugin,
  onTogglePlugin,
  onToggleTool,
  onCreatePlugin,
}) => {
  const [showInstallDialog, setShowInstallDialog] = useState(false);
  const [showMarketplace, setShowMarketplace] = useState(false);
  const [showCreator, setShowCreator] = useState(false);
  const [gitUrl, setGitUrl] = useState('');
  const [installing, setInstalling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedPlugin, setExpandedPlugin] = useState<string | null>(null);

  const handleInstall = async () => {
    if (!gitUrl.trim()) {
      setError('Please enter a Git URL');
      return;
    }

    setInstalling(true);
    setError(null);

    try {
      await onInstallPlugin(gitUrl);
      setGitUrl('');
      setShowInstallDialog(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Installation failed');
    } finally {
      setInstalling(false);
    }
  };

  const handleUninstall = async (pluginId: string, pluginName: string) => {
    if (window.confirm(`Are you sure you want to uninstall "${pluginName}"?`)) {
      try {
        await onUninstallPlugin(pluginId);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Uninstall failed');
      }
    }
  };

  const handleTogglePlugin = async (pluginId: string, enabled: boolean) => {
    try {
      await onTogglePlugin(pluginId, !enabled);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Toggle failed');
    }
  };

  const handleToggleTool = async (pluginId: string, toolName: string, enabled: boolean) => {
    try {
      await onToggleTool(pluginId, toolName, !enabled);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Toggle failed');
    }
  };

  const handleAccordionChange = (pluginId: string) => (_: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedPlugin(isExpanded ? pluginId : null);
  };

  return (
    <>
      <Card sx={{ height: '100%' }}>
        <CardHeader
          avatar={<ExtensionIcon />}
          title="Plugins"
          action={
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<StoreIcon />}
                onClick={() => setShowMarketplace(true)}
              >
                Browse
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setShowInstallDialog(true)}
              >
                Install
              </Button>
              <Button
                variant="contained"
                size="small"
                startIcon={<CodeIcon />}
                onClick={() => setShowCreator(true)}
              >
                Create New
              </Button>
            </Stack>
          }
        />
        <CardContent>
          {error && (
            <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {plugins.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <ExtensionIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                No plugins installed
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Click "Install" to add MCP server plugins
              </Typography>
            </Box>
          ) : (
            <Box sx={{ maxHeight: '600px', overflowY: 'auto' }}>
              {plugins.map((plugin) => (
                <PluginCard key={plugin.id}>
                  <Accordion
                    expanded={expandedPlugin === plugin.id}
                    onChange={handleAccordionChange(plugin.id)}
                    sx={{
                      backgroundColor: 'transparent',
                      boxShadow: 'none',
                      '&:before': { display: 'none' },
                    }}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', mr: 2 }}>
                        <ExtensionIcon sx={{ mr: 1.5, color: plugin.enabled ? 'primary.main' : 'text.disabled' }} />
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {plugin.name}
                          </Typography>
                          {plugin.version && (
                            <Typography variant="caption" color="text.secondary">
                              v{plugin.version}
                            </Typography>
                          )}
                        </Box>
                        <Stack direction="row" spacing={1} alignItems="center" onClick={(e) => e.stopPropagation()}>
                          <Chip
                            label={`${plugin.tools.length} tools`}
                            size="small"
                            variant="outlined"
                          />
                          <Switch
                            checked={plugin.enabled}
                            onChange={() => handleTogglePlugin(plugin.id, plugin.enabled)}
                            size="small"
                          />
                          <Tooltip title="Uninstall">
                            <IconButton
                              size="small"
                              onClick={() => handleUninstall(plugin.id, plugin.name)}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </Box>
                    </AccordionSummary>

                    <AccordionDetails>
                      <Stack spacing={2}>
                        {/* Plugin Info */}
                        {plugin.description && (
                          <Typography variant="body2" color="text.secondary">
                            {plugin.description}
                          </Typography>
                        )}

                        <Box>
                          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                            <GitHubIcon fontSize="small" color="action" />
                            <Typography variant="caption" color="text.secondary" sx={{
                              wordBreak: 'break-all',
                              fontFamily: "'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace"
                            }}>
                              {plugin.git_url}
                            </Typography>
                          </Stack>
                          {plugin.author && (
                            <Typography variant="caption" color="text.secondary">
                              by {plugin.author}
                            </Typography>
                          )}
                        </Box>

                        <Divider />

                        {/* Tools */}
                        <Box>
                          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                            Tools ({plugin.tools.length})
                          </Typography>

                          {plugin.tools.length === 0 ? (
                            <Typography variant="caption" color="text.secondary">
                              No tools available
                            </Typography>
                          ) : (
                            <List dense disablePadding>
                              {plugin.tools.map((tool) => (
                                <ListItem
                                  key={tool.id}
                                  sx={{
                                    borderRadius: 1,
                                    mb: 0.5,
                                    backgroundColor: (theme) => theme.palette.mode === 'dark'
                                      ? 'rgba(255, 255, 255, 0.02)'
                                      : 'rgba(0, 0, 0, 0.02)',
                                  }}
                                >
                                  <ListItemText
                                    primary={
                                      <Typography
                                        variant="body2"
                                        sx={{
                                          fontFamily: "'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace",
                                          fontSize: '0.875rem',
                                        }}
                                      >
                                        {tool.tool_name}
                                      </Typography>
                                    }
                                  />
                                  <ListItemSecondaryAction>
                                    <Switch
                                      edge="end"
                                      checked={tool.enabled && plugin.enabled}
                                      onChange={() => handleToggleTool(plugin.id, tool.tool_name, tool.enabled)}
                                      disabled={!plugin.enabled}
                                      size="small"
                                    />
                                  </ListItemSecondaryAction>
                                </ListItem>
                              ))}
                            </List>
                          )}
                        </Box>

                        {/* Metadata */}
                        <Box sx={{ pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                          <Typography variant="caption" color="text.secondary">
                            Installed: {new Date(plugin.installed_at).toLocaleString()}
                          </Typography>
                        </Box>
                      </Stack>
                    </AccordionDetails>
                  </Accordion>
                </PluginCard>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Install Plugin Dialog */}
      <Dialog
        open={showInstallDialog}
        onClose={() => !installing && setShowInstallDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Install Plugin</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Enter the Git repository URL for the MCP server plugin you want to install.
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label="Git URL"
            placeholder="https://github.com/user/plugin.git"
            value={gitUrl}
            onChange={(e) => setGitUrl(e.target.value)}
            disabled={installing}
            helperText="The plugin must contain mcp_server.json or package.json"
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !installing) {
                handleInstall();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowInstallDialog(false)} disabled={installing}>
            Cancel
          </Button>
          <Button
            onClick={handleInstall}
            variant="contained"
            disabled={installing || !gitUrl.trim()}
            startIcon={installing ? <CircularProgress size={16} /> : <AddIcon />}
          >
            {installing ? 'Installing...' : 'Install'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Plugin Marketplace */}
      <PluginMarketplace
        open={showMarketplace}
        onClose={() => setShowMarketplace(false)}
        onInstallPlugin={onInstallPlugin}
      />

      {/* Plugin Creator */}
      <PluginCreator
        open={showCreator}
        onClose={() => setShowCreator(false)}
        onCreatePlugin={onCreatePlugin}
      />
    </>
  );
};

export default PluginsPanel;

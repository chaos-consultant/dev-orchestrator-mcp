import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Typography,
  Chip,
  Box,
  Tab,
  Tabs,
  Alert,
  IconButton,
  Tooltip,
  InputAdornment,
  Stack,
  Divider,
  Link,
} from '@mui/material';
import {
  Search as SearchIcon,
  Close as CloseIcon,
  Security as SecurityIcon,
  Star as StarIcon,
  Download as DownloadIcon,
  OpenInNew as OpenInNewIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Extension as ExtensionIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// Types
interface CatalogPlugin {
  id: string;
  name: string;
  description: string;
  author: string;
  author_url: string;
  category: string;
  git_url: string;
  subdirectory?: string;
  version: string;
  mcp_version: string;
  verified: boolean;
  verification_level: string;
  tools: string[];
  dependencies: {
    python?: string;
    node?: string;
    pip?: string[];
    npm?: string[];
  };
  required_env: string[];
  documentation_url: string;
  downloads: number;
  rating: number;
  security_notes: string;
}

interface PluginCatalog {
  version: string;
  last_updated: string;
  categories: string[];
  plugins: CatalogPlugin[];
  verification_levels: {
    [key: string]: {
      label: string;
      badge_color: string;
      trust_level: string;
      description: string;
    };
  };
}

interface PluginMarketplaceProps {
  open: boolean;
  onClose: () => void;
  onInstallPlugin: (gitUrl: string) => Promise<void>;
}

const PluginMarketplace: React.FC<PluginMarketplaceProps> = ({
  open,
  onClose,
  onInstallPlugin,
}) => {
  const [catalog, setCatalog] = useState<PluginCatalog | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTab, setSelectedTab] = useState(0); // 0=All, 1=Anthropic, 2=Official, 3=Community
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlugin, setSelectedPlugin] = useState<CatalogPlugin | null>(null);
  const [installing, setInstalling] = useState<string | null>(null);

  // Load plugin catalog
  useEffect(() => {
    if (open) {
      loadCatalog();
    }
  }, [open]);

  const loadCatalog = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load from local file (in production, this would be from GitHub)
      const response = await fetch('/plugin-catalog.json');
      if (!response.ok) {
        throw new Error('Failed to load plugin catalog');
      }
      const data = await response.json();
      setCatalog(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load catalog');
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async (plugin: CatalogPlugin) => {
    setInstalling(plugin.id);

    try {
      // Construct full git URL with subdirectory if needed
      const gitUrl = plugin.subdirectory
        ? `${plugin.git_url}#subdirectory:${plugin.subdirectory}`
        : plugin.git_url;

      await onInstallPlugin(gitUrl);
      // Success - could show success message
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Installation failed');
    } finally {
      setInstalling(null);
    }
  };

  const getFilteredPlugins = (): CatalogPlugin[] => {
    if (!catalog) return [];

    let filtered = catalog.plugins;

    // Filter by tab
    if (selectedTab === 1) {
      // Anthropic Official
      filtered = filtered.filter(p => p.verification_level === 'anthropic-official');
    } else if (selectedTab === 2) {
      // Dev Orchestrator Official
      filtered = filtered.filter(p => p.verification_level === 'devorch-official');
    } else if (selectedTab === 3) {
      // Community
      filtered = filtered.filter(
        p => p.verification_level !== 'anthropic-official' &&
           p.verification_level !== 'devorch-official'
      );
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(p => p.category === selectedCategory);
    }

    // Filter by search
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        p =>
          p.name.toLowerCase().includes(term) ||
          p.description.toLowerCase().includes(term) ||
          p.author.toLowerCase().includes(term) ||
          p.tools.some(t => t.toLowerCase().includes(term))
      );
    }

    return filtered;
  };

  const getVerificationBadge = (plugin: CatalogPlugin) => {
    if (!catalog) return null;

    const level = catalog.verification_levels[plugin.verification_level];
    if (!level) return null;

    const icons = {
      'anthropic-official': <CheckCircleIcon fontSize="small" />,
      'devorch-official': <CheckCircleIcon fontSize="small" />,
      'verified-community': <StarIcon fontSize="small" />,
      'community': <ExtensionIcon fontSize="small" />,
    };

    return (
      <Tooltip title={level.description}>
        <Chip
          icon={icons[plugin.verification_level as keyof typeof icons]}
          label={level.label}
          size="small"
          sx={{
            backgroundColor: level.badge_color,
            color: 'white',
            fontWeight: 600,
            fontSize: '0.7rem',
          }}
        />
      </Tooltip>
    );
  };

  const getSecurityIcon = (plugin: CatalogPlugin) => {
    const hasWarning = plugin.security_notes.includes('⚠️');
    const hasDanger = plugin.security_notes.includes('🔴');

    if (hasDanger) {
      return (
        <Tooltip title="High-risk permissions required">
          <SecurityIcon color="error" fontSize="small" />
        </Tooltip>
      );
    } else if (hasWarning) {
      return (
        <Tooltip title="Medium-risk permissions required">
          <WarningIcon color="warning" fontSize="small" />
        </Tooltip>
      );
    } else {
      return (
        <Tooltip title="Low-risk permissions">
          <CheckCircleIcon color="success" fontSize="small" />
        </Tooltip>
      );
    }
  };

  const filteredPlugins = getFilteredPlugins();

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center" gap={1}>
              <ExtensionIcon />
              <Typography variant="h6">Plugin Marketplace</Typography>
            </Box>
            <IconButton onClick={onClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent>
          {/* Security Notice */}
          <Alert severity="info" icon={<SecurityIcon />} sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Security Notice:</strong> Anthropic Official plugins are maintained and security-audited by Anthropic.
              Always review plugin source code before installing. See <strong>docs/PLUGIN_SECURITY.md</strong> in the repository.
            </Typography>
          </Alert>

          {/* Contribution Notice */}
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Want to contribute?</strong> Add your MCP server plugin to the marketplace!
              See <strong>docs/PLUGIN_CONTRIBUTING.md</strong> in the repository for guidelines.
            </Typography>
          </Alert>

          {error && (
            <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Tabs for filtering */}
          <Tabs
            value={selectedTab}
            onChange={(_, newValue) => setSelectedTab(newValue)}
            sx={{ mb: 2 }}
          >
            <Tab label="All Plugins" />
            <Tab label="Anthropic Official" />
            <Tab label="Dev Orchestrator" />
            <Tab label="Community" />
          </Tabs>

          {/* Search and Filter */}
          <Box display="flex" gap={2} mb={3}>
            <TextField
              fullWidth
              placeholder="Search plugins, tools, or authors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              size="small"
            />
            <TextField
              select
              label="Category"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              SelectProps={{
                native: true,
              }}
              size="small"
              sx={{ minWidth: 200 }}
            >
              <option value="all">All Categories</option>
              {catalog?.categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace('-', ' ').toUpperCase()}
                </option>
              ))}
            </TextField>
          </Box>

          {/* Plugin Grid */}
          {loading ? (
            <Box textAlign="center" py={4}>
              <Typography>Loading plugins...</Typography>
            </Box>
          ) : filteredPlugins.length === 0 ? (
            <Box textAlign="center" py={4}>
              <ExtensionIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                No plugins found matching your criteria
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {filteredPlugins.map((plugin) => (
                <Grid item xs={12} md={6} key={plugin.id}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: 'divider',
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                        <Box flex={1}>
                          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
                            {plugin.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            by{' '}
                            <Link href={plugin.author_url} target="_blank" underline="hover">
                              {plugin.author}
                            </Link>
                          </Typography>
                        </Box>
                        <Box display="flex" gap={0.5}>
                          {getVerificationBadge(plugin)}
                          {getSecurityIcon(plugin)}
                        </Box>
                      </Box>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 60 }}>
                        {plugin.description}
                      </Typography>

                      <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 1 }}>
                        <Chip
                          label={plugin.category}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                        <Chip
                          label={`v${plugin.version}`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                        <Chip
                          icon={<DownloadIcon sx={{ fontSize: '0.9rem' }} />}
                          label={plugin.downloads.toLocaleString()}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                        {plugin.rating > 0 && (
                          <Chip
                            icon={<StarIcon sx={{ fontSize: '0.9rem', color: '#FFC107' }} />}
                            label={plugin.rating.toFixed(1)}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem' }}
                          />
                        )}
                      </Stack>

                      <Typography variant="caption" color="text.secondary">
                        {plugin.tools.length} tools
                      </Typography>

                      {plugin.required_env.length > 0 && (
                        <Box mt={1}>
                          <Tooltip title={`Required: ${plugin.required_env.join(', ')}`}>
                            <Chip
                              icon={<InfoIcon fontSize="small" />}
                              label="Requires configuration"
                              size="small"
                              color="warning"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem' }}
                            />
                          </Tooltip>
                        </Box>
                      )}
                    </CardContent>

                    <Divider />

                    <CardActions sx={{ justifyContent: 'space-between', px: 2, py: 1.5 }}>
                      <Button
                        type="button"
                        size="small"
                        startIcon={<InfoIcon />}
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          setSelectedPlugin(plugin);
                        }}
                      >
                        Details
                      </Button>
                      <Stack direction="row" spacing={1}>
                        {plugin.documentation_url && (
                          <Button
                            size="small"
                            component="a"
                            href={plugin.documentation_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            startIcon={<OpenInNewIcon />}
                          >
                            Docs
                          </Button>
                        )}
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => handleInstall(plugin)}
                          disabled={installing === plugin.id}
                        >
                          {installing === plugin.id ? 'Installing...' : 'Install'}
                        </Button>
                      </Stack>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </DialogContent>
      </Dialog>

      {/* Plugin Details Dialog */}
      {selectedPlugin && (
        <Dialog
          open={Boolean(selectedPlugin)}
          onClose={() => setSelectedPlugin(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">{selectedPlugin.name}</Typography>
              <IconButton onClick={() => setSelectedPlugin(null)} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
          </DialogTitle>
          <DialogContent>
            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Description
                </Typography>
                <Typography variant="body2">{selectedPlugin.description}</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Tools ({selectedPlugin.tools.length})
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5}>
                  {selectedPlugin.tools.map((tool) => (
                    <Chip key={tool} label={tool} size="small" variant="outlined" />
                  ))}
                </Box>
              </Box>

              {selectedPlugin.required_env.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Required Environment Variables
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5}>
                    {selectedPlugin.required_env.map((env) => (
                      <Chip key={env} label={env} size="small" color="warning" />
                    ))}
                  </Box>
                </Box>
              )}

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Security Notes
                </Typography>
                <Alert severity={selectedPlugin.security_notes.includes('⚠️') ? 'warning' : 'info'}>
                  {selectedPlugin.security_notes}
                </Alert>
              </Box>

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Dependencies
                </Typography>
                <Typography variant="caption" component="pre" sx={{ fontFamily: 'monospace' }}>
                  {JSON.stringify(selectedPlugin.dependencies, null, 2)}
                </Typography>
              </Box>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSelectedPlugin(null)}>Close</Button>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => {
                handleInstall(selectedPlugin);
                setSelectedPlugin(null);
              }}
            >
              Install
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </>
  );
};

export default PluginMarketplace;

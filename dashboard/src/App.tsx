import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Card,
  CardHeader,
  CardContent,
  Button,
  Chip,
  Alert,
  Box,
  Paper,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  TextField,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  Switch,
  FormControlLabel,
  styled,
  alpha,
  ThemeProvider,
  createTheme,
  CssBaseline,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  ViewModule as CubesIcon,
  Storage as ServerIcon,
  Code as CodeIcon,
  Stop as StopIcon,
  Sync as SyncIcon,
  Error as ErrorIcon,
  Send as SendIcon,
  Brightness4 as Brightness4Icon,
  Brightness7 as Brightness7Icon,
  Psychology as PsychologyIcon,
  Help as HelpIcon,
  PlayArrow as PlayArrowIcon,
  Info as InfoIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  AccountTree as AccountTreeIcon,
  CloudUpload as CloudUploadIcon,
  CloudDownload as CloudDownloadIcon,
  BookmarkAdd as BookmarkAddIcon,
  Bookmark as BookmarkIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
} from '@mui/icons-material';

import PluginsPanel from './components/PluginsPanel';
import Sidebar from './components/Sidebar';
import GuidedTour from './components/GuidedTour';
import NLPSettings from './components/NLPSettings';
import ExtensionsView from './views/ExtensionsView';
import { dashboardTourSteps, tours } from './tours';

// Types
interface ProjectProfile {
  name: string;
  path: string;
  project_type: string[];
  has_python: boolean;
  has_fastapi: boolean;
  has_node: boolean;
  has_react: boolean;
  has_git: boolean;
  git_branch?: string;
  git_user_email?: string;
  venv_path?: string;
  backend_port?: number;
  frontend_port?: number;
}

interface Service {
  id: string;
  name: string;
  command: string;
  cwd: string;
  port?: number;
  pid: number;
  started_at: string;
  status: string;
}

interface CommandHistory {
  command: string;
  cwd: string;
  status: string;
  exit_code?: number;
  timestamp: string;
}

interface PendingApproval {
  id: string;
  command: string;
  cwd: string;
  reason: string;
  requested_at: string;
}

interface LogEntry {
  level: string;
  message: string;
  source: string;
  timestamp: string;
}

interface RepoInfo {
  name: string;
  path: string;
  branch?: string;
  has_uncommitted_changes: boolean;
  ahead_behind?: string;
  last_commit_message?: string;
  last_commit_time?: string;
  last_commit_author?: string;
  is_git_repo: boolean;
  error?: string;
}

interface WorkspaceStatus {
  workspace_root: string;
  total_repos: number;
  repos_with_changes: number;
  repos_ahead_of_upstream: number;
  repos_need_pull: number;
  repos: RepoInfo[];
}

interface SavedCommand {
  id: string;
  name: string;
  command: string;
  cwd?: string;
  description?: string;
  created_at: string;
}

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

interface AppState {
  current_project?: ProjectProfile;
  services: Record<string, Service>;
  command_history: CommandHistory[];
  pending_approvals: PendingApproval[];
  logs: LogEntry[];
  workspace?: WorkspaceStatus;
  saved_commands?: SavedCommand[];
  plugins?: Plugin[];
}

const WS_URL = 'ws://127.0.0.1:8766';

// Styled components with macOS aesthetic
const LogEntryPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(1),
  fontSize: '0.875rem',
  fontFamily: "'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace",
  borderRadius: 8,
  border: theme.palette.mode === 'dark'
    ? '1px solid rgba(255, 255, 255, 0.08)'
    : '1px solid rgba(0, 0, 0, 0.06)',
  backgroundColor: theme.palette.mode === 'dark'
    ? 'rgba(255, 255, 255, 0.03)'
    : 'rgba(0, 0, 0, 0.02)',
}));

const CodeBox = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark'
    ? 'rgba(255, 255, 255, 0.05)'
    : 'rgba(0, 0, 0, 0.04)',
  padding: theme.spacing(1.5),
  borderRadius: 8,
  fontFamily: "'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace",
  fontSize: '0.875rem',
  overflowX: 'auto',
  border: theme.palette.mode === 'dark'
    ? '1px solid rgba(255, 255, 255, 0.08)'
    : '1px solid rgba(0, 0, 0, 0.06)',
}));

const App: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [state, setState] = useState<AppState | null>(null);
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null);
  const [commandInput, setCommandInput] = useState('');
  const [darkMode, setDarkMode] = useState(false);
  const [logFilter, setLogFilter] = useState<string>('all');
  const [selectedCommand, setSelectedCommand] = useState<CommandHistory | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [useNlp, setUseNlp] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [runTour, setRunTour] = useState(false);
  const [tourCompleted, setTourCompleted] = useState(() => {
    const completed = localStorage.getItem('tour_completed');
    return completed ? JSON.parse(completed) : {};
  });
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [commandToSave, setCommandToSave] = useState<CommandHistory | null>(null);
  const [savedCommandName, setSavedCommandName] = useState('');
  const [savedCommandDesc, setSavedCommandDesc] = useState('');
  const [currentView, setCurrentView] = useState<'dashboard' | 'plugins' | 'extensions' | 'workspace' | 'logs' | 'settings'>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [nlpSettingsOpen, setNlpSettingsOpen] = useState(false);
  const [nlpConfig, setNlpConfig] = useState<any>(null);
  const [repoFilter, setRepoFilter] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  // Create macOS-style theme
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: darkMode ? 'dark' : 'light',
          primary: {
            main: darkMode ? '#0A84FF' : '#007AFF',
            light: darkMode ? '#409CFF' : '#4DA2FF',
            dark: darkMode ? '#0066CC' : '#0051D5',
          },
          secondary: {
            main: darkMode ? '#FF453A' : '#FF3B30',
            light: darkMode ? '#FF6961' : '#FF6259',
            dark: darkMode ? '#CC2E24' : '#CC2920',
          },
          success: {
            main: darkMode ? '#32D74B' : '#34C759',
            light: darkMode ? '#5EDF6C' : '#5DD87A',
            dark: darkMode ? '#28AC3C' : '#2A9E47',
          },
          warning: {
            main: darkMode ? '#FF9F0A' : '#FF9500',
            light: darkMode ? '#FFB23B' : '#FFAC33',
            dark: darkMode ? '#CC7F08' : '#CC7700',
          },
          error: {
            main: darkMode ? '#FF453A' : '#FF3B30',
            light: darkMode ? '#FF6961' : '#FF6259',
            dark: darkMode ? '#CC2E24' : '#CC2920',
          },
          background: {
            default: darkMode ? '#1C1C1E' : '#F2F2F7',
            paper: darkMode ? '#2C2C2E' : '#FFFFFF',
          },
          divider: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)',
        },
        typography: {
          fontFamily: [
            '-apple-system',
            'BlinkMacSystemFont',
            '"SF Pro Display"',
            '"SF Pro Text"',
            '"Helvetica Neue"',
            'Arial',
            'sans-serif',
          ].join(','),
          h6: {
            fontWeight: 600,
            letterSpacing: '-0.01em',
          },
          subtitle1: {
            fontWeight: 500,
            letterSpacing: '-0.005em',
          },
          body1: {
            letterSpacing: '-0.005em',
          },
          body2: {
            letterSpacing: '-0.005em',
          },
          button: {
            textTransform: 'none',
            fontWeight: 500,
            letterSpacing: '-0.005em',
          },
        },
        shape: {
          borderRadius: 12,
        },
        components: {
          MuiCard: {
            styleOverrides: {
              root: {
                backgroundImage: 'none',
                boxShadow: darkMode
                  ? '0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2)'
                  : '0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06)',
                border: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.06)',
              },
            },
          },
          MuiButton: {
            styleOverrides: {
              root: {
                borderRadius: 8,
                padding: '6px 16px',
                fontWeight: 500,
              },
              contained: {
                boxShadow: 'none',
                '&:hover': {
                  boxShadow: 'none',
                },
              },
            },
          },
          MuiChip: {
            styleOverrides: {
              root: {
                borderRadius: 6,
                fontWeight: 500,
              },
            },
          },
          MuiPaper: {
            styleOverrides: {
              root: {
                backgroundImage: 'none',
              },
            },
          },
          MuiAppBar: {
            styleOverrides: {
              root: {
                backgroundImage: 'none',
                boxShadow: 'none',
                borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.08)',
                backdropFilter: 'blur(20px)',
                backgroundColor: darkMode ? 'rgba(28, 28, 30, 0.85)' : 'rgba(255, 255, 255, 0.85)',
                color: darkMode ? '#FFFFFF' : '#1C1C1E',
              },
            },
          },
          MuiListItem: {
            styleOverrides: {
              root: {
                borderRadius: 8,
              },
            },
          },
          MuiTextField: {
            styleOverrides: {
              root: {
                '& .MuiOutlinedInput-root': {
                  borderRadius: 8,
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: darkMode ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.3)',
                    },
                  },
                  '&.Mui-focused': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderWidth: 2,
                    },
                  },
                },
              },
            },
          },
          MuiDialog: {
            styleOverrides: {
              paper: {
                borderRadius: 12,
                boxShadow: darkMode
                  ? '0 10px 40px rgba(0, 0, 0, 0.5)'
                  : '0 10px 40px rgba(0, 0, 0, 0.15)',
              },
            },
          },
          MuiTooltip: {
            styleOverrides: {
              tooltip: {
                borderRadius: 6,
                fontSize: '0.75rem',
                padding: '6px 10px',
                backgroundColor: darkMode ? 'rgba(60, 60, 67, 0.95)' : 'rgba(60, 60, 67, 0.9)',
              },
            },
          },
          MuiAlert: {
            styleOverrides: {
              root: {
                borderRadius: 10,
              },
            },
          },
        },
      }),
    [darkMode]
  );

  const handleMessage = useCallback((data: { type: string; data: unknown }) => {
    switch (data.type) {
      case 'state':
        setState(data.data as AppState);
        break;
      case 'project_changed':
        setState((prev) =>
          prev ? { ...prev, current_project: data.data as ProjectProfile } : null
        );
        break;
      case 'service_started':
        setState((prev) => {
          if (!prev) return null;
          const svc = data.data as Service;
          return {
            ...prev,
            services: { ...prev.services, [svc.id]: svc },
          };
        });
        break;
      case 'service_stopped':
        setState((prev) => {
          if (!prev) return null;
          const { id } = data.data as { id: string };
          const services = { ...prev.services };
          delete services[id];
          return { ...prev, services };
        });
        break;
      case 'approval_required':
        setState((prev) =>
          prev
            ? {
                ...prev,
                pending_approvals: [...prev.pending_approvals, data.data as PendingApproval],
              }
            : null
        );
        break;
      case 'approval_resolved':
        setState((prev) => {
          if (!prev) return null;
          const { id } = data.data as { id: string };
          return {
            ...prev,
            pending_approvals: prev.pending_approvals.filter((a) => a.id !== id),
          };
        });
        break;
      case 'command':
        setState((prev) =>
          prev
            ? {
                ...prev,
                command_history: [...prev.command_history.slice(-49), data.data as CommandHistory],
              }
            : null
        );
        break;
      case 'log':
        setState((prev) =>
          prev
            ? {
                ...prev,
                logs: [...prev.logs.slice(-99), data.data as LogEntry],
              }
            : null
        );
        break;
      case 'workspace':
        setState((prev) =>
          prev ? { ...prev, workspace: data.data as WorkspaceStatus } : null
        );
        break;
      case 'saved_commands':
        setState((prev) =>
          prev ? { ...prev, saved_commands: data.data as SavedCommand[] } : null
        );
        break;
      case 'logs_cleared':
        setState((prev) =>
          prev ? { ...prev, logs: [] } : null
        );
        break;
      case 'plugins':
        setState((prev) =>
          prev ? { ...prev, plugins: data.data as Plugin[] } : null
        );
        break;
      case 'plugin_installed':
      case 'plugin_uninstalled':
      case 'plugin_toggled':
      case 'plugin_tool_toggled':
        // Request full plugin list update
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'list_plugins' }));
        }
        break;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setConnected(true);
      setReconnectAttempts(0);
      ws.send(JSON.stringify({ type: 'get_state' }));
      ws.send(JSON.stringify({ type: 'list_plugins' }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;

      reconnectTimeoutRef.current = window.setTimeout(() => {
        setReconnectAttempts((prev) => prev + 1);
        connect();
      }, 3000);
    };

    wsRef.current = ws;
  }, [handleMessage]);

  const sendApproval = (approvalId: string, approved: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: approved ? 'approve' : 'reject',
          approval_id: approvalId,
        })
      );
    }
    setSelectedApproval(null);
  };

  const stopService = (serviceId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'stop_service',
          service_id: serviceId,
        })
      );
    }
  };

  const sendCommand = () => {
    if (!commandInput.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'run_command',
        command: commandInput.trim(),
        use_nlp: useNlp,
      })
    );
    setCommandInput('');
  };

  const switchProject = (repoName: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'switch_project',
          repo_name: repoName,
        })
      );
    }
  };

  const clearLogs = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'clear_logs',
        })
      );
    }
  };

  const saveCommand = (cmd: CommandHistory, name: string, description?: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'save_command',
          command: cmd.command,
          cwd: cmd.cwd,
          name,
          description,
        })
      );
    }
  };

  const deleteSavedCommand = (id: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'delete_saved_command',
          id,
        })
      );
    }
  };

  const executeSavedCommand = (cmd: SavedCommand) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'run_command',
          command: cmd.command,
          cwd: cmd.cwd,
        })
      );
    }
  };

  // Plugin operations
  const handleInstallPlugin = async (gitUrl: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'install_plugin',
          git_url: gitUrl,
        })
      );
    }
  };

  const handleUninstallPlugin = async (pluginId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'uninstall_plugin',
          plugin_id: pluginId,
        })
      );
    }
  };

  const handleCreatePlugin = async (pluginData: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'execute_tool',
          tool: 'create_plugin',
          arguments: pluginData,
        })
      );
    }
  };

  const handleTogglePlugin = async (pluginId: string, enabled: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'toggle_plugin',
          plugin_id: pluginId,
          enabled: enabled,
        })
      );
    }
  };

  const handleToggleTool = async (pluginId: string, toolName: string, enabled: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'toggle_plugin_tool',
          plugin_id: pluginId,
          tool_name: toolName,
          enabled: enabled,
        })
      );
    }
  };

  const handleCommandKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendCommand();
    }
  };

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  const renderConnectionStatus = () => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      {connected ? (
        <Tooltip title="Connected to WebSocket server at ws://127.0.0.1:8766">
          <Chip
            icon={<CheckCircleIcon />}
            label="Connected"
            color="success"
            size="small"
          />
        </Tooltip>
      ) : (
        <>
          <Tooltip title="Disconnected from WebSocket server. Attempting to reconnect...">
            <Chip
              icon={<CancelIcon />}
              label={reconnectAttempts > 0 ? `Reconnecting (${reconnectAttempts})` : "Disconnected"}
              color="error"
              size="small"
            />
          </Tooltip>
          <CircularProgress size={16} />
        </>
      )}
      <Tooltip title="View documentation and feature guide">
        <IconButton size="small" onClick={() => setShowHelp(true)} color="inherit">
          <HelpIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Start guided tour">
        <IconButton size="small" onClick={startTour} color="inherit">
          <PlayArrowIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Toggle dark/light mode">
        <IconButton size="small" onClick={() => setDarkMode(!darkMode)} color="inherit">
          {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
        </IconButton>
      </Tooltip>
    </Box>
  );

  const renderProjectCard = () => {
    const project = state?.current_project;

    if (!project) {
      return (
        <Card>
          <CardHeader
            avatar={<CubesIcon />}
            title="No Project"
            subheader="Run detect_project to scan"
          />
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader
          avatar={<CubesIcon />}
          title={project.name}
          subheader={
            <Box>
              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                {project.path}
              </Typography>
              <Stack direction="row" spacing={0.5} sx={{ mt: 1 }} flexWrap="wrap">
                {project.project_type.map((t) => (
                  <Chip key={t} label={t} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.7rem' }} />
                ))}
                {project.git_branch && (
                  <Chip
                    label={`${project.git_branch}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ height: 20, fontSize: '0.7rem' }}
                  />
                )}
                {project.venv_path && (
                  <Chip
                    label="venv"
                    size="small"
                    color="success"
                    variant="outlined"
                    sx={{ height: 20, fontSize: '0.7rem' }}
                  />
                )}
              </Stack>
            </Box>
          }
        />
      </Card>
    );
  };

  const renderServicesCard = () => {
    const services = state?.services || {};
    const serviceList = Object.values(services);

    return (
      <Card>
        <CardHeader
          avatar={<ServerIcon />}
          title={`Running Services (${serviceList.length})`}
        />
        <CardContent>
          {serviceList.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="body2" color="text.secondary">
                No services running
              </Typography>
            </Box>
          ) : (
            <Stack spacing={2}>
              {serviceList.map((svc) => (
                <Paper key={svc.id} variant="outlined" sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {svc.name}
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                        <Chip label={`Port ${svc.port || 'N/A'}`} size="small" color="primary" />
                        <Chip label={`PID ${svc.pid}`} size="small" />
                      </Stack>
                    </Box>
                    <Button
                      variant="contained"
                      color="error"
                      size="small"
                      startIcon={<StopIcon />}
                      onClick={() => stopService(svc.id)}
                    >
                      Stop
                    </Button>
                  </Box>
                </Paper>
              ))}
            </Stack>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderApprovalsCard = () => {
    const approvals = state?.pending_approvals || [];

    if (approvals.length === 0) return null;

    return (
      <Box sx={{ mb: 3 }}>
        <Card>
          <CardHeader
            avatar={<WarningIcon color="warning" />}
            title={`Pending Approvals (${approvals.length})`}
          />
          <CardContent>
            <Stack spacing={2}>
              {approvals.map((approval) => (
                <Alert
                  key={approval.id}
                  severity="warning"
                  action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => setSelectedApproval(approval)}
                    >
                      Review
                    </Button>
                  }
                >
                  <Typography variant="subtitle2" fontWeight="bold">
                    {approval.reason}
                  </Typography>
                  <CodeBox sx={{ mt: 1, backgroundColor: alpha('#000', 0.05) }}>
                    {approval.command.substring(0, 60)}...
                  </CodeBox>
                </Alert>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Box>
    );
  };

  const renderCommandsPanel = () => {
    const history = state?.command_history || [];
    const recent = history.slice(-10).reverse();
    const savedCommands = state?.saved_commands || [];

    return (
      <Card>
        <CardHeader
          avatar={<CodeIcon />}
          title="Commands"
        />
        <CardContent sx={{ maxHeight: '500px', overflow: 'auto' }}>
          {/* Saved Commands Section */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <BookmarkIcon fontSize="small" />
              Saved ({savedCommands.length})
            </Typography>
            {savedCommands.length === 0 ? (
              <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', display: 'block', ml: 3 }}>
                No saved commands. Save frequently used commands from history below.
              </Typography>
            ) : (
              <List dense sx={{ bgcolor: 'action.hover', borderRadius: 2, p: 0.5 }}>
                {savedCommands.map((cmd, idx) => (
                  <React.Fragment key={cmd.id}>
                    <ListItem sx={{ pr: 1, borderRadius: 1 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <BookmarkIcon color="primary" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="body2" fontWeight="600" fontSize="0.875rem">
                            {cmd.name}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="caption" fontFamily="monospace" display="block" noWrap>
                            {cmd.command}
                          </Typography>
                        }
                      />
                      <Stack direction="row" spacing={0.5}>
                        <Tooltip title="Execute">
                          <IconButton size="small" color="primary" onClick={() => executeSavedCommand(cmd)}>
                            <PlayArrowIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton size="small" color="error" onClick={() => deleteSavedCommand(cmd.id)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </ListItem>
                    {idx < savedCommands.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Recent Commands Section */}
          <Box>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SyncIcon fontSize="small" />
              Recent ({recent.length})
            </Typography>
            {recent.length === 0 ? (
              <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', display: 'block', ml: 3 }}>
                No commands yet
              </Typography>
            ) : (
              <List dense>
                {recent.map((cmd, idx) => (
                  <React.Fragment key={`${cmd.command}-${cmd.timestamp}-${idx}`}>
                    <ListItem sx={{ pr: 1 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        {cmd.status === 'completed' ? (
                          <CheckCircleIcon color="success" fontSize="small" />
                        ) : cmd.status === 'failed' ? (
                          <ErrorIcon color="error" fontSize="small" />
                        ) : (
                          <SyncIcon fontSize="small" />
                        )}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="body2" fontFamily="monospace" fontSize="0.85rem" noWrap>
                            {cmd.command}
                          </Typography>
                        }
                      />
                      <Chip
                        label={cmd.exit_code !== undefined ? `${cmd.exit_code}` : cmd.status}
                        size="small"
                        color={
                          cmd.status === 'completed'
                            ? 'success'
                            : cmd.status === 'failed'
                            ? 'error'
                            : 'default'
                        }
                        sx={{ mr: 1, minWidth: 36 }}
                      />
                      <Tooltip title="Save command">
                        <IconButton
                          size="small"
                          onClick={() => {
                            setCommandToSave(cmd);
                            setSaveDialogOpen(true);
                          }}
                        >
                          <BookmarkAddIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </ListItem>
                    {idx < recent.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderLogs = () => {
    const logs = state?.logs || [];
    const filtered = logs.filter(log =>
      logFilter === 'all' || log.level === logFilter
    );
    const recent = filtered.slice(-50).reverse();

    return (
      <Card>
        <CardHeader
          title="Logs"
          action={
            <Stack direction="row" spacing={1}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Filter</InputLabel>
                <Select
                  value={logFilter}
                  label="Filter"
                  onChange={(e) => setLogFilter(e.target.value)}
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="INFO">Info</MenuItem>
                  <MenuItem value="WARN">Warning</MenuItem>
                  <MenuItem value="ERROR">Error</MenuItem>
                </Select>
              </FormControl>
              <Button
                size="small"
                variant="outlined"
                onClick={clearLogs}
                disabled={logs.length === 0}
              >
                Clear
              </Button>
            </Stack>
          }
        />
        <CardContent sx={{ maxHeight: '400px', overflow: 'auto', p: 0 }}>
          <Stack spacing={0.5} sx={{ p: 2 }}>
            {recent.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  No logs matching filter
                </Typography>
              </Box>
            ) : (
              recent.map((log, idx) => (
                <LogEntryPaper key={idx} variant="outlined">
                  <Typography component="span" variant="caption" color="text.secondary" sx={{ mr: 1 }}>
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </Typography>
                  <Chip
                    label={log.level}
                    size="small"
                    color={
                      log.level === 'ERROR'
                        ? 'error'
                        : log.level === 'WARN'
                        ? 'warning'
                        : 'default'
                    }
                    sx={{ mr: 1 }}
                  />
                  <Typography component="span" variant="body2">
                    {log.message}
                  </Typography>
                </LogEntryPaper>
              ))
            )}
          </Stack>
        </CardContent>
      </Card>
    );
  };

  const renderWorkspacePanel = () => {
    const workspace = state?.workspace;

    if (!workspace) {
      return (
        <Card>
          <CardHeader
            avatar={<AccountTreeIcon />}
            title="Workspace"
            subheader="No workspace detected"
          />
        </Card>
      );
    }

    const getRepoStatusColor = (repo: any) => {
      if (repo.has_uncommitted_changes) return 'warning.main';
      if (repo.ahead_behind && repo.ahead_behind.includes('behind')) return 'error.main';
      if (repo.ahead_behind && repo.ahead_behind.includes('ahead')) return 'info.main';
      return 'success.main';
    };

    const filteredRepos = workspace.repos.filter((repo: any) =>
      repo.name.toLowerCase().includes(repoFilter.toLowerCase())
    );

    return (
      <Card>
        <CardHeader
          avatar={<AccountTreeIcon />}
          title={`${workspace.total_repos} Repositories`}
          subheader={
            <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
              {workspace.repos_with_changes > 0 && (
                <Chip label={`${workspace.repos_with_changes} modified`} size="small" color="warning" sx={{ height: 18, fontSize: '0.65rem' }} />
              )}
              {workspace.repos_ahead_of_upstream > 0 && (
                <Chip label={`${workspace.repos_ahead_of_upstream} ahead`} size="small" color="info" sx={{ height: 18, fontSize: '0.65rem' }} />
              )}
              {workspace.repos_need_pull > 0 && (
                <Chip label={`${workspace.repos_need_pull} behind`} size="small" color="error" sx={{ height: 18, fontSize: '0.65rem' }} />
              )}
            </Stack>
          }
        />
        <CardContent>
          {/* Search Filter */}
          {workspace.repos.length > 6 && (
            <TextField
              size="small"
              fullWidth
              placeholder="Filter repositories..."
              value={repoFilter}
              onChange={(e) => setRepoFilter(e.target.value)}
              sx={{ mb: 2 }}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} fontSize="small" />,
              }}
            />
          )}

          {/* Compact Grid of Repo Cards */}
          <Grid container spacing={1.5}>
            {filteredRepos.slice(0, 12).map((repo: any) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={repo.name}>
                <Paper
                  onClick={() => switchProject(repo.name)}
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    borderLeft: 4,
                    borderColor: getRepoStatusColor(repo),
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'action.hover',
                      transform: 'translateY(-2px)',
                      boxShadow: 2,
                    },
                  }}
                >
                  <Stack spacing={0.5}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Typography variant="body2" fontWeight="bold" noWrap sx={{ flex: 1, pr: 1 }}>
                        {repo.name}
                      </Typography>
                      {repo.has_uncommitted_changes && (
                        <FolderOpenIcon fontSize="small" color="warning" />
                      )}
                    </Box>
                    {repo.branch && (
                      <Chip
                        label={repo.branch}
                        size="small"
                        variant="outlined"
                        sx={{ height: 18, fontSize: '0.65rem', width: 'fit-content' }}
                      />
                    )}
                    {(repo.ahead_behind && repo.ahead_behind !== 'no upstream' && repo.ahead_behind !== 'up to date') && (
                      <Typography variant="caption" color="text.secondary" noWrap>
                        {repo.ahead_behind}
                      </Typography>
                    )}
                  </Stack>
                </Paper>
              </Grid>
            ))}
          </Grid>

          {filteredRepos.length > 12 && (
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="caption" color="text.secondary">
                +{filteredRepos.length - 12} more repositories
              </Typography>
            </Box>
          )}

          {filteredRepos.length === 0 && repoFilter && (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="body2" color="text.secondary">
                No repositories match "{repoFilter}"
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  const handleSaveCommand = () => {
    if (commandToSave && savedCommandName.trim()) {
      saveCommand(commandToSave, savedCommandName.trim(), savedCommandDesc.trim() || undefined);
      setSaveDialogOpen(false);
      setCommandToSave(null);
      setSavedCommandName('');
      setSavedCommandDesc('');
    }
  };

  const handleTourComplete = () => {
    setRunTour(false);
    const updated = { ...tourCompleted, [currentView]: true };
    setTourCompleted(updated);
    localStorage.setItem('tour_completed', JSON.stringify(updated));
  };

  const startTour = () => {
    setRunTour(true);
  };

  // Auto-start tour for first-time users on dashboard view
  useEffect(() => {
    if (currentView === 'dashboard' && !tourCompleted.dashboard && connected) {
      const timer = setTimeout(() => {
        setRunTour(true);
      }, 1000); // Delay to ensure elements are rendered
      return () => clearTimeout(timer);
    }
  }, [currentView, tourCompleted, connected]);

  const renderDashboardView = () => (
    <>
      {/* Manual Command Input */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            <Stack direction="row" spacing={2} alignItems="center">
              <Tooltip title={useNlp ? "Type natural language like 'show files' or 'what's the git status'" : "Enter shell commands like 'ls -la' or 'git status'. Press Enter to execute."}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder={useNlp ? "Enter natural language command..." : "Enter shell command..."}
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  onKeyPress={handleCommandKeyPress}
                  disabled={!connected}
                  InputProps={{
                    startAdornment: useNlp ? (
                      <PsychologyIcon sx={{ mr: 1, color: 'primary.main' }} />
                    ) : (
                      <CodeIcon sx={{ mr: 1, color: 'action.disabled' }} />
                    ),
                  }}
                />
              </Tooltip>
              <Tooltip title="Execute the command (or press Enter)">
                <span>
                  <Button
                    variant="contained"
                    onClick={sendCommand}
                    disabled={!connected || !commandInput.trim()}
                    endIcon={<SendIcon />}
                  >
                    Run
                  </Button>
                </span>
              </Tooltip>
            </Stack>
            <Tooltip title="Enable to use natural language commands powered by Ollama AI. Translates plain English into shell commands or detects MCP tool requests.">
              <FormControlLabel
                control={
                  <Switch
                    checked={useNlp}
                    onChange={(e) => setUseNlp(e.target.checked)}
                    color="primary"
                  />
                }
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PsychologyIcon fontSize="small" />
                    <Typography variant="body2">
                      Natural Language Processing (AI-powered command translation)
                    </Typography>
                  </Box>
                }
              />
            </Tooltip>
          </Stack>
        </CardContent>
      </Card>

      {renderApprovalsCard()}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6} lg={4}>
          {renderProjectCard()}
        </Grid>
        <Grid item xs={12} md={6} lg={4}>
          {renderCommandsPanel()}
        </Grid>
        <Grid item xs={12} md={6} lg={4}>
          {Object.values(state?.services || {}).length > 0 && renderServicesCard()}
        </Grid>
      </Grid>
    </>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return renderDashboardView();
      case 'plugins':
        return (
          <Card>
            <CardHeader title="Plugins" />
            <CardContent>
              <PluginsPanel
                plugins={state?.plugins || []}
                onInstallPlugin={handleInstallPlugin}
                onUninstallPlugin={handleUninstallPlugin}
                onTogglePlugin={handleTogglePlugin}
                onToggleTool={handleToggleTool}
                onCreatePlugin={handleCreatePlugin}
              />
            </CardContent>
          </Card>
        );
      case 'extensions':
        return <ExtensionsView sendMessage={sendMessage} />;
      case 'workspace':
        return renderWorkspacePanel();
      case 'logs':
        return (
          <Container maxWidth="xl">
            {renderLogs()}
          </Container>
        );
      case 'settings':
        return (
          <Container maxWidth="lg">
            <Typography variant="h4" gutterBottom>
              Settings
            </Typography>
            <Stack spacing={3}>
              <Card>
                <CardHeader
                  title="Natural Language Processing"
                  subheader="Configure NLP providers for command translation"
                />
                <CardContent>
                  <Stack spacing={2}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="body1">NLP Command Translation</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Use natural language to generate shell commands with Ollama, OpenAI, Gemini, or Anthropic
                        </Typography>
                      </Box>
                      <FormControlLabel
                        control={<Switch checked={useNlp} onChange={(e) => setUseNlp(e.target.checked)} />}
                        label="Enabled"
                      />
                    </Box>
                    <Divider />
                    <Button
                      variant="outlined"
                      startIcon={<PsychologyIcon />}
                      onClick={() => setNlpSettingsOpen(true)}
                    >
                      Configure NLP Providers
                    </Button>
                    {nlpConfig && (
                      <Box>
                        <Alert severity="info" sx={{ mb: 2 }}>
                          <Typography variant="body2" fontWeight="bold">Primary Provider: {nlpConfig.primaryProvider || 'Not configured'}</Typography>
                        </Alert>
                        <Stack spacing={1}>
                          {nlpConfig.providers?.ollama?.enabled && (
                            <Typography variant="body2">
                              • Ollama: {nlpConfig.providers.ollama.model || 'codellama:7b-instruct'}
                            </Typography>
                          )}
                          {nlpConfig.providers?.openai?.enabled && (
                            <Typography variant="body2">
                              • OpenAI: {nlpConfig.providers.openai.model || 'gpt-3.5-turbo'}
                            </Typography>
                          )}
                          {nlpConfig.providers?.gemini?.enabled && (
                            <Typography variant="body2">
                              • Gemini: {nlpConfig.providers.gemini.model || 'gemini-pro'}
                            </Typography>
                          )}
                          {nlpConfig.providers?.anthropic?.enabled && (
                            <Typography variant="body2">
                              • Anthropic: {nlpConfig.providers.anthropic.model || 'claude-3-5-sonnet-20241022'}
                            </Typography>
                          )}
                          <Typography variant="caption" color="text.secondary">
                            Fallback to local: {nlpConfig.fallbackToLocal ? 'Enabled' : 'Disabled'}
                          </Typography>
                        </Stack>
                      </Box>
                    )}
                  </Stack>
                </CardContent>
              </Card>

              <Card>
                <CardHeader
                  title="Appearance"
                  subheader="Customize the dashboard appearance"
                />
                <CardContent>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={darkMode}
                        onChange={(e) => setDarkMode(e.target.checked)}
                      />
                    }
                    label="Dark Mode"
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader
                  title="About"
                  subheader="Dev Orchestrator version and information"
                />
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="body2">Version: 0.2.0</Typography>
                    <Typography variant="body2" color="text.secondary">
                      MCP server for Mac dev environment orchestration with guardrails
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          </Container>
        );
      default:
        return renderDashboardView();
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar
          open={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          currentView={currentView}
          onNavigate={(view) => setCurrentView(view as 'dashboard' | 'plugins' | 'extensions' | 'workspace' | 'logs' | 'settings')}
        />
        <Box component="main" sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
                Dev Orchestrator
              </Typography>
              {renderConnectionStatus()}
            </Toolbar>
          </AppBar>

          <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            {renderCurrentView()}
          </Container>
        </Box>
      </Box>

      {selectedApproval && (
        <Dialog
          open={true}
          onClose={() => setSelectedApproval(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Command Approval Required</DialogTitle>
          <DialogContent>
            <Stack spacing={3} sx={{ mt: 1 }}>
              <Alert severity="warning">{selectedApproval.reason}</Alert>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Command
                </Typography>
                <CodeBox>{selectedApproval.command}</CodeBox>
              </Box>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Working Directory
                </Typography>
                <CodeBox>{selectedApproval.cwd}</CodeBox>
              </Box>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSelectedApproval(null)}>Cancel</Button>
            <Button
              onClick={() => sendApproval(selectedApproval.id, false)}
              color="error"
              variant="outlined"
            >
              Reject
            </Button>
            <Button
              onClick={() => sendApproval(selectedApproval.id, true)}
              color="primary"
              variant="contained"
              autoFocus
            >
              Approve
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {selectedCommand && (
        <Dialog
          open={true}
          onClose={() => setSelectedCommand(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Command Details</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Command
                </Typography>
                <CodeBox>{selectedCommand.command}</CodeBox>
              </Box>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Working Directory
                </Typography>
                <CodeBox>{selectedCommand.cwd}</CodeBox>
              </Box>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Status
                </Typography>
                <Chip
                  label={selectedCommand.status}
                  color={
                    selectedCommand.status === 'completed'
                      ? 'success'
                      : selectedCommand.status === 'failed'
                      ? 'error'
                      : 'default'
                  }
                />
                {selectedCommand.exit_code !== undefined && (
                  <Chip label={`Exit Code: ${selectedCommand.exit_code}`} sx={{ ml: 1 }} />
                )}
              </Box>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Timestamp
                </Typography>
                <Typography variant="body2">{new Date(selectedCommand.timestamp).toLocaleString()}</Typography>
              </Box>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSelectedCommand(null)}>Close</Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Save Command Dialog */}
      <Dialog
        open={saveDialogOpen}
        onClose={() => {
          setSaveDialogOpen(false);
          setCommandToSave(null);
          setSavedCommandName('');
          setSavedCommandDesc('');
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Save Command</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            {commandToSave && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Command
                </Typography>
                <CodeBox>{commandToSave.command}</CodeBox>
              </Box>
            )}
            <TextField
              label="Name"
              value={savedCommandName}
              onChange={(e) => setSavedCommandName(e.target.value)}
              fullWidth
              required
              placeholder="e.g., 'Git status', 'Run tests'"
              autoFocus
            />
            <TextField
              label="Description (optional)"
              value={savedCommandDesc}
              onChange={(e) => setSavedCommandDesc(e.target.value)}
              fullWidth
              multiline
              rows={2}
              placeholder="Brief description of what this command does"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setSaveDialogOpen(false);
              setCommandToSave(null);
              setSavedCommandName('');
              setSavedCommandDesc('');
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveCommand}
            variant="contained"
            disabled={!savedCommandName.trim()}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Help/Documentation Dialog */}
      <Dialog
        open={showHelp}
        onClose={() => setShowHelp(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HelpIcon color="primary" />
            Dashboard Documentation & Features
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            {/* Command Execution Section */}
            <Box>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SendIcon color="primary" fontSize="small" />
                Command Execution
              </Typography>
              <Typography variant="body2" paragraph>
                Execute shell commands directly from the dashboard with two modes:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CodeIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary="Shell Mode (Default)"
                    secondary="Execute standard shell commands like 'ls -la', 'git status', or 'npm install'"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><PsychologyIcon fontSize="small" color="primary" /></ListItemIcon>
                  <ListItemText
                    primary="Natural Language Mode (NLP)"
                    secondary="Use plain English like 'show directory contents' or 'what's the git status'. Powered by Ollama AI."
                  />
                </ListItem>
              </List>
              <Alert severity="info" sx={{ mt: 1 }}>
                💡 Press Enter to execute commands quickly
              </Alert>
            </Box>

            <Divider />

            {/* NLP Feature */}
            <Box>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PsychologyIcon color="primary" fontSize="small" />
                Natural Language Processing
              </Typography>
              <Typography variant="body2" paragraph>
                When enabled, the NLP feature translates your natural language input into shell commands or MCP tool calls:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Shell Translation"
                    secondary="'list files' → 'ls -la' • 'get current branch' → 'git branch --show-current'"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Tool Detection"
                    secondary="'start the backend' → detects 'start_service' MCP tool with parameters"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Confidence Scoring"
                    secondary="Each translation shows confidence level (0.0-1.0) in the logs"
                  />
                </ListItem>
              </List>
            </Box>

            <Divider />

            {/* Project Detection */}
            <Box>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CubesIcon color="primary" fontSize="small" />
                Project Detection
              </Typography>
              <Typography variant="body2" paragraph>
                Automatically detects your project type and configuration including:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText primary="Python (FastAPI, Django, Flask)" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Node.js (React, Express)" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Git repository and branch info" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Virtual environment detection" />
                </ListItem>
              </List>
              <Typography variant="body2" color="text.secondary">
                Use the MCP server's 'detect_project' tool to scan your workspace
              </Typography>
            </Box>

            <Divider />

            {/* Services */}
            <Box>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ServerIcon color="primary" fontSize="small" />
                Running Services
              </Typography>
              <Typography variant="body2" paragraph>
                Monitor and control background services:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="View active services"
                    secondary="See process IDs (PID), ports, and start times"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Stop services"
                    secondary="Click the red Stop button to terminate a service"
                  />
                </ListItem>
              </List>
            </Box>

            <Divider />

            {/* Guardrails */}
            <Box>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarningIcon color="warning" fontSize="small" />
                Guardrails & Approvals
              </Typography>
              <Typography variant="body2" paragraph>
                Dangerous commands require your explicit approval:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Blocked Commands"
                    secondary="Commands like 'rm -rf /' are automatically blocked"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Approval Required"
                    secondary="Commands like 'git push --force' or 'sudo' require confirmation"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Review Dialog"
                    secondary="See full command details before approving or rejecting"
                  />
                </ListItem>
              </List>
              <Alert severity="warning" sx={{ mt: 1 }}>
                ⚠️ Always review approval dialogs carefully before confirming
              </Alert>
            </Box>

            <Divider />

            {/* Features Overview */}
            <Box>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <InfoIcon color="primary" fontSize="small" />
                Additional Features
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><Brightness4Icon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary="Dark/Light Mode"
                    secondary="Toggle theme with the sun/moon icon"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><ErrorIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary="Log Filtering"
                    secondary="Filter logs by level: All, Info, Warning, Error"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CodeIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary="Command History"
                    secondary="Click any command to see full details and exit codes"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><SyncIcon fontSize="small" /></ListItemIcon>
                  <ListItemText
                    primary="Auto Reconnect"
                    secondary="Dashboard automatically reconnects to WebSocket server"
                  />
                </ListItem>
              </List>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setShowHelp(false); startTour(); }} startIcon={<PlayArrowIcon />}>
            Start Tour
          </Button>
          <Button onClick={() => setShowHelp(false)} variant="contained">
            Got It
          </Button>
        </DialogActions>
      </Dialog>

      {/* Guided Tour with Joyride */}
      <GuidedTour
        run={runTour}
        onComplete={handleTourComplete}
        steps={dashboardTourSteps}
      />

      {/* NLP Settings Dialog */}
      <NLPSettings
        open={nlpSettingsOpen}
        onClose={() => setNlpSettingsOpen(false)}
        onSave={(settings) => {
          setNlpConfig(settings);
          sendMessage({ type: 'configure_nlp', config: settings });
          setNlpSettingsOpen(false);
        }}
        currentSettings={nlpConfig}
      />
    </ThemeProvider>
  );
};

export default App;

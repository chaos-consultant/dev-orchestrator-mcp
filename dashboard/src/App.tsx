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
} from '@mui/icons-material';

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

interface AppState {
  current_project?: ProjectProfile;
  services: Record<string, Service>;
  command_history: CommandHistory[];
  pending_approvals: PendingApproval[];
  logs: LogEntry[];
  workspace?: WorkspaceStatus;
  saved_commands?: SavedCommand[];
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
  const [showTour, setShowTour] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [commandToSave, setCommandToSave] = useState<CommandHistory | null>(null);
  const [savedCommandName, setSavedCommandName] = useState('');
  const [savedCommandDesc, setSavedCommandDesc] = useState('');
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
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setConnected(true);
      setReconnectAttempts(0);
      ws.send(JSON.stringify({ type: 'get_state' }));
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
        <IconButton size="small" onClick={() => setShowTour(true)} color="inherit">
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
          <CardHeader title="Current Project" />
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CubesIcon sx={{ fontSize: 60, color: 'action.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No Project Detected
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Run <code>detect_project</code> to scan a directory.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader
          avatar={<CubesIcon />}
          title={project.name}
        />
        <CardContent>
          <Stack spacing={2}>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Path</Typography>
              <CodeBox>{project.path}</CodeBox>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>Type</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                {project.project_type.map((t) => (
                  <Chip key={t} label={t} color="primary" size="small" />
                ))}
              </Stack>
            </Box>
            {project.git_branch && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Git Branch</Typography>
                <Typography variant="body2">{project.git_branch}</Typography>
              </Box>
            )}
            {project.git_user_email && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Git User</Typography>
                <Typography variant="body2">{project.git_user_email}</Typography>
              </Box>
            )}
            {project.venv_path && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Virtual Environment</Typography>
                <Chip label="Active" color="success" size="small" />
              </Box>
            )}
          </Stack>
        </CardContent>
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

  const renderCommandHistory = () => {
    const history = state?.command_history || [];
    const recent = history.slice(-10).reverse();

    return (
      <Card>
        <CardHeader
          avatar={<CodeIcon />}
          title="Recent Commands"
        />
        <CardContent sx={{ maxHeight: '300px', overflow: 'auto' }}>
          {recent.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="body2" color="text.secondary">
                No commands yet
              </Typography>
            </Box>
          ) : (
            <List dense>
              {recent.map((cmd, idx) => (
                <React.Fragment key={idx}>
                  <ListItem
                    sx={{ pr: 1 }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
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
                        <Typography variant="body2" fontFamily="monospace" fontSize="0.85rem">
                          {cmd.command.substring(0, 40)}
                          {cmd.command.length > 40 ? '...' : ''}
                        </Typography>
                      }
                    />
                    <Chip
                      label={cmd.exit_code !== undefined ? `exit ${cmd.exit_code}` : cmd.status}
                      size="small"
                      color={
                        cmd.status === 'completed'
                          ? 'success'
                          : cmd.status === 'failed'
                          ? 'error'
                          : 'default'
                      }
                      sx={{ mr: 1 }}
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
          />
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <AccountTreeIcon sx={{ fontSize: 60, color: 'action.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No Workspace Detected
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Workspace discovery happens automatically
              </Typography>
            </Box>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader
          avatar={<AccountTreeIcon />}
          title={`Workspace (${workspace.total_repos} repos)`}
          subheader={workspace.workspace_root}
        />
        <CardContent>
          {/* Summary Stats */}
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            {workspace.repos_with_changes > 0 && (
              <Chip
                icon={<WarningIcon />}
                label={`${workspace.repos_with_changes} with changes`}
                color="warning"
                size="small"
              />
            )}
            {workspace.repos_ahead_of_upstream > 0 && (
              <Chip
                icon={<CloudUploadIcon />}
                label={`${workspace.repos_ahead_of_upstream} ahead`}
                color="info"
                size="small"
              />
            )}
            {workspace.repos_need_pull > 0 && (
              <Chip
                icon={<CloudDownloadIcon />}
                label={`${workspace.repos_need_pull} behind`}
                color="error"
                size="small"
              />
            )}
          </Stack>

          {/* Repo List */}
          <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
            <List dense>
              {workspace.repos.slice(0, 10).map((repo, idx) => (
                <React.Fragment key={repo.name}>
                  <ListItem
                    onClick={() => switchProject(repo.name)}
                    sx={{
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {repo.has_uncommitted_changes ? (
                        <FolderOpenIcon color="warning" fontSize="small" />
                      ) : (
                        <FolderIcon color="action" fontSize="small" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight={repo.has_uncommitted_changes ? 'bold' : 'normal'}>
                            {repo.name}
                          </Typography>
                          {repo.branch && (
                            <Chip
                              label={repo.branch}
                              size="small"
                              variant="outlined"
                              sx={{ height: 20, fontSize: '0.7rem' }}
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                          {repo.has_uncommitted_changes && (
                            <Chip label="uncommitted" size="small" color="warning" sx={{ height: 18, fontSize: '0.65rem' }} />
                          )}
                          {repo.ahead_behind && repo.ahead_behind !== 'no upstream' && repo.ahead_behind !== 'up to date' && (
                            <Chip label={repo.ahead_behind} size="small" color="info" sx={{ height: 18, fontSize: '0.65rem' }} />
                          )}
                          {repo.last_commit_time && (
                            <Typography variant="caption" color="text.secondary">
                              {repo.last_commit_time}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  {idx < Math.min(workspace.repos.length, 10) - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
            {workspace.repos.length > 10 && (
              <Box sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  ... and {workspace.repos.length - 10} more repositories
                </Typography>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderSavedCommands = () => {
    const savedCommands = state?.saved_commands || [];

    return (
      <Card>
        <CardHeader
          avatar={<BookmarkIcon />}
          title={`Saved Commands (${savedCommands.length})`}
        />
        <CardContent>
          {savedCommands.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <BookmarkIcon sx={{ fontSize: 60, color: 'action.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No Saved Commands
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Save frequently used commands from history
              </Typography>
            </Box>
          ) : (
            <List dense>
              {savedCommands.map((cmd, idx) => (
                <React.Fragment key={cmd.id}>
                  <ListItem sx={{ pr: 1 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <BookmarkIcon color="primary" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Typography variant="body2" fontWeight="bold">
                          {cmd.name}
                        </Typography>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" fontFamily="monospace" display="block">
                            {cmd.command.substring(0, 50)}
                            {cmd.command.length > 50 ? '...' : ''}
                          </Typography>
                          {cmd.description && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              {cmd.description}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <Stack direction="row" spacing={1}>
                      <Tooltip title="Execute command">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => executeSavedCommand(cmd)}
                        >
                          <PlayArrowIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => deleteSavedCommand(cmd.id)}
                        >
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

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh' }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
              Dev Orchestrator
            </Typography>
            {renderConnectionStatus()}
          </Toolbar>
        </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
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
            {renderServicesCard()}
          </Grid>
          <Grid item xs={12} md={6} lg={4}>
            {renderCommandHistory()}
          </Grid>
          <Grid item xs={12} md={6}>
            {renderSavedCommands()}
          </Grid>
          <Grid item xs={12}>
            {renderWorkspacePanel()}
          </Grid>
          <Grid item xs={12}>
            {renderLogs()}
          </Grid>
        </Grid>
      </Container>

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
          <Button onClick={() => { setShowHelp(false); setShowTour(true); }} startIcon={<PlayArrowIcon />}>
            Start Tour
          </Button>
          <Button onClick={() => setShowHelp(false)} variant="contained">
            Got It
          </Button>
        </DialogActions>
      </Dialog>

      {/* Guided Tour Overlay */}
      {showTour && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            bgcolor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          onClick={() => setShowTour(false)}
        >
          <Paper
            sx={{ p: 4, maxWidth: 500, m: 2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PlayArrowIcon color="primary" />
              Dashboard Tour
            </Typography>
            <Typography variant="body1" paragraph>
              Welcome to the Dev Orchestrator Dashboard!
            </Typography>
            <List>
              <ListItem>
                <ListItemText
                  primary="1. Try the Command Input"
                  secondary="Type 'ls -la' or enable NLP and try 'show files'"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="2. Toggle NLP Mode"
                  secondary="Enable the switch to use natural language"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="3. Check the Logs"
                  secondary="Filter logs to see command execution details"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="4. View Command History"
                  secondary="Click any command to see full details"
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="5. Try Dark Mode"
                  secondary="Toggle the theme with the sun/moon icon"
                />
              </ListItem>
            </List>
            <Stack direction="row" spacing={2} justifyContent="flex-end" sx={{ mt: 3 }}>
              <Button onClick={() => setShowTour(false)} variant="outlined">
                Skip Tour
              </Button>
              <Button onClick={() => setShowTour(false)} variant="contained">
                Let's Go!
              </Button>
            </Stack>
          </Paper>
        </Box>
      )}
      </Box>
    </ThemeProvider>
  );
};

export default App;

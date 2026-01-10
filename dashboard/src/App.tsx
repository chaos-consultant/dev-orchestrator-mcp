import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  styled,
  alpha,
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

interface AppState {
  current_project?: ProjectProfile;
  services: Record<string, Service>;
  command_history: CommandHistory[];
  pending_approvals: PendingApproval[];
  logs: LogEntry[];
}

const WS_URL = 'ws://127.0.0.1:8766';

// Styled components
const LogEntryPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(1),
  fontSize: '0.875rem',
  fontFamily: 'monospace',
}));

const CodeBox = styled(Box)(({ theme }) => ({
  backgroundColor: alpha(theme.palette.grey[900], 0.05),
  padding: theme.spacing(1.5),
  borderRadius: theme.shape.borderRadius,
  fontFamily: 'monospace',
  fontSize: '0.875rem',
  overflowX: 'auto',
}));

const App: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [state, setState] = useState<AppState | null>(null);
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: 'get_state' }));
    };

    ws.onclose = () => {
      setConnected(false);
      reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    wsRef.current = ws;
  }, []);

  const handleMessage = (data: { type: string; data: unknown }) => {
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
    }
  };

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
        <Chip
          icon={<CheckCircleIcon />}
          label="Connected"
          color="success"
          size="small"
        />
      ) : (
        <>
          <Chip
            icon={<CancelIcon />}
            label="Disconnected"
            color="error"
            size="small"
          />
          <CircularProgress size={16} />
        </>
      )}
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
                  <ListItem>
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
                          {cmd.command.substring(0, 50)}
                          {cmd.command.length > 50 ? '...' : ''}
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
                    />
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
    const recent = logs.slice(-50).reverse();

    return (
      <Card>
        <CardHeader title="Logs" />
        <CardContent sx={{ maxHeight: '400px', overflow: 'auto', p: 0 }}>
          <Stack spacing={0.5} sx={{ p: 2 }}>
            {recent.map((log, idx) => (
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
            ))}
          </Stack>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🔧 Dev Orchestrator
          </Typography>
          {renderConnectionStatus()}
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
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
    </Box>
  );
};

export default App;

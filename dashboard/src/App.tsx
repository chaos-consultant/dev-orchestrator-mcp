import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Page,
  PageSection,
  Masthead,
  MastheadMain,
  MastheadBrand,
  MastheadContent,
  Brand,
  Card,
  CardTitle,
  CardBody,
  CardHeader,
  Grid,
  GridItem,
  Title,
  Label,
  LabelGroup,
  Button,
  Alert,
  AlertGroup,
  AlertActionCloseButton,
  DescriptionList,
  DescriptionListGroup,
  DescriptionListTerm,
  DescriptionListDescription,
  EmptyState,
  EmptyStateHeader,
  EmptyStateIcon,
  EmptyStateBody,
  Spinner,
  Split,
  SplitItem,
  Stack,
  StackItem,
  Panel,
  PanelMain,
  PanelMainBody,
  Flex,
  FlexItem,
  Divider,
  Modal,
  ModalVariant,
  CodeBlock,
  CodeBlockCode,
} from '@patternfly/react-core';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  TimesCircleIcon,
  CubesIcon,
  ServerIcon,
  CodeIcon,
  PlayIcon,
  StopIcon,
  SyncIcon,
} from '@patternfly/react-icons';

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
      // Reconnect after 3 seconds
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
    <Split hasGutter>
      <SplitItem>
        {connected ? (
          <Label color="green" icon={<CheckCircleIcon />}>
            Connected
          </Label>
        ) : (
          <Label color="red" icon={<TimesCircleIcon />}>
            Disconnected
          </Label>
        )}
      </SplitItem>
      {!connected && (
        <SplitItem>
          <Spinner size="sm" aria-label="Reconnecting" />
        </SplitItem>
      )}
    </Split>
  );

  const renderProjectCard = () => {
    const project = state?.current_project;

    if (!project) {
      return (
        <Card>
          <CardTitle>Current Project</CardTitle>
          <CardBody>
            <EmptyState>
              <EmptyStateHeader
                titleText="No Project Detected"
                icon={<EmptyStateIcon icon={CubesIcon} />}
              />
              <EmptyStateBody>
                Run <code>detect_project</code> to scan a directory.
              </EmptyStateBody>
            </EmptyState>
          </CardBody>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <CubesIcon /> {project.name}
          </CardTitle>
        </CardHeader>
        <CardBody>
          <DescriptionList isHorizontal>
            <DescriptionListGroup>
              <DescriptionListTerm>Path</DescriptionListTerm>
              <DescriptionListDescription>
                <code>{project.path}</code>
              </DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>Type</DescriptionListTerm>
              <DescriptionListDescription>
                <LabelGroup>
                  {project.project_type.map((t) => (
                    <Label key={t} color="blue">
                      {t}
                    </Label>
                  ))}
                </LabelGroup>
              </DescriptionListDescription>
            </DescriptionListGroup>
            {project.git_branch && (
              <DescriptionListGroup>
                <DescriptionListTerm>Git Branch</DescriptionListTerm>
                <DescriptionListDescription>{project.git_branch}</DescriptionListDescription>
              </DescriptionListGroup>
            )}
            {project.git_user_email && (
              <DescriptionListGroup>
                <DescriptionListTerm>Git User</DescriptionListTerm>
                <DescriptionListDescription>{project.git_user_email}</DescriptionListDescription>
              </DescriptionListGroup>
            )}
            {project.venv_path && (
              <DescriptionListGroup>
                <DescriptionListTerm>Virtual Env</DescriptionListTerm>
                <DescriptionListDescription>
                  <Label color="green">Active</Label>
                </DescriptionListDescription>
              </DescriptionListGroup>
            )}
          </DescriptionList>
        </CardBody>
      </Card>
    );
  };

  const renderServicesCard = () => {
    const services = state?.services || {};
    const serviceList = Object.values(services);

    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <ServerIcon /> Running Services ({serviceList.length})
          </CardTitle>
        </CardHeader>
        <CardBody>
          {serviceList.length === 0 ? (
            <EmptyState variant="xs">
              <EmptyStateHeader titleText="No services running" />
            </EmptyState>
          ) : (
            <Stack hasGutter>
              {serviceList.map((svc) => (
                <StackItem key={svc.id}>
                  <Panel variant="raised">
                    <PanelMain>
                      <PanelMainBody>
                        <Flex justifyContent={{ default: 'justifyContentSpaceBetween' }}>
                          <FlexItem>
                            <Stack>
                              <StackItem>
                                <strong>{svc.name}</strong>
                              </StackItem>
                              <StackItem>
                                <Label color="blue">Port {svc.port || 'N/A'}</Label>{' '}
                                <Label>PID {svc.pid}</Label>
                              </StackItem>
                            </Stack>
                          </FlexItem>
                          <FlexItem>
                            <Button variant="danger" size="sm" icon={<StopIcon />}>
                              Stop
                            </Button>
                          </FlexItem>
                        </Flex>
                      </PanelMainBody>
                    </PanelMain>
                  </Panel>
                </StackItem>
              ))}
            </Stack>
          )}
        </CardBody>
      </Card>
    );
  };

  const renderApprovalsCard = () => {
    const approvals = state?.pending_approvals || [];

    if (approvals.length === 0) return null;

    return (
      <Card className="approval-card">
        <CardHeader>
          <CardTitle>
            <ExclamationTriangleIcon color="var(--pf-t--global--color--status--warning--default)" />{' '}
            Pending Approvals ({approvals.length})
          </CardTitle>
        </CardHeader>
        <CardBody>
          <AlertGroup>
            {approvals.map((approval) => (
              <Alert
                key={approval.id}
                variant="warning"
                title={approval.reason}
                actionLinks={
                  <>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setSelectedApproval(approval)}
                    >
                      Review
                    </Button>
                  </>
                }
              >
                <code>{approval.command.substring(0, 60)}...</code>
              </Alert>
            ))}
          </AlertGroup>
        </CardBody>
      </Card>
    );
  };

  const renderCommandHistory = () => {
    const history = state?.command_history || [];
    const recent = history.slice(-10).reverse();

    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <CodeIcon /> Recent Commands
          </CardTitle>
        </CardHeader>
        <CardBody style={{ maxHeight: '300px', overflow: 'auto' }}>
          {recent.length === 0 ? (
            <EmptyState variant="xs">
              <EmptyStateHeader titleText="No commands yet" />
            </EmptyState>
          ) : (
            <Stack>
              {recent.map((cmd, idx) => (
                <StackItem key={idx}>
                  <Flex>
                    <FlexItem>
                      {cmd.status === 'completed' ? (
                        <CheckCircleIcon color="green" />
                      ) : cmd.status === 'failed' ? (
                        <TimesCircleIcon color="red" />
                      ) : (
                        <SyncIcon />
                      )}
                    </FlexItem>
                    <FlexItem grow={{ default: 'grow' }}>
                      <code style={{ fontSize: '0.85rem' }}>
                        {cmd.command.substring(0, 50)}
                        {cmd.command.length > 50 ? '...' : ''}
                      </code>
                    </FlexItem>
                    <FlexItem>
                      <Label
                        color={
                          cmd.status === 'completed'
                            ? 'green'
                            : cmd.status === 'failed'
                            ? 'red'
                            : 'grey'
                        }
                      >
                        {cmd.exit_code !== undefined ? `exit ${cmd.exit_code}` : cmd.status}
                      </Label>
                    </FlexItem>
                  </Flex>
                  <Divider />
                </StackItem>
              ))}
            </Stack>
          )}
        </CardBody>
      </Card>
    );
  };

  const renderLogs = () => {
    const logs = state?.logs || [];
    const recent = logs.slice(-50).reverse();

    return (
      <Card>
        <CardHeader>
          <CardTitle>Logs</CardTitle>
        </CardHeader>
        <CardBody style={{ maxHeight: '400px', overflow: 'auto', padding: 0 }}>
          {recent.map((log, idx) => (
            <div
              key={idx}
              className={`log-entry log-${log.level.toLowerCase()}`}
            >
              <span style={{ color: 'var(--pf-t--global--color--nonstatus--gray--default)' }}>
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>{' '}
              <Label
                isCompact
                color={
                  log.level === 'ERROR'
                    ? 'red'
                    : log.level === 'WARN'
                    ? 'orange'
                    : 'grey'
                }
              >
                {log.level}
              </Label>{' '}
              <span>{log.message}</span>
            </div>
          ))}
        </CardBody>
      </Card>
    );
  };

  return (
    <Page
      className="dashboard-page"
      masthead={
        <Masthead>
          <MastheadMain>
            <MastheadBrand>
              <Title headingLevel="h1" size="lg">
                🔧 Dev Orchestrator
              </Title>
            </MastheadBrand>
          </MastheadMain>
          <MastheadContent>{renderConnectionStatus()}</MastheadContent>
        </Masthead>
      }
    >
      <PageSection>
        {renderApprovalsCard()}
      </PageSection>

      <PageSection>
        <Grid hasGutter>
          <GridItem md={6} lg={4}>
            {renderProjectCard()}
          </GridItem>
          <GridItem md={6} lg={4}>
            {renderServicesCard()}
          </GridItem>
          <GridItem md={6} lg={4}>
            {renderCommandHistory()}
          </GridItem>
          <GridItem span={12}>
            {renderLogs()}
          </GridItem>
        </Grid>
      </PageSection>

      {selectedApproval && (
        <Modal
          variant={ModalVariant.medium}
          title="Command Approval Required"
          isOpen={true}
          onClose={() => setSelectedApproval(null)}
          actions={[
            <Button
              key="approve"
              variant="primary"
              onClick={() => sendApproval(selectedApproval.id, true)}
            >
              Approve
            </Button>,
            <Button
              key="reject"
              variant="danger"
              onClick={() => sendApproval(selectedApproval.id, false)}
            >
              Reject
            </Button>,
            <Button
              key="cancel"
              variant="link"
              onClick={() => setSelectedApproval(null)}
            >
              Cancel
            </Button>,
          ]}
        >
          <Stack hasGutter>
            <StackItem>
              <Alert variant="warning" title={selectedApproval.reason} isInline />
            </StackItem>
            <StackItem>
              <Title headingLevel="h4">Command</Title>
              <CodeBlock>
                <CodeBlockCode>{selectedApproval.command}</CodeBlockCode>
              </CodeBlock>
            </StackItem>
            <StackItem>
              <Title headingLevel="h4">Working Directory</Title>
              <code>{selectedApproval.cwd}</code>
            </StackItem>
          </Stack>
        </Modal>
      )}
    </Page>
  );
};

export default App;

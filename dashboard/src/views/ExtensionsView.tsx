import React, { useState } from 'react';
import {
  Container,
  Grid,
  Card,
  CardHeader,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Stack,
  Typography,
  Alert,
  Box,
  Chip,
  CircularProgress,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Widgets as WidgetsIcon,
  AccountTree as WorkflowIcon,
  Link as IntegrationIcon,
  Add as AddIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

interface ExtensionsViewProps {
  sendMessage: (message: any) => void;
}

type ExtensionType = 'widget' | 'workflow' | 'integration';

const ExtensionsView: React.FC<ExtensionsViewProps> = ({ sendMessage }) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [showCreator, setShowCreator] = useState(false);
  const [creatorType, setCreatorType] = useState<ExtensionType>('widget');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Widget form state
  const [widgetName, setWidgetName] = useState('');
  const [widgetDescription, setWidgetDescription] = useState('');
  const [widgetAuthor, setWidgetAuthor] = useState('');
  const [widgetCategory, setWidgetCategory] = useState('monitoring');
  const [widgetTemplateType, setWidgetTemplateType] = useState<'basic' | 'interactive' | 'realtime'>('basic');

  // Workflow form state
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');

  // Integration form state
  const [integrationName, setIntegrationName] = useState('');
  const [integrationDescription, setIntegrationDescription] = useState('');

  const handleOpenCreator = (type: ExtensionType) => {
    setCreatorType(type);
    setShowCreator(true);
    setError(null);
    setSuccess(false);
  };

  const handleCloseCreator = () => {
    if (!creating) {
      setShowCreator(false);
      // Reset all forms
      setWidgetName('');
      setWidgetDescription('');
      setWidgetAuthor('');
      setWidgetCategory('monitoring');
      setWidgetTemplateType('basic');
      setWorkflowName('');
      setWorkflowDescription('');
      setIntegrationName('');
      setIntegrationDescription('');
      setError(null);
      setSuccess(false);
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    setError(null);

    try {
      let toolName: string;
      let args: any;

      if (creatorType === 'widget') {
        if (!widgetName.trim()) {
          setError('Widget name is required');
          setCreating(false);
          return;
        }
        toolName = 'create_widget';
        args = {
          name: widgetName.trim(),
          description: widgetDescription.trim() || 'A custom widget',
          author: widgetAuthor.trim() || 'Anonymous',
          category: widgetCategory,
          template_type: widgetTemplateType,
        };
      } else if (creatorType === 'workflow') {
        if (!workflowName.trim()) {
          setError('Workflow name is required');
          setCreating(false);
          return;
        }
        toolName = 'create_workflow';
        args = {
          name: workflowName.trim(),
          description: workflowDescription.trim() || 'A custom workflow',
        };
      } else {
        if (!integrationName.trim()) {
          setError('Integration name is required');
          setCreating(false);
          return;
        }
        toolName = 'create_integration';
        args = {
          name: integrationName.trim(),
          description: integrationDescription.trim() || 'A custom integration',
        };
      }

      sendMessage({
        type: 'execute_tool',
        tool: toolName,
        arguments: args,
      });

      setSuccess(true);
      setTimeout(() => {
        handleCloseCreator();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create extension');
    } finally {
      setCreating(false);
    }
  };

  const renderCreatorForm = () => {
    if (creatorType === 'widget') {
      return (
        <Stack spacing={3}>
          <TextField
            autoFocus
            fullWidth
            label="Widget Name"
            placeholder="service-health-monitor"
            value={widgetName}
            onChange={(e) => setWidgetName(e.target.value)}
            helperText="Use lowercase with hyphens"
          />
          <TextField
            fullWidth
            label="Description"
            placeholder="Monitor service health and uptime"
            value={widgetDescription}
            onChange={(e) => setWidgetDescription(e.target.value)}
            multiline
            rows={2}
          />
          <TextField
            fullWidth
            label="Author"
            placeholder="Your Name"
            value={widgetAuthor}
            onChange={(e) => setWidgetAuthor(e.target.value)}
          />
          <TextField
            select
            fullWidth
            label="Category"
            value={widgetCategory}
            onChange={(e) => setWidgetCategory(e.target.value)}
          >
            <MenuItem value="monitoring">Monitoring</MenuItem>
            <MenuItem value="productivity">Productivity</MenuItem>
            <MenuItem value="analytics">Analytics</MenuItem>
            <MenuItem value="utility">Utility</MenuItem>
          </TextField>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Template Type
            </Typography>
            <Stack direction="row" spacing={2}>
              {['basic', 'interactive', 'realtime'].map((type) => (
                <Box
                  key={type}
                  onClick={() => setWidgetTemplateType(type as any)}
                  sx={{
                    flex: 1,
                    p: 2,
                    border: '2px solid',
                    borderColor: widgetTemplateType === type ? 'primary.main' : 'divider',
                    borderRadius: 2,
                    cursor: 'pointer',
                    '&:hover': { borderColor: 'primary.main' },
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                    {type}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        </Stack>
      );
    } else if (creatorType === 'workflow') {
      return (
        <Stack spacing={3}>
          <TextField
            autoFocus
            fullWidth
            label="Workflow Name"
            placeholder="deploy-production"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            helperText="Use lowercase with hyphens"
          />
          <TextField
            fullWidth
            label="Description"
            placeholder="Deploy application to production environment"
            value={workflowDescription}
            onChange={(e) => setWorkflowDescription(e.target.value)}
            multiline
            rows={3}
          />
          <Alert severity="info">
            After creation, edit the generated YAML file to define workflow steps, parameters, and conditions.
          </Alert>
        </Stack>
      );
    } else {
      return (
        <Stack spacing={3}>
          <TextField
            autoFocus
            fullWidth
            label="Integration Name"
            placeholder="custom-notifier"
            value={integrationName}
            onChange={(e) => setIntegrationName(e.target.value)}
            helperText="Use lowercase with hyphens"
          />
          <TextField
            fullWidth
            label="Description"
            placeholder="Send notifications to custom service"
            value={integrationDescription}
            onChange={(e) => setIntegrationDescription(e.target.value)}
            multiline
            rows={3}
          />
          <Alert severity="info">
            After creation, edit the generated Python file to implement event handlers and configuration.
          </Alert>
        </Stack>
      );
    }
  };

  const getCreatorTitle = () => {
    switch (creatorType) {
      case 'widget':
        return 'Create New Widget';
      case 'workflow':
        return 'Create New Workflow';
      case 'integration':
        return 'Create New Integration';
      default:
        return 'Create Extension';
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Extensions
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Create custom widgets, workflows, and integrations to extend Dev Orchestrator
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Widgets Card */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<WidgetsIcon color="primary" />}
              title="Widgets"
              subheader="Custom dashboard components"
            />
            <CardContent>
              <Typography variant="body2" color="text.secondary" paragraph>
                Create React components to display custom data and visualizations on your dashboard.
              </Typography>
              <Stack spacing={1}>
                <Chip label="Basic - Simple display" size="small" />
                <Chip label="Interactive - With actions" size="small" />
                <Chip label="Realtime - Auto-updating" size="small" />
              </Stack>
              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                sx={{ mt: 2 }}
                onClick={() => handleOpenCreator('widget')}
              >
                Create Widget
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Workflows Card */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<WorkflowIcon color="primary" />}
              title="Workflows"
              subheader="Multi-step command sequences"
            />
            <CardContent>
              <Typography variant="body2" color="text.secondary" paragraph>
                Define YAML-based workflows with parameters, conditionals, and approval steps.
              </Typography>
              <Stack spacing={1}>
                <Chip label="YAML syntax" size="small" />
                <Chip label="Jinja2 templating" size="small" />
                <Chip label="Approval gates" size="small" />
              </Stack>
              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                sx={{ mt: 2 }}
                onClick={() => handleOpenCreator('workflow')}
              >
                Create Workflow
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Integrations Card */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<IntegrationIcon color="primary" />}
              title="Integrations"
              subheader="External service connections"
            />
            <CardContent>
              <Typography variant="body2" color="text.secondary" paragraph>
                Connect to external services with event handlers and custom logic.
              </Typography>
              <Stack spacing={1}>
                <Chip label="Event handlers" size="small" />
                <Chip label="OAuth2 support" size="small" />
                <Chip label="Webhooks" size="small" />
              </Stack>
              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                sx={{ mt: 2 }}
                onClick={() => handleOpenCreator('integration')}
              >
                Create Integration
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Documentation Card */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Extension Development" />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Widget Development
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Widgets are React TypeScript components with access to application state.
                    They can read data, execute commands, and render custom UI.
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Workflow Development
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Workflows are YAML files with steps, parameters, and conditionals.
                    Use Jinja2 templating for dynamic values and approval gates for critical operations.
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Integration Development
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Integrations are Python classes with event handlers.
                    Connect to external APIs, webhooks, and services with custom configuration.
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Creator Dialog */}
      <Dialog
        open={showCreator}
        onClose={handleCloseCreator}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {creatorType === 'widget' && <WidgetsIcon sx={{ mr: 1 }} />}
            {creatorType === 'workflow' && <WorkflowIcon sx={{ mr: 1 }} />}
            {creatorType === 'integration' && <IntegrationIcon sx={{ mr: 1 }} />}
            {getCreatorTitle()}
          </Box>
        </DialogTitle>

        <DialogContent>
          {success ? (
            <Alert severity="success">
              ✅ Extension created successfully! Files are ready in your extensions directory.
            </Alert>
          ) : (
            <>
              {error && (
                <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
              {renderCreatorForm()}
            </>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={handleCloseCreator} disabled={creating}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            variant="contained"
            disabled={creating || success}
            startIcon={creating ? <CircularProgress size={16} /> : <CodeIcon />}
          >
            {creating ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ExtensionsView;

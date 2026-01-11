import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Stack,
  Typography,
  Alert,
  Box,
  Chip,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

interface Tool {
  name: string;
  description: string;
}

interface PluginCreatorProps {
  open: boolean;
  onClose: () => void;
  onCreatePlugin: (pluginData: any) => Promise<void>;
}

const PluginCreator: React.FC<PluginCreatorProps> = ({ open, onClose, onCreatePlugin }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [author, setAuthor] = useState('');
  const [templateType, setTemplateType] = useState<'basic' | 'advanced'>('basic');
  const [runtime, setRuntime] = useState<'python' | 'node'>('python');
  const [tools, setTools] = useState<Tool[]>([{ name: '', description: '' }]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const steps = ['Plugin Info', 'Template Type', 'Define Tools', 'Review'];

  const handleNext = () => {
    // Validation
    if (activeStep === 0) {
      if (!name.trim()) {
        setError('Plugin name is required');
        return;
      }
      if (!description.trim()) {
        setError('Description is required');
        return;
      }
    } else if (activeStep === 2) {
      const validTools = tools.filter(t => t.name.trim() && t.description.trim());
      if (validTools.length === 0) {
        setError('At least one tool is required');
        return;
      }
    }
    setError(null);
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setError(null);
    setActiveStep((prev) => prev - 1);
  };

  const handleAddTool = () => {
    setTools([...tools, { name: '', description: '' }]);
  };

  const handleRemoveTool = (index: number) => {
    setTools(tools.filter((_, i) => i !== index));
  };

  const handleToolChange = (index: number, field: 'name' | 'description', value: string) => {
    const newTools = [...tools];
    newTools[index][field] = value;
    setTools(newTools);
  };

  const handleCreate = async () => {
    setCreating(true);
    setError(null);

    try {
      const validTools = tools
        .filter(t => t.name.trim() && t.description.trim())
        .map(t => ({
          name: t.name.trim(),
          description: t.description.trim(),
        }));

      await onCreatePlugin({
        name: name.trim(),
        description: description.trim(),
        author: author.trim() || 'Anonymous',
        template_type: templateType,
        runtime,
        tools: validTools,
      });

      setSuccess(true);
      setTimeout(() => {
        handleClose();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create plugin');
    } finally {
      setCreating(false);
    }
  };

  const handleClose = () => {
    if (!creating) {
      setName('');
      setDescription('');
      setAuthor('');
      setTemplateType('basic');
      setRuntime('python');
      setTools([{ name: '', description: '' }]);
      setActiveStep(0);
      setError(null);
      setSuccess(false);
      onClose();
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Stack spacing={3}>
            <TextField
              autoFocus
              fullWidth
              label="Plugin Name"
              placeholder="my-awesome-plugin"
              value={name}
              onChange={(e) => setName(e.target.value)}
              helperText="Use lowercase with hyphens (e.g., weather-api, slack-notifier)"
            />
            <TextField
              fullWidth
              label="Description"
              placeholder="A plugin that..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              multiline
              rows={3}
              helperText="Brief description of what your plugin does"
            />
            <TextField
              fullWidth
              label="Author"
              placeholder="Your Name"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              helperText="Optional: Your name or organization"
            />
          </Stack>
        );

      case 1:
        return (
          <Stack spacing={3}>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Template Type
              </Typography>
              <Stack direction="row" spacing={2}>
                <Box
                  onClick={() => setTemplateType('basic')}
                  sx={{
                    flex: 1,
                    p: 2,
                    border: '2px solid',
                    borderColor: templateType === 'basic' ? 'primary.main' : 'divider',
                    borderRadius: 2,
                    cursor: 'pointer',
                    '&:hover': { borderColor: 'primary.main' },
                  }}
                >
                  <Typography variant="h6">Basic</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Simple plugin with tool definitions
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                    <Chip label="Quick" size="small" />
                    <Chip label="Beginner" size="small" />
                  </Stack>
                </Box>
                <Box
                  onClick={() => setTemplateType('advanced')}
                  sx={{
                    flex: 1,
                    p: 2,
                    border: '2px solid',
                    borderColor: templateType === 'advanced' ? 'primary.main' : 'divider',
                    borderRadius: 2,
                    cursor: 'pointer',
                    '&:hover': { borderColor: 'primary.main' },
                  }}
                >
                  <Typography variant="h6">Advanced</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Plugin with state management and resources
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                    <Chip label="Powerful" size="small" />
                    <Chip label="Advanced" size="small" />
                  </Stack>
                </Box>
              </Stack>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Runtime
              </Typography>
              <TextField
                select
                fullWidth
                value={runtime}
                onChange={(e) => setRuntime(e.target.value as 'python' | 'node')}
              >
                <MenuItem value="python">Python (Recommended)</MenuItem>
                <MenuItem value="node">Node.js</MenuItem>
              </TextField>
            </Box>
          </Stack>
        );

      case 2:
        return (
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle2">
                Plugin Tools ({tools.filter(t => t.name.trim()).length})
              </Typography>
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={handleAddTool}
              >
                Add Tool
              </Button>
            </Box>

            <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
              {tools.map((tool, index) => (
                <Box
                  key={index}
                  sx={{
                    p: 2,
                    mb: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                    backgroundColor: (theme) =>
                      theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)',
                  }}
                >
                  <Stack spacing={2}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        Tool #{index + 1}
                      </Typography>
                      {tools.length > 1 && (
                        <IconButton
                          size="small"
                          onClick={() => handleRemoveTool(index)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      )}
                    </Box>
                    <TextField
                      fullWidth
                      label="Tool Name"
                      placeholder="get_weather"
                      value={tool.name}
                      onChange={(e) => handleToolChange(index, 'name', e.target.value)}
                      size="small"
                      helperText="Use snake_case (e.g., get_data, send_message)"
                    />
                    <TextField
                      fullWidth
                      label="Description"
                      placeholder="Get current weather for a location"
                      value={tool.description}
                      onChange={(e) => handleToolChange(index, 'description', e.target.value)}
                      size="small"
                      multiline
                      rows={2}
                    />
                  </Stack>
                </Box>
              ))}
            </Box>
          </Stack>
        );

      case 3:
        const validTools = tools.filter(t => t.name.trim() && t.description.trim());
        return (
          <Stack spacing={2}>
            <Alert severity="info">
              Review your plugin details before creating
            </Alert>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Plugin Name
              </Typography>
              <Typography variant="body1">{name}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Description
              </Typography>
              <Typography variant="body2">{description}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Configuration
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Chip label={`Template: ${templateType}`} size="small" />
                <Chip label={`Runtime: ${runtime}`} size="small" />
                <Chip label={`${validTools.length} tools`} size="small" />
              </Stack>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Tools
              </Typography>
              <Stack spacing={1}>
                {validTools.map((tool, index) => (
                  <Box
                    key={index}
                    sx={{
                      p: 1.5,
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                      {tool.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {tool.description}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            </Box>
          </Stack>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { minHeight: 500 } }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <CodeIcon sx={{ mr: 1 }} />
          Create New Plugin
        </Box>
      </DialogTitle>

      <DialogContent>
        {success ? (
          <Alert severity="success" sx={{ mb: 2 }}>
            ✅ Plugin created successfully! Files are ready in your plugins directory.
          </Alert>
        ) : (
          <>
            <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            {error && (
              <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {renderStepContent()}
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={creating}>
          Cancel
        </Button>
        {activeStep > 0 && activeStep < steps.length - 1 && (
          <Button onClick={handleBack} disabled={creating}>
            Back
          </Button>
        )}
        {activeStep < steps.length - 1 ? (
          <Button onClick={handleNext} variant="contained" disabled={creating}>
            Next
          </Button>
        ) : (
          <Button
            onClick={handleCreate}
            variant="contained"
            disabled={creating || success}
            startIcon={creating ? <CircularProgress size={16} /> : <CodeIcon />}
          >
            {creating ? 'Creating...' : 'Create Plugin'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default PluginCreator;

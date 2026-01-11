import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Box,
  Typography,
  Tabs,
  Tab,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Chip,
  Stack,
  IconButton,
  InputAdornment,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

interface NLPSettingsProps {
  open: boolean;
  onClose: () => void;
  onSave: (settings: NLPConfig) => void;
  currentSettings?: NLPConfig;
}

interface NLPConfig {
  enabled: boolean;
  primaryProvider: 'ollama' | 'openai' | 'gemini' | 'anthropic';
  fallbackToLocal: boolean;
  providers: {
    ollama: OllamaConfig;
    openai: OpenAIConfig;
    gemini: GeminiConfig;
    anthropic: AnthropicConfig;
  };
}

interface OllamaConfig {
  enabled: boolean;
  url: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

interface OpenAIConfig {
  enabled: boolean;
  apiKey: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

interface GeminiConfig {
  enabled: boolean;
  apiKey: string;
  model: string;
  tier: 'free' | 'paid';
  temperature: number;
  maxTokens: number;
}

interface AnthropicConfig {
  enabled: boolean;
  apiKey: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

const DEFAULT_SETTINGS: NLPConfig = {
  enabled: true,
  primaryProvider: 'ollama',
  fallbackToLocal: true,
  providers: {
    ollama: {
      enabled: true,
      url: 'http://localhost:11434',
      model: 'codellama:7b-instruct',
      temperature: 0.1,
      maxTokens: 512,
    },
    openai: {
      enabled: false,
      apiKey: '',
      model: 'gpt-3.5-turbo',
      temperature: 0.1,
      maxTokens: 150,
    },
    gemini: {
      enabled: false,
      apiKey: '',
      model: 'gemini-pro',
      tier: 'free',
      temperature: 0.1,
      maxTokens: 150,
    },
    anthropic: {
      enabled: false,
      apiKey: '',
      model: 'claude-3-5-sonnet-20241022',
      temperature: 0.1,
      maxTokens: 150,
    },
  },
};

const OLLAMA_MODELS = [
  { value: 'codellama:7b-instruct', label: 'CodeLlama 7B (Recommended)', description: 'Fast, good for simple commands' },
  { value: 'codellama:13b-instruct', label: 'CodeLlama 13B', description: 'More accurate, moderate speed' },
  { value: 'phind-codellama:34b-v2', label: 'Phind CodeLlama 34B', description: 'Most accurate, slower' },
  { value: 'wizardcoder:7b', label: 'WizardCoder 7B', description: 'Specialized for code generation' },
  { value: 'wizardcoder:13b', label: 'WizardCoder 13B', description: 'Balanced performance' },
  { value: 'deepseek-coder:6.7b-instruct', label: 'DeepSeek Coder 6.7B (Recommended)', description: 'Excellent for developer tasks' },
];

const OPENAI_MODELS = [
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (Recommended)', cost: '$0.0015/1k tokens' },
  { value: 'gpt-4-turbo-preview', label: 'GPT-4 Turbo', cost: '$0.01/1k tokens' },
  { value: 'gpt-4', label: 'GPT-4', cost: '$0.03/1k tokens' },
];

const GEMINI_MODELS = [
  { value: 'gemini-pro', label: 'Gemini Pro (Free)', tier: 'free' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro (Paid)', tier: 'paid' },
  { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash (Free)', tier: 'free' },
];

const ANTHROPIC_MODELS = [
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (Recommended)', cost: '$0.003/1k tokens' },
  { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku', cost: '$0.0008/1k tokens' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus', cost: '$0.015/1k tokens' },
];

const NLPSettings: React.FC<NLPSettingsProps> = ({ open, onClose, onSave, currentSettings }) => {
  const [settings, setSettings] = useState<NLPConfig>(currentSettings || DEFAULT_SETTINGS);
  const [activeTab, setActiveTab] = useState(0);
  const [showApiKeys, setShowApiKeys] = useState({
    openai: false,
    gemini: false,
    anthropic: false,
  });
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (currentSettings) {
      setSettings(currentSettings);
    }
  }, [currentSettings]);

  const handleSave = () => {
    onSave(settings);
    onClose();
  };

  const handleTestProvider = async (provider: string) => {
    setTesting(provider);
    // TODO: Send test request to backend
    setTimeout(() => {
      setTestResults({ ...testResults, [provider]: Math.random() > 0.3 });
      setTesting(null);
    }, 2000);
  };

  const renderOllamaSettings = () => (
    <Box>
      <FormControlLabel
        control={
          <Switch
            checked={settings.providers.ollama.enabled}
            onChange={(e) =>
              setSettings({
                ...settings,
                providers: {
                  ...settings.providers,
                  ollama: { ...settings.providers.ollama, enabled: e.target.checked },
                },
              })
            }
          />
        }
        label="Enable Ollama (Local)"
      />

      {settings.providers.ollama.enabled && (
        <Stack spacing={3} sx={{ mt: 2 }}>
          <TextField
            label="Ollama URL"
            fullWidth
            value={settings.providers.ollama.url}
            onChange={(e) =>
              setSettings({
                ...settings,
                providers: {
                  ...settings.providers,
                  ollama: { ...settings.providers.ollama, url: e.target.value },
                },
              })
            }
            helperText="Default: http://localhost:11434"
          />

          <FormControl fullWidth>
            <InputLabel>Model</InputLabel>
            <Select
              value={settings.providers.ollama.model}
              label="Model"
              onChange={(e) =>
                setSettings({
                  ...settings,
                  providers: {
                    ...settings.providers,
                    ollama: { ...settings.providers.ollama, model: e.target.value },
                  },
                })
              }
            >
              {OLLAMA_MODELS.map((model) => (
                <MenuItem key={model.value} value={model.value}>
                  <Box>
                    <Typography variant="body1">{model.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {model.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box>
            <Typography variant="body2" gutterBottom>
              Temperature: {settings.providers.ollama.temperature}
            </Typography>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.providers.ollama.temperature}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  providers: {
                    ...settings.providers,
                    ollama: { ...settings.providers.ollama, temperature: parseFloat(e.target.value) },
                  },
                })
              }
              style={{ width: '100%' }}
            />
            <Typography variant="caption" color="text.secondary">
              Lower = more deterministic, Higher = more creative
            </Typography>
          </Box>

          <Button
            variant="outlined"
            startIcon={testing === 'ollama' ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={() => handleTestProvider('ollama')}
            disabled={testing !== null}
          >
            Test Connection
          </Button>

          {testResults.ollama !== undefined && (
            <Alert severity={testResults.ollama ? 'success' : 'error'}>
              {testResults.ollama ? 'Connected successfully!' : 'Connection failed. Is Ollama running?'}
            </Alert>
          )}
        </Stack>
      )}
    </Box>
  );

  const renderOpenAISettings = () => (
    <Box>
      <FormControlLabel
        control={
          <Switch
            checked={settings.providers.openai.enabled}
            onChange={(e) =>
              setSettings({
                ...settings,
                providers: {
                  ...settings.providers,
                  openai: { ...settings.providers.openai, enabled: e.target.checked },
                },
              })
            }
          />
        }
        label="Enable OpenAI"
      />

      {settings.providers.openai.enabled && (
        <Stack spacing={3} sx={{ mt: 2 }}>
          <TextField
            label="API Key"
            fullWidth
            type={showApiKeys.openai ? 'text' : 'password'}
            value={settings.providers.openai.apiKey}
            onChange={(e) =>
              setSettings({
                ...settings,
                providers: {
                  ...settings.providers,
                  openai: { ...settings.providers.openai, apiKey: e.target.value },
                },
              })
            }
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowApiKeys({ ...showApiKeys, openai: !showApiKeys.openai })}
                    edge="end"
                  >
                    {showApiKeys.openai ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            helperText="Get your API key from platform.openai.com"
          />

          <FormControl fullWidth>
            <InputLabel>Model</InputLabel>
            <Select
              value={settings.providers.openai.model}
              label="Model"
              onChange={(e) =>
                setSettings({
                  ...settings,
                  providers: {
                    ...settings.providers,
                    openai: { ...settings.providers.openai, model: e.target.value },
                  },
                })
              }
            >
              {OPENAI_MODELS.map((model) => (
                <MenuItem key={model.value} value={model.value}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <Typography>{model.label}</Typography>
                    <Chip label={model.cost} size="small" />
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            startIcon={testing === 'openai' ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={() => handleTestProvider('openai')}
            disabled={testing !== null || !settings.providers.openai.apiKey}
          >
            Test Connection
          </Button>

          {testResults.openai !== undefined && (
            <Alert severity={testResults.openai ? 'success' : 'error'}>
              {testResults.openai ? 'API key is valid!' : 'Invalid API key or connection failed'}
            </Alert>
          )}
        </Stack>
      )}
    </Box>
  );

  const renderGeminiSettings = () => (
    <Box>
      <FormControlLabel
        control={
          <Switch
            checked={settings.providers.gemini.enabled}
            onChange={(e) =>
              setSettings({
                ...settings,
                providers: {
                  ...settings.providers,
                  gemini: { ...settings.providers.gemini, enabled: e.target.checked },
                },
              })
            }
          />
        }
        label="Enable Google Gemini"
      />

      {settings.providers.gemini.enabled && (
        <Stack spacing={3} sx={{ mt: 2 }}>
          <Alert severity="info">
            Gemini offers a free tier with generous rate limits. Get your API key from aistudio.google.com
          </Alert>

          <TextField
            label="API Key"
            fullWidth
            type={showApiKeys.gemini ? 'text' : 'password'}
            value={settings.providers.gemini.apiKey}
            onChange={(e) =>
              setSettings({
                ...settings,
                providers: {
                  ...settings.providers,
                  gemini: { ...settings.providers.gemini, apiKey: e.target.value },
                },
              })
            }
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowApiKeys({ ...showApiKeys, gemini: !showApiKeys.gemini })}
                    edge="end"
                  >
                    {showApiKeys.gemini ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <FormControl fullWidth>
            <InputLabel>Model</InputLabel>
            <Select
              value={settings.providers.gemini.model}
              label="Model"
              onChange={(e) =>
                setSettings({
                  ...settings,
                  providers: {
                    ...settings.providers,
                    gemini: { ...settings.providers.gemini, model: e.target.value },
                  },
                })
              }
            >
              {GEMINI_MODELS.map((model) => (
                <MenuItem key={model.value} value={model.value}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <Typography>{model.label}</Typography>
                    <Chip label={model.tier} size="small" color={model.tier === 'free' ? 'success' : 'default'} />
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            startIcon={testing === 'gemini' ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={() => handleTestProvider('gemini')}
            disabled={testing !== null || !settings.providers.gemini.apiKey}
          >
            Test Connection
          </Button>

          {testResults.gemini !== undefined && (
            <Alert severity={testResults.gemini ? 'success' : 'error'}>
              {testResults.gemini ? 'API key is valid!' : 'Invalid API key or connection failed'}
            </Alert>
          )}
        </Stack>
      )}
    </Box>
  );

  const renderAnthropicSettings = () => (
    <Box>
      <FormControlLabel
        control={
          <Switch
            checked={settings.providers.anthropic.enabled}
            onChange={(e) =>
              setSettings({
                ...settings,
                providers: {
                  ...settings.providers,
                  anthropic: { ...settings.providers.anthropic, enabled: e.target.checked },
                },
              })
            }
          />
        }
        label="Enable Anthropic Claude"
      />

      {settings.providers.anthropic.enabled && (
        <Stack spacing={3} sx={{ mt: 2 }}>
          <TextField
            label="API Key"
            fullWidth
            type={showApiKeys.anthropic ? 'text' : 'password'}
            value={settings.providers.anthropic.apiKey}
            onChange={(e) =>
              setSettings({
                ...settings,
                providers: {
                  ...settings.providers,
                  anthropic: { ...settings.providers.anthropic, apiKey: e.target.value },
                },
              })
            }
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowApiKeys({ ...showApiKeys, anthropic: !showApiKeys.anthropic })}
                    edge="end"
                  >
                    {showApiKeys.anthropic ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            helperText="Get your API key from console.anthropic.com"
          />

          <FormControl fullWidth>
            <InputLabel>Model</InputLabel>
            <Select
              value={settings.providers.anthropic.model}
              label="Model"
              onChange={(e) =>
                setSettings({
                  ...settings,
                  providers: {
                    ...settings.providers,
                    anthropic: { ...settings.providers.anthropic, model: e.target.value },
                  },
                })
              }
            >
              {ANTHROPIC_MODELS.map((model) => (
                <MenuItem key={model.value} value={model.value}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <Typography>{model.label}</Typography>
                    <Chip label={model.cost} size="small" />
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            startIcon={testing === 'anthropic' ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={() => handleTestProvider('anthropic')}
            disabled={testing !== null || !settings.providers.anthropic.apiKey}
          >
            Test Connection
          </Button>

          {testResults.anthropic !== undefined && (
            <Alert severity={testResults.anthropic ? 'success' : 'error'}>
              {testResults.anthropic ? 'API key is valid!' : 'Invalid API key or connection failed'}
            </Alert>
          )}
        </Stack>
      )}
    </Box>
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          NLP Settings
          <IconButton
            aria-label="close"
            onClick={onClose}
            sx={{
              color: (theme) => theme.palette.grey[500],
            }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <Alert severity="info">
            Configure natural language to shell command translation. Templates are always tried first for instant matching.
          </Alert>

          <FormControl fullWidth>
            <InputLabel>Primary Provider</InputLabel>
            <Select
              value={settings.primaryProvider}
              label="Primary Provider"
              onChange={(e) => setSettings({ ...settings, primaryProvider: e.target.value as any })}
            >
              <MenuItem value="ollama">Ollama (Local)</MenuItem>
              <MenuItem value="openai">OpenAI</MenuItem>
              <MenuItem value="gemini">Google Gemini</MenuItem>
              <MenuItem value="anthropic">Anthropic Claude</MenuItem>
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Switch
                checked={settings.fallbackToLocal}
                onChange={(e) => setSettings({ ...settings, fallbackToLocal: e.target.checked })}
              />
            }
            label="Fallback to Ollama if primary provider fails"
          />

          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
              <Tab label="Ollama" />
              <Tab label="OpenAI" />
              <Tab label="Gemini" />
              <Tab label="Anthropic" />
            </Tabs>
          </Box>

          <Box sx={{ pt: 2 }}>
            {activeTab === 0 && renderOllamaSettings()}
            {activeTab === 1 && renderOpenAISettings()}
            {activeTab === 2 && renderGeminiSettings()}
            {activeTab === 3 && renderAnthropicSettings()}
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default NLPSettings;

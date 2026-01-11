import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Stack,
  Chip,
  LinearProgress,
  Alert,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Extension as ExtensionIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  HelpOutline as HelpOutlineIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

interface HealthStatus {
  plugin_id: string;
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  response_time_ms: number | null;
  error_message: string | null;
  tools_count: number | null;
  last_checked: number;
}

interface Plugin {
  id: string;
  name: string;
  enabled: boolean;
}

interface PluginHealthWidgetProps {
  plugins: Plugin[];
  healthStatuses: Record<string, HealthStatus>;
  onCheckAllHealth?: () => void;
  checking?: boolean;
}

const PluginHealthWidget: React.FC<PluginHealthWidgetProps> = ({
  plugins,
  healthStatuses,
  onCheckAllHealth,
  checking = false,
}) => {
  const enabledPlugins = plugins.filter(p => p.enabled);
  const healthyCount = Object.values(healthStatuses).filter(h => h.status === 'healthy').length;
  const degradedCount = Object.values(healthStatuses).filter(h => h.status === 'degraded').length;
  const downCount = Object.values(healthStatuses).filter(h => h.status === 'down').length;
  const unknownCount = enabledPlugins.length - healthyCount - degradedCount - downCount;

  const healthPercentage = enabledPlugins.length > 0
    ? Math.round((healthyCount / enabledPlugins.length) * 100)
    : 100;

  const getOverallStatus = () => {
    if (downCount > 0) return 'error';
    if (degradedCount > 0) return 'warning';
    if (healthyCount === enabledPlugins.length && enabledPlugins.length > 0) return 'success';
    return 'info';
  };

  const getStatusIcon = (status: HealthStatus['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon sx={{ fontSize: 20, color: 'success.main' }} />;
      case 'degraded':
        return <WarningIcon sx={{ fontSize: 20, color: 'warning.main' }} />;
      case 'down':
        return <ErrorIcon sx={{ fontSize: 20, color: 'error.main' }} />;
      default:
        return <HelpOutlineIcon sx={{ fontSize: 20, color: 'text.disabled' }} />;
    }
  };

  if (enabledPlugins.length === 0) {
    return (
      <Card>
        <CardHeader
          avatar={<ExtensionIcon />}
          title="Plugin Health"
        />
        <CardContent>
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <ExtensionIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              No plugins enabled
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        avatar={<ExtensionIcon />}
        title="Plugin Health"
        subheader={`${enabledPlugins.length} enabled plugin${enabledPlugins.length !== 1 ? 's' : ''}`}
        action={
          onCheckAllHealth && (
            <Tooltip title="Refresh all health checks">
              <IconButton onClick={onCheckAllHealth} disabled={checking} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          )
        }
      />
      <CardContent>
        <Stack spacing={2}>
          {/* Overall Health Status */}
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" fontWeight={600}>
                System Health
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {healthPercentage}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={healthPercentage}
              color={getOverallStatus() as any}
              sx={{ height: 8, borderRadius: 1 }}
            />
          </Box>

          {/* Status Summary */}
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip
              icon={<CheckCircleIcon />}
              label={`${healthyCount} Healthy`}
              size="small"
              color="success"
              variant={healthyCount > 0 ? "filled" : "outlined"}
            />
            {degradedCount > 0 && (
              <Chip
                icon={<WarningIcon />}
                label={`${degradedCount} Degraded`}
                size="small"
                color="warning"
                variant="filled"
              />
            )}
            {downCount > 0 && (
              <Chip
                icon={<ErrorIcon />}
                label={`${downCount} Down`}
                size="small"
                color="error"
                variant="filled"
              />
            )}
            {unknownCount > 0 && (
              <Chip
                icon={<HelpOutlineIcon />}
                label={`${unknownCount} Unknown`}
                size="small"
                variant="outlined"
              />
            )}
          </Stack>

          {/* Issues Alert */}
          {downCount > 0 && (
            <Alert severity="error">
              {downCount} plugin{downCount !== 1 ? 's are' : ' is'} not responding
            </Alert>
          )}
          {downCount === 0 && degradedCount > 0 && (
            <Alert severity="warning">
              {degradedCount} plugin{degradedCount !== 1 ? 's are' : ' is'} degraded
            </Alert>
          )}

          {/* Individual Plugin Status */}
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Recent Checks
            </Typography>
            <Stack spacing={1}>
              {enabledPlugins.slice(0, 5).map((plugin) => {
                const health = healthStatuses[plugin.id];
                return (
                  <Box
                    key={plugin.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      p: 1,
                      borderRadius: 1,
                      backgroundColor: (theme) => theme.palette.mode === 'dark'
                        ? 'rgba(255, 255, 255, 0.02)'
                        : 'rgba(0, 0, 0, 0.02)',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1, minWidth: 0 }}>
                      {health && getStatusIcon(health.status)}
                      <Typography variant="body2" noWrap sx={{ flex: 1 }}>
                        {plugin.name}
                      </Typography>
                    </Box>
                    {health?.response_time_ms && (
                      <Tooltip title="Response time">
                        <Typography variant="caption" color="text.secondary">
                          {health.response_time_ms.toFixed(0)}ms
                        </Typography>
                      </Tooltip>
                    )}
                  </Box>
                );
              })}
              {enabledPlugins.length > 5 && (
                <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center', pt: 1 }}>
                  +{enabledPlugins.length - 5} more
                </Typography>
              )}
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default PluginHealthWidget;

/**
 * healthService.js
 * Pings the backend health endpoint to show connectivity status in UI.
 *
 * GET /health → { status: "ok"|"degraded", database: string, assistant: string }
 */

import { apiGet, isBackendConfigured } from './apiClient';

/**
 * @typedef {'connected'|'degraded'|'offline'|'not_configured'} BackendStatus
 *
 * @typedef {Object} HealthResult
 * @property {BackendStatus} status
 * @property {string} [database]
 * @property {string} [assistant]
 */

/**
 * Check backend health status.
 * @returns {Promise<HealthResult>}
 */
export async function checkHealth() {
  if (!isBackendConfigured()) {
    return { status: 'not_configured' };
  }
  try {
    const data = await apiGet('/health');
    return {
      status: data.status === 'ok' ? 'connected' : 'degraded',
      database: data.database,
      assistant: data.assistant,
    };
  } catch {
    return { status: 'offline' };
  }
}

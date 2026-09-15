/**
 * projectService.js
 * API calls for individual project detail, history, and predictions.
 *
 * GET /projects/{project_id}          → ProjectDetail
 * GET /projects/{project_id}/history  → HistoryOut
 * GET /projects/{project_id}/prediction → PredictionOut
 */

import { apiGet, isBackendConfigured } from './apiClient';
import { mockReviewQueue } from '../data/mockData';

/**
 * Helper: build a synthetic ProjectDetail from a mock ReviewQueueItem.
 * Removed once the backend is live.
 *
 * @param {string} projectId
 * @returns {import('./types').ProjectDetail}
 */
function _mockDetail(projectId) {
  const item = mockReviewQueue.find((r) => r.canonical_project_id === projectId) ?? mockReviewQueue[0];
  return {
    canonical_project_id: item.canonical_project_id,
    project_code: item.canonical_project_id,
    canonical_name: item.canonical_name,
    agency: item.agency,
    ministry: 'Ministry of Statistics (Demonstration)',
    sector: item.sector,
    state: item.state,
    identity_method: 'SYNTHETIC_CUF',
    identity_status: 'CONFIRMED',
    latest_reporting_month: '2025-02-01',
    latest_snapshot: {
      reporting_month: '2025-02-01',
      agency: item.agency,
      state: item.state,
      sector: item.sector,
      project_observation_count: 8,
      months_since_first_observation: 24,
      progress_current: 48,
      progress_velocity: -1.2,
      expenditure_current: 72,
      expenditure_velocity: 2.4,
      cost_ratio: 1.5,
      source: null,
    },
    prediction: null,
    data_trust: {
      status: item.data_trust,
      identity: 'CONFIRMED',
      availability: 'PRESENT',
      coverage: 'SUFFICIENT',
      freshness: 'CURRENT',
      completeness: 'COMPLETE',
      schema_validity: 'VALID',
      provenance: 'SYNTHETIC',
    },
    model_release: {
      schedule_prediction: 'WITHHELD',
      cost_prediction: 'WITHHELD',
      release_state: 'BLOCKED_PENDING_HUMAN_TARGET_TRANSFER',
    },
    prediction_eligibility: {
      eligible: false,
      reasons: ['Model release BLOCKED_PENDING_HUMAN_TARGET_TRANSFER'],
    },
    officer_decision: {
      decision: item.officer_decision,
      implementation_watch: item.implementation_watch,
      attention_trend: item.attention_trend,
      evidence: item.evidence,
    },
    cost_intelligence: null,
  };
}

/**
 * Fetch full project intelligence dossier.
 *
 * @param {string} projectId
 * @returns {Promise<{ data: import('./types').ProjectDetail, synthetic: boolean }>}
 */
export async function fetchProjectDetail(projectId) {
  if (!isBackendConfigured()) {
    return { data: _mockDetail(projectId), synthetic: true };
  }
  try {
    const data = await apiGet(`/projects/${encodeURIComponent(projectId)}`);
    return { data, synthetic: false };
  } catch {
    return { data: _mockDetail(projectId), synthetic: true };
  }
}

/**
 * Fetch observation history for a project.
 *
 * @param {string} projectId
 * @returns {Promise<{ data: import('./types').HistoryOut, synthetic: boolean }>}
 */
export async function fetchProjectHistory(projectId) {
  if (!isBackendConfigured()) {
    return {
      data: {
        canonical_project_id: projectId,
        observations: [],
        unavailable_months: [],
        interpolated: false,
      },
      synthetic: true,
    };
  }
  try {
    const data = await apiGet(`/projects/${encodeURIComponent(projectId)}/history`);
    return { data, synthetic: false };
  } catch {
    return {
      data: { canonical_project_id: projectId, observations: [], unavailable_months: [], interpolated: false },
      synthetic: true,
    };
  }
}

/**
 * Fetch the latest ML prediction for a project.
 *
 * @param {string} projectId
 * @returns {Promise<{ data: import('./types').PredictionOut|null, synthetic: boolean }>}
 */
export async function fetchProjectPrediction(projectId) {
  if (!isBackendConfigured()) {
    return { data: null, synthetic: true };
  }
  try {
    const data = await apiGet(`/projects/${encodeURIComponent(projectId)}/prediction`);
    return { data, synthetic: false };
  } catch {
    return { data: null, synthetic: true };
  }
}

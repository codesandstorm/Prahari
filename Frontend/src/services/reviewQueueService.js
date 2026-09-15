/**
 * reviewQueueService.js
 * API calls for the PRAHARI Review Queue.
 *
 * GET /review-queue
 * Backend schema → ReviewQueueOut (backend/schemas.py)
 */

import { apiGet, isBackendConfigured } from './apiClient';
import { mockReviewQueueResponse } from '../data/mockData';

/**
 * Fetch the paginated review queue.
 *
 * @param {Object} [params]
 * @param {number}  [params.page=1]
 * @param {number}  [params.pageSize=25]
 * @param {string}  [params.reviewState]  - 'REVIEW_RECOMMENDED' | 'DATA_VERIFICATION_REQUIRED' | 'MONITOR' | 'PREDICTION_WITHHELD'
 * @param {string}  [params.reasonCode]
 * @param {string}  [params.modelReleaseState] - 'RELEASED' | 'WITHHELD'
 * @returns {Promise<{ data: import('./types').ReviewQueueResponse, synthetic: boolean }>}
 */
export async function fetchReviewQueue({
  page = 1,
  pageSize = 25,
  reviewState,
  reasonCode,
  modelReleaseState,
} = {}) {
  if (!isBackendConfigured()) {
    return { data: mockReviewQueueResponse, synthetic: true };
  }

  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (reviewState) params.set('review_state', reviewState);
  if (reasonCode) params.set('reason_code', reasonCode);
  if (modelReleaseState) params.set('model_release_state', modelReleaseState);

  try {
    const data = await apiGet(`/review-queue?${params}`);
    return { data, synthetic: false };
  } catch {
    // Graceful fallback so the UI stays functional during backend outages.
    return { data: mockReviewQueueResponse, synthetic: true };
  }
}

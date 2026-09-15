/**
 * filterService.js
 * Fetches distinct filter options (ministries, sectors, states, etc.)
 * from the backend projects listing. Falls back to mock values.
 *
 * NOTE: The backend currently has no dedicated /filters endpoint.
 * Once one is available, replace the extraction logic below.
 * Expected backend endpoint:  GET /filters  →  FilterOptions
 */

import { isBackendConfigured } from './apiClient';
import { mockFilterOptions } from '../data/mockData';

/**
 * Fetch selectable filter options for the dashboard filter bar.
 *
 * @returns {Promise<{ data: import('./types').FilterOptions, synthetic: boolean }>}
 */
export async function fetchFilterOptions() {
  if (!isBackendConfigured()) {
    return { data: mockFilterOptions, synthetic: true };
  }
  // TODO: Replace with GET /filters once the backend exposes that endpoint.
  // For now return mock options so the filter bar renders correctly.
  return { data: mockFilterOptions, synthetic: true };
}

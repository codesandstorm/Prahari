/**
 * prahariData.js — LEGACY SHIM
 *
 * This file previously held all inline demo data AND the API_BASE_URL constant.
 * Both have been moved to their proper locations:
 *
 *   - Demo / mock data  →  src/data/mockData.js
 *   - API base URL      →  VITE_PRAHARI_API_BASE_URL env var (read in src/services/apiClient.js)
 *   - Type definitions  →  src/services/types.js
 *
 * This shim re-exports everything so that any legacy import path continues to work
 * without code changes across the rest of the codebase.
 * TODO: Remove this file once all import sites are updated to use the new paths.
 */

export {
  mockReviewQueue as reviewQueue,
  mockKpis as kpis,
  mockEarlyWarnings as earlyWarnings,
  mockPortfolioProgress as portfolioProgress,
} from './mockData';

/** @deprecated Use import.meta.env.VITE_PRAHARI_API_BASE_URL via apiClient.js */
export const API_BASE_URL = 'http://localhost:8000/api/v1';

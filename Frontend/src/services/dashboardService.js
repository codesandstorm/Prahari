/**
 * dashboardService.js
 * API calls for the Officer Dashboard.
 *
 * GET /dashboard/summary  →  DashboardSummary counts
 * GET /projects           →  paginated project list with predictions
 */

import { apiGet, isBackendConfigured } from './apiClient';
import {
  mockDashboardSummary,
  mockKpis,
  mockEarlyWarnings,
  mockPortfolioProgress,
  mockCostOverview,
  mockCostSummary,
  mockWatchDistribution,
} from '../data/mockData';

/**
 * Fetch high-level dashboard counts.
 *
 * @returns {Promise<{ data: import('./types').DashboardSummary, synthetic: boolean }>}
 */
export async function fetchDashboardSummary() {
  if (!isBackendConfigured()) {
    return { data: mockDashboardSummary, synthetic: true };
  }
  try {
    const data = await apiGet('/dashboard/summary');
    return { data, synthetic: false };
  } catch {
    return { data: mockDashboardSummary, synthetic: true };
  }
}

/**
 * Returns KPI cards.
 * TODO: Derive these from fetchDashboardSummary() + /projects totals once backend is live.
 *
 * @returns {Promise<{ data: import('./types').KpiCard[], synthetic: boolean }>}
 */
export async function fetchKpis() {
  if (!isBackendConfigured()) {
    return { data: mockKpis, synthetic: true };
  }
  // Placeholder — swap with real aggregation endpoint when available.
  return { data: mockKpis, synthetic: true };
}

/**
 * Returns early-warning triage counts.
 * TODO: Drive from review-queue counts once backend is live.
 *
 * @returns {Promise<{ data: import('./types').EarlyWarningCard[], synthetic: boolean }>}
 */
export async function fetchEarlyWarnings() {
  if (!isBackendConfigured()) {
    return { data: mockEarlyWarnings, synthetic: true };
  }
  return { data: mockEarlyWarnings, synthetic: true };
}

/**
 * Returns portfolio-level analytics data.
 *
 * @returns {Promise<{
 *   portfolioProgress: import('./types').ProgressBand[],
 *   costOverview: import('./types').CostRow[],
 *   costSummary: object,
 *   watchDistribution: import('./types').WatchDistribution,
 *   synthetic: boolean,
 * }>}
 */
export async function fetchPortfolioAnalytics() {
  if (!isBackendConfigured()) {
    return {
      portfolioProgress: mockPortfolioProgress,
      costOverview: mockCostOverview,
      costSummary: mockCostSummary,
      watchDistribution: mockWatchDistribution,
      synthetic: true,
    };
  }
  // TODO: Replace with real analytics endpoint.
  return {
    portfolioProgress: mockPortfolioProgress,
    costOverview: mockCostOverview,
    costSummary: mockCostSummary,
    watchDistribution: mockWatchDistribution,
    synthetic: true,
  };
}

/**
 * Fetch paginated project list.
 *
 * @param {Object} [params]
 * @param {number} [params.page=1]
 * @param {number} [params.pageSize=25]
 * @param {string} [params.search]
 * @param {string} [params.sector]
 * @param {string} [params.ministry]
 * @param {string} [params.sort='canonical_project_id']
 * @param {'asc'|'desc'} [params.order='asc']
 * @returns {Promise<{ data: import('./types').ProjectSummary[], meta: object, synthetic: boolean }>}
 */
export async function fetchProjects({
  page = 1,
  pageSize = 25,
  search,
  sector,
  ministry,
  sort = 'canonical_project_id',
  order = 'asc',
} = {}) {
  if (!isBackendConfigured()) {
    return { data: [], meta: { total: 0, pages: 0 }, synthetic: true };
  }
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    sort,
    order,
  });
  if (search) params.set('search', search);
  if (sector) params.set('sector', sector);
  if (ministry) params.set('ministry', ministry);

  try {
    const { items, total, pages, ...rest } = await apiGet(`/projects?${params}`);
    return { data: items, meta: { total, pages, ...rest }, synthetic: false };
  } catch {
    return { data: [], meta: { total: 0, pages: 0 }, synthetic: true };
  }
}

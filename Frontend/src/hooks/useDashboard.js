import { useEffect, useState } from 'react';
import { fetchDashboardSummary, fetchKpis, fetchEarlyWarnings, fetchPortfolioAnalytics } from '../services/dashboardService';

import { fetchFilterOptions } from '../services/filterService';

/**
 * Aggregates all data needed for the Officer Dashboard.
 *
 * @param {import('../services/types').ActiveFilters} [filters]
 *
 * @returns {{
 *   kpis: import('../services/types').KpiCard[],
 *   earlyWarnings: import('../services/types').EarlyWarningCard[],
 *   portfolioProgress: import('../services/types').ProgressBand[],
 *   costOverview: import('../services/types').CostRow[],
 *   costSummary: object,
 *   watchDistribution: import('../services/types').WatchDistribution,
 *   summary: import('../services/types').DashboardSummary|null,
 *   options: import('../services/types').FilterOptions,
 *   synthetic: boolean,
 *   loading: boolean,
 *   error: string|null,
 * }}
 */
export function useDashboard(filters = {}) {
  const [state, setState] = useState({
    kpis: [],
    earlyWarnings: [],
    portfolioProgress: [],
    costOverview: [],
    costSummary: {},
    watchDistribution: null,
    summary: null,
    options: {},
    synthetic: true,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;
    setState((prev) => ({ ...prev, loading: true, error: null }));

    Promise.all([
      fetchDashboardSummary(),
      fetchKpis(),
      fetchEarlyWarnings(),
      fetchPortfolioAnalytics(),
      fetchFilterOptions(),
    ])
      .then(([summaryRes, kpisRes, warningsRes, analyticsRes, optionsRes]) => {
        if (!active) return;
        setState({
          kpis: kpisRes.data,
          earlyWarnings: warningsRes.data,
          portfolioProgress: analyticsRes.portfolioProgress,
          costOverview: analyticsRes.costOverview,
          costSummary: analyticsRes.costSummary,
          watchDistribution: analyticsRes.watchDistribution,
          summary: summaryRes.data,
          options: optionsRes.data,
          synthetic: kpisRes.synthetic,
          loading: false,
          error: null,
        });
      })
      .catch((err) => {
        if (!active) return;
        setState((prev) => ({ ...prev, loading: false, error: err.message }));
      });

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)]);

  return state;
}

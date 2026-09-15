/**
 * mockData.js
 * All synthetic / demo data lives here.
 *
 * When the backend is connected, nothing in this file is imported
 * by the real service calls — each service uses it only as a fallback
 * when VITE_PRAHARI_API_BASE_URL is not set or the backend is unreachable.
 *
 * To swap in real data: set VITE_PRAHARI_API_BASE_URL in .env and restart the dev server.
 */

// ---------------------------------------------------------------------------
// Review Queue items
// ---------------------------------------------------------------------------

/** @type {import('./types').ReviewQueueItem[]} */
export const mockReviewQueue = [
  {
    canonical_project_id: 'CUF-001',
    canonical_name: 'Synthetic CUF Demonstration Corridor',
    sector: 'Roads & Highways',
    agency: 'Demonstration Agency',
    state: 'Synthetic CUF Sandbox',
    officer_decision: 'REVIEW_RECOMMENDED',
    implementation_watch: 'ELEVATED',
    data_trust: 'USABLE',
    attention_trend: 'WORSENING',
    evidence: 'PHYSICAL_PROGRESS_STAGNANT · MILESTONE_OVERDUE',
    financial_exposure: 'Synthetic demonstration value',
  },
  {
    canonical_project_id: 'CUF-002',
    canonical_name: 'Synthetic CUF Water Programme',
    sector: 'Water Resources',
    agency: 'Demonstration Agency',
    state: 'Synthetic CUF Sandbox',
    officer_decision: 'DATA_VERIFICATION_REQUIRED',
    implementation_watch: 'WATCH',
    data_trust: 'VERIFICATION REQUIRED',
    attention_trend: 'STABLE',
    evidence: 'SOURCE_AVAILABILITY_LIMITED',
    financial_exposure: 'Synthetic demonstration value',
  },
  {
    canonical_project_id: 'CUF-003',
    canonical_name: 'Synthetic Dedicated Freight Corridor',
    sector: 'Railways',
    agency: 'CUF Demonstration Agency',
    state: 'Synthetic CUF Sandbox',
    officer_decision: 'REVIEW_RECOMMENDED',
    implementation_watch: 'ELEVATED',
    data_trust: 'USABLE',
    attention_trend: 'WORSENING',
    evidence: 'MILESTONE_SLIPPAGE · CONTRACTOR_PACING',
    financial_exposure: 'Synthetic demonstration value',
  },
  {
    canonical_project_id: 'CUF-004',
    canonical_name: 'Synthetic Rail Link Tunnel Package',
    sector: 'Railways',
    agency: 'CUF Demonstration Agency',
    state: 'Synthetic CUF Sandbox',
    officer_decision: 'REVIEW_RECOMMENDED',
    implementation_watch: 'ELEVATED',
    data_trust: 'USABLE',
    attention_trend: 'WATCH',
    evidence: 'GEOLOGICAL_INGRESS · PACE_STAGNATION',
    financial_exposure: 'Synthetic demonstration value',
  },
  {
    canonical_project_id: 'CUF-005',
    canonical_name: 'Synthetic Petroleum Refinery Programme',
    sector: 'Petroleum',
    agency: 'CUF Demonstration Agency',
    state: 'Synthetic CUF Sandbox',
    officer_decision: 'MONITOR',
    implementation_watch: 'MODERATE',
    data_trust: 'USABLE',
    attention_trend: 'STABLE',
    evidence: 'EQUIPMENT_DELIVERY_STAGGER',
    financial_exposure: 'Synthetic demonstration value',
  },
  {
    canonical_project_id: 'CUF-006',
    canonical_name: 'Synthetic Metro Rail Phase Programme',
    sector: 'Urban Transit',
    agency: 'CUF Demonstration Agency',
    state: 'Synthetic CUF Sandbox',
    officer_decision: 'MONITOR',
    implementation_watch: 'MODERATE',
    data_trust: 'USABLE',
    attention_trend: 'WATCH',
    evidence: 'TBM_PACE_SLOWDOWN',
    financial_exposure: 'Synthetic demonstration value',
  },
];

/** @type {import('./types').ReviewQueueResponse} */
export const mockReviewQueueResponse = {
  items: mockReviewQueue,
  status: 'SYNTHETIC',
  policy_version: 'v1-demo',
  counts: {
    REVIEW_RECOMMENDED: 3,
    DATA_VERIFICATION_REQUIRED: 1,
    MONITOR: 2,
    PREDICTION_WITHHELD: 0,
  },
  page: 1,
  page_size: 25,
  total: 6,
  pages: 1,
};

// ---------------------------------------------------------------------------
// Dashboard KPIs
// ---------------------------------------------------------------------------

/** @type {import('./types').DashboardSummary} */
export const mockDashboardSummary = {
  projects: 1829,
  observations: 32450,
  predictions: 1105,
  alerts: 124,
  note: 'Synthetic CUF demonstration data — not official project evidence.',
};

/** @type {import('./types').KpiCard[]} */
export const mockKpis = [
  { label: 'TOTAL PROJECTS', value: '1,829', note: 'Major & Mega ≥ ₹150 Cr' },
  { label: 'ORIGINAL APPROVED COST', value: '₹ 26,84,210 Cr', note: 'CCEA Sanctioned Base' },
  { label: 'LATEST REVISED COST', value: '₹ 31,45,690 Cr', note: 'Net Anticipated Outlay' },
  { label: 'CUMULATIVE EXPENDITURE', value: '₹ 14,92,340 Cr', note: 'Funds Disbursed' },
];

// ---------------------------------------------------------------------------
// Early Warning triage counts
// ---------------------------------------------------------------------------

/** @type {import('./types').EarlyWarningCard[]} */
export const mockEarlyWarnings = [
  {
    label: 'REVIEW RECOMMENDED',
    count: 68,
    note: 'Projects showing critical pace drops and serious schedule slippage.',
  },
  {
    label: 'DATA VERIFICATION REQUIRED',
    count: 32,
    note: 'Physical progress milestones misaligned with recorded expenditure.',
  },
  {
    label: 'MONITOR',
    count: 18,
    note: 'Sustained monthly deceleration observed; nearing buffer limit.',
  },
  {
    label: 'PREDICTION WITHHELD',
    count: 6,
    note: 'Schedule & Cost Predictions: WITHHELD.',
  },
];

// ---------------------------------------------------------------------------
// Portfolio / Analytics
// ---------------------------------------------------------------------------

/** @type {import('./types').ProgressBand[]} */
export const mockPortfolioProgress = [
  { label: '0% – 25% Complete', amount: '345 projects (18.9%)', widthPct: 45 },
  { label: '26% – 50% Complete', amount: '428 projects (23.4%)', widthPct: 56 },
  { label: '51% – 75% Complete', amount: '383 projects (20.9%)', widthPct: 51 },
  { label: '76% – 100% Complete', amount: '673 projects (36.8%)', widthPct: 88 },
];

/** @type {import('./types').CostRow[]} */
export const mockCostOverview = [
  { label: 'Original Approved Cost', amount: '₹ 26.84 Lakh Cr', widthPct: 85 },
  { label: 'Latest Revised Cost', amount: '₹ 31.46 Lakh Cr', widthPct: 100 },
  { label: 'Cumulative Expenditure', amount: '₹ 14.92 Lakh Cr', widthPct: 47 },
];

export const mockCostSummary = {
  escalationText: 'Overall Cost Escalation: ₹ 4,61,480 Cr (+17.19%)',
  unspentBalance: '₹ 16,53,350 Cr',
  totalOverrun: '₹ 4,61,480 Cr',
  absorptionRate: '55.6% vs Approved',
};

/** @type {import('./types').WatchDistribution} */
export const mockWatchDistribution = {
  total: 124,
  label: 'FLAGGED',
  items: [
    { label: 'Review Recommended', count: 68, pct: 55 },
    { label: 'Implementation Watch', count: 38, pct: 31 },
    { label: 'Monitor', count: 12, pct: 10 },
    { label: 'Prediction Withheld', count: 6, pct: 4 },
  ],
};

// ---------------------------------------------------------------------------
// Filter options (populated from backend once connected)
// ---------------------------------------------------------------------------

/** @type {import('./types').FilterOptions} */
export const mockFilterOptions = {
  ministries: ['All Ministries'],
  sectors: ['All Sectors'],
  states: ['All States / UTs'],
  projectStatuses: ['All Projects'],
  reviewStatuses: ['All Review Statuses'],
  reportingMonths: ['February, 2025'],
};

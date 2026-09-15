/**
 * types.js
 * JSDoc type definitions for all PRAHARI data models.
 *
 * These mirror the backend Pydantic schemas in backend/schemas.py.
 * Your teammate's API must return JSON that conforms to these shapes.
 *
 * When TypeScript is adopted later, convert these to interface/type declarations.
 */

// ---------------------------------------------------------------------------
// Core project models
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} SourceOut
 * @property {string} reporting_month       - ISO date "YYYY-MM-DD"
 * @property {string|null} source_id
 * @property {string} coverage_class
 * @property {string|null} sha256
 * @property {string|null} schema_family
 */

/**
 * @typedef {Object} SnapshotOut
 * @property {string} reporting_month
 * @property {string|null} agency
 * @property {string|null} state
 * @property {string|null} sector
 * @property {number|null} project_observation_count
 * @property {number|null} months_since_first_observation
 * @property {number|null} progress_current              - 0..100
 * @property {number|null} progress_velocity
 * @property {number|null} expenditure_current
 * @property {number|null} expenditure_velocity
 * @property {number|null} cost_ratio
 * @property {SourceOut|null} [source]
 */

/**
 * @typedef {'AVAILABLE'|'ABSTAIN'|'WITHHELD'} PredictionStatus
 * @typedef {'LOW'|'MEDIUM'|'HIGH'} RiskBand
 * @typedef {'LOW'|'MODERATE'|'HIGH'|'ABSTAIN'} ReliabilityBand
 */

/**
 * @typedef {Object} PredictionOut
 * @property {string} prediction_id
 * @property {string} canonical_project_id
 * @property {string} as_of_month
 * @property {string} target
 * @property {number} horizon_months
 * @property {PredictionStatus} prediction_status
 * @property {number|null} probability
 * @property {RiskBand|null} risk_band
 * @property {ReliabilityBand} reliability_band
 * @property {string[]} reliability_reasons
 * @property {string} data_quality_status
 * @property {string|null} review_priority
 * @property {Object[]} contributors
 * @property {string} model_version
 * @property {string} feature_version
 * @property {string} target_version
 * @property {string|null} abstention_reason
 * @property {string} created_at
 */

/**
 * @typedef {Object} ProjectSummary
 * @property {string} canonical_project_id
 * @property {string|null} project_code
 * @property {string} canonical_name
 * @property {string|null} agency
 * @property {string|null} ministry
 * @property {string|null} sector
 * @property {string|null} state
 * @property {string|null} latest_reporting_month
 * @property {PredictionOut|null} prediction
 */

/**
 * @typedef {ProjectSummary & {
 *   identity_method: string,
 *   identity_status: string,
 *   latest_snapshot: SnapshotOut|null,
 *   data_trust: Object,
 *   model_release: Object,
 *   prediction_eligibility: Object,
 *   officer_decision: Object,
 *   cost_intelligence: Object|null,
 * }} ProjectDetail
 */

// ---------------------------------------------------------------------------
// Review Queue
// ---------------------------------------------------------------------------

/**
 * @typedef {'REVIEW_RECOMMENDED'|'DATA_VERIFICATION_REQUIRED'|'MONITOR'|'PREDICTION_WITHHELD'} OfficerDecision
 * @typedef {'ELEVATED'|'WATCH'|'MODERATE'} ImplementationWatch
 * @typedef {'USABLE'|'VERIFICATION REQUIRED'|'WITHHELD'} DataTrust
 * @typedef {'WORSENING'|'WATCH'|'STABLE'} AttentionTrend
 */

/**
 * @typedef {Object} ReviewQueueItem
 * @property {string} canonical_project_id
 * @property {string} canonical_name
 * @property {string|null} sector
 * @property {string|null} agency
 * @property {string|null} state
 * @property {OfficerDecision} officer_decision
 * @property {ImplementationWatch} implementation_watch
 * @property {DataTrust} data_trust
 * @property {AttentionTrend} attention_trend
 * @property {string} evidence
 * @property {string} financial_exposure
 */

/**
 * @typedef {Object} ReviewQueueResponse
 * @property {ReviewQueueItem[]} items
 * @property {string} status
 * @property {string} policy_version
 * @property {Record<string,number>} counts
 * @property {number} page
 * @property {number} page_size
 * @property {number} total
 * @property {number} pages
 */

// ---------------------------------------------------------------------------
// Dashboard / Analytics
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} DashboardSummary
 * @property {number} projects
 * @property {number} observations
 * @property {number} predictions
 * @property {number} alerts
 * @property {string} note
 */

/**
 * @typedef {Object} KpiCard
 * @property {string} label
 * @property {string} value
 * @property {string} note
 */

/**
 * @typedef {Object} EarlyWarningCard
 * @property {string} label
 * @property {number} count
 * @property {string} note
 */

/**
 * @typedef {Object} ProgressBand
 * @property {string} label
 * @property {string} amount
 * @property {number} widthPct  - 0..100
 */

/**
 * @typedef {Object} CostRow
 * @property {string} label
 * @property {string} amount
 * @property {number} widthPct
 */

/**
 * @typedef {Object} WatchDistributionItem
 * @property {string} label
 * @property {number} count
 * @property {number} pct
 */

/**
 * @typedef {Object} WatchDistribution
 * @property {number} total
 * @property {string} label
 * @property {WatchDistributionItem[]} items
 */

// ---------------------------------------------------------------------------
// Filter options
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} FilterOptions
 * @property {string[]} ministries
 * @property {string[]} sectors
 * @property {string[]} states
 * @property {string[]} projectStatuses
 * @property {string[]} reviewStatuses
 * @property {string[]} reportingMonths
 */

/**
 * @typedef {Object} ActiveFilters
 * @property {string} ministry
 * @property {string} sector
 * @property {string} state
 * @property {string} projectStatus
 * @property {string} reviewStatus
 * @property {string} reportingMonth
 */

// ---------------------------------------------------------------------------
// Project History
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} HistoryOut
 * @property {string} canonical_project_id
 * @property {SnapshotOut[]} observations
 * @property {SourceOut[]} unavailable_months
 * @property {false} interpolated
 */

// ---------------------------------------------------------------------------
// Assistant / LLM
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} AssistantRequest
 * @property {string} request_id
 * @property {string} question
 * @property {string|null} [canonical_project_id]
 */

/**
 * @typedef {Object} AssistantOut
 * @property {string} request_id
 * @property {string} route
 * @property {Object} answer
 * @property {string[]} project_evidence_references
 * @property {Object[]} document_citations
 * @property {string|null} reliability_statement
 * @property {string[]} limitations
 * @property {boolean} fallback_used
 * @property {string|null} fallback_reason
 * @property {string} model_version
 * @property {string|null} rag_index_version
 * @property {Record<string,number>} latency_metadata
 */

export default {};

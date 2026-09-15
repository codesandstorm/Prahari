/**
 * prahariService.js — LEGACY SHIM
 *
 * The original monolithic service has been split into focused modules:
 *   - src/services/apiClient.js          (HTTP client + error handling)
 *   - src/services/reviewQueueService.js (review queue)
 *   - src/services/dashboardService.js   (KPIs, portfolio analytics)
 *   - src/services/projectService.js     (project detail, history, prediction)
 *   - src/services/assistantService.js   (LLM assistant)
 *   - src/services/filterService.js      (filter options)
 *   - src/services/healthService.js      (backend health check)
 *
 * This shim re-exports getReviewQueue so existing hook imports keep working.
 * TODO: Remove once useReviewQueue.js is updated to import from reviewQueueService directly.
 */

export { fetchReviewQueue as getReviewQueue } from './reviewQueueService';

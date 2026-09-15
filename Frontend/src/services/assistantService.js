/**
 * assistantService.js
 * API call for the PRAHARI LLM assistant.
 *
 * POST /assistant/query → AssistantOut
 */

import { apiPost, isBackendConfigured } from './apiClient';

/**
 * Send a question to the PRAHARI assistant.
 *
 * @param {import('./types').AssistantRequest} request
 * @returns {Promise<import('./types').AssistantOut>}
 * @throws {Error} if the backend is unavailable or returns an error
 */
export async function queryAssistant(request) {
  if (!isBackendConfigured()) {
    throw new Error(
      'ASSISTANT_UNAVAILABLE: Set VITE_PRAHARI_API_BASE_URL in .env to enable the assistant.',
    );
  }
  return apiPost('/assistant/query', request);
}

/**
 * Check whether the assistant is likely to be available.
 * Useful for disabling the input while backend is not configured.
 */
export function isAssistantAvailable() {
  return isBackendConfigured();
}

/**
 * apiClient.js
 * Centralised fetch wrapper for all PRAHARI backend calls.
 *
 * Base URL is read once from the Vite environment variable.
 * If VITE_PRAHARI_API_BASE_URL is not set the services fall back to
 * synthetic demo data — no errors are thrown.
 */

export const API_BASE_URL = import.meta.env.VITE_PRAHARI_API_BASE_URL ?? '';

/**
 * Generic GET helper.
 * @param {string} path  - e.g. "/review-queue?page_size=25"
 * @returns {Promise<any>} - parsed JSON body
 * @throws  {ApiError}    - on non-2xx responses
 */
export async function apiGet(path) {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body?.detail?.code ?? 'API_ERROR', body?.detail?.message ?? response.statusText);
  }
  return response.json();
}

/**
 * Generic POST helper.
 * @param {string} path
 * @param {object} body
 * @returns {Promise<any>}
 */
export async function apiPost(path, body) {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(response.status, data?.detail?.code ?? 'API_ERROR', data?.detail?.message ?? response.statusText);
  }
  return response.json();
}

export class ApiError extends Error {
  /**
   * @param {number} status
   * @param {string} code
   * @param {string} message
   */
  constructor(status, code, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

/** Returns true when the backend URL is configured. */
export function isBackendConfigured() {
  return Boolean(API_BASE_URL);
}

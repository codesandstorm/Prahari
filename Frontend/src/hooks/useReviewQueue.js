import { useEffect, useState } from 'react';
import { fetchReviewQueue } from '../services/reviewQueueService';

/**
 * Fetches the review queue from the API (or mock data if backend is not configured).
 *
 * @param {Object} [params]
 * @param {number}  [params.page=1]
 * @param {number}  [params.pageSize=25]
 * @param {string}  [params.reviewState]
 *
 * @returns {{
 *   items: import('../services/types').ReviewQueueItem[],
 *   meta: object,
 *   counts: Record<string,number>,
 *   synthetic: boolean,
 *   loading: boolean,
 *   error: string|null,
 * }}
 */
export function useReviewQueue(params = {}) {
  const [state, setState] = useState({
    items: [],
    meta: {},
    counts: {},
    synthetic: true,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;
    setState((prev) => ({ ...prev, loading: true, error: null }));

    fetchReviewQueue(params)
      .then(({ data, synthetic }) => {
        if (!active) return;
        setState({
          items: data.items ?? [],
          meta: { page: data.page, page_size: data.page_size, total: data.total, pages: data.pages },
          counts: data.counts ?? {},
          synthetic,
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
    // Stringify params to avoid infinite re-renders from object identity changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params)]);

  return state;
}

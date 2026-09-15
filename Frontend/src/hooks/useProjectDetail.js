import { useEffect, useState } from 'react';
import { fetchProjectDetail, fetchProjectHistory } from '../services/projectService';

/**
 * Fetches full project intelligence dossier and observation history.
 *
 * @param {string} projectId
 * @returns {{
 *   project: import('../services/types').ProjectDetail|null,
 *   history: import('../services/types').HistoryOut|null,
 *   synthetic: boolean,
 *   loading: boolean,
 *   error: string|null,
 * }}
 */
export function useProjectDetail(projectId) {
  const [state, setState] = useState({
    project: null,
    history: null,
    synthetic: true,
    loading: true,
    error: null,
  });

  useEffect(() => {
    if (!projectId) return;
    let active = true;
    setState({ project: null, history: null, synthetic: true, loading: true, error: null });

    Promise.all([
      fetchProjectDetail(projectId),
      fetchProjectHistory(projectId),
    ])
      .then(([detailRes, historyRes]) => {
        if (!active) return;
        setState({
          project: detailRes.data,
          history: historyRes.data,
          synthetic: detailRes.synthetic,
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
  }, [projectId]);

  return state;
}

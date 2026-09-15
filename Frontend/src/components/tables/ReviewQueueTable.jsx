import React from 'react';
import { Link } from 'react-router-dom';
import Badge from '../common/Badge';

const COLUMNS = [
  'Priority',
  'Project',
  'Sector',
  'Officer Decision',
  'Implementation Watch',
  'Data Trust',
  'Attention Trend',
  'Key Evidence',
  'Financial Exposure',
  'Action',
];

/**
 * Review queue table with client-side search.
 *
 * @param {Object}   props
 * @param {import('../../services/types').ReviewQueueItem[]} props.items
 * @param {string}   props.query
 * @param {Object}   [props.meta]
 * @param {function} [props.onPageChange]
 */
export default function ReviewQueueTable({ items = [], query = '', onQueryChange, meta = {}, onPageChange }) {
  const filtered = items.filter((item) =>
    Object.values(item).join(' ').toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="pr-card pr-table-wrap">
      <div className="pr-table-tools">
        <input
          value={query}
          onChange={(e) => onQueryChange?.(e.target.value)}
          placeholder="⌕  Search project name, code..."
          aria-label="Search project"
        />
        <select aria-label="Risk level">
          <option>All Risk Levels</option>
          <option>REVIEW_RECOMMENDED</option>
          <option>DATA_VERIFICATION_REQUIRED</option>
          <option>MONITOR</option>
          <option>PREDICTION_WITHHELD</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <p className="pr-empty" style={{ padding: '20px 16px', textAlign: 'center' }}>
          No projects match your search.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              {COLUMNS.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((item, index) => (
              <tr key={item.canonical_project_id}>
                <td>P{index + 1}</td>
                <td>
                  <b>{item.canonical_name}</b>
                  <small>{item.agency}</small>
                </td>
                <td>{item.sector}</td>
                <td>
                  <Badge value={item.officer_decision} />
                </td>
                <td>
                  <Badge value={item.implementation_watch} />
                </td>
                <td>
                  <Badge value={item.data_trust} />
                </td>
                <td>
                  <Badge value={item.attention_trend} />
                </td>
                <td>{item.evidence}</td>
                <td>{item.financial_exposure}</td>
                <td>
                  <Link
                    className="pr-link"
                    to={`/prahari/project/${item.canonical_project_id}`}
                  >
                    VIEW DOSSIER
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {meta.pages > 1 && (
        <div className="pr-pagination" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderTop: '1px solid #edf1f4', fontSize: '10px', color: '#557087' }}>
          <span>Showing page {meta.page} of {meta.pages} ({meta.total} projects)</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="pr-secondary" disabled={meta.page <= 1} onClick={() => onPageChange?.(meta.page - 1)}>
              ← Previous
            </button>
            <button className="pr-secondary" disabled={meta.page >= meta.pages} onClick={() => onPageChange?.(meta.page + 1)}>
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

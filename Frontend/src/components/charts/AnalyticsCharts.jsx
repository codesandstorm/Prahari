import React from 'react';

const CHARTS = [
  { type: 'watch', title: 'Implementation Watch Distribution' },
  { type: 'progress', title: 'Physical Progress Distribution' },
  { type: 'cost', title: 'Cost / Outlay Comparison' },
  { type: 'trend', title: 'Attention Trend Distribution' },
  { type: 'sector', title: 'Sector Benchmarking' },
  { type: 'trust', title: 'Data Trust Distribution' },
];

/**
 * Analytics Charts grid.
 *
 * @param {Object} props
 * @param {import('../../services/types').ProgressBand[]}   [props.portfolioProgress]
 * @param {import('../../services/types').CostRow[]}         [props.costOverview]
 * @param {import('../../services/types').WatchDistribution} [props.watchDistribution]
 * @param {boolean}                                          [props.loading=false]
 */
export default function AnalyticsCharts({
  portfolioProgress = [],
  costOverview = [],
  watchDistribution = null,
  loading = false,
}) {
  if (loading) {
    return <div className="pr-loading">Loading configuration...</div>;
  }

  return (
    <div className="pr-chart-grid">
      {CHARTS.map(({ type, title }) => (
        <article className={`pr-card pr-chart pr-chart-${type}`} key={type}>
          <h3>{title}</h3>
          
          {/* Watch Distribution */}
          {type === 'watch' && (
            <>
              {!watchDistribution ? (
                <p>Awaiting selected data scope</p>
              ) : (
                <div className="pr-chart-body">
                  <div className="pr-donut">
                    <b>
                      {watchDistribution.total}
                      <small>{watchDistribution.label}</small>
                    </b>
                  </div>
                  <ul className="pr-legend">
                    {watchDistribution.items?.map(({ label, count, pct }) => (
                      <li key={label}>
                        {label} <b>{count} ({pct}%)</b>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {/* Physical Progress Distribution */}
          {type === 'progress' && (
            <>
              {portfolioProgress.length === 0 ? (
                <p>Awaiting selected data scope</p>
              ) : (
                <div className="pr-distribution">
                  {portfolioProgress.map(({ label, amount, widthPct }, i) => (
                    <span key={label} style={{ display: 'block', margin: '14px 0' }}>
                      <span style={{ fontSize: '10px', display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                        {label}
                        <b>{amount}</b>
                      </span>
                      <i style={{ display: 'block', height: '8px', background: '#eef3f7', overflow: 'hidden' }}>
                         <u style={{ display: 'block', height: '100%', width: `${widthPct}%`, background: i === 3 ? '#f59b09' : (i === 5 ? '#009b70' : '#03a8e6'), textDecoration: 'none' }} />
                      </i>
                    </span>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Cost Comparison */}
          {type === 'cost' && (
            <>
              {costOverview.length === 0 ? (
                <p>Awaiting selected data scope</p>
              ) : (
                <div className="pr-comparison" style={{ marginTop: '16px' }}>
                  {costOverview.map(({ label, amount, widthPct }, i) => (
                    <span key={label} style={{ display: 'block', marginBottom: '14px' }}>
                      <span style={{ fontSize: '10px', display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                        {label}
                        <b style={{ float: 'right' }}>{amount}</b>
                      </span>
                      <i style={{ display: 'block', height: '10px', background: '#eef3f7', overflow: 'hidden' }}>
                         <u style={{ display: 'block', height: '100%', width: `${widthPct}%`, background: i === 0 ? '#1596ce' : (i === 1 ? '#2864ea' : (i === 2 ? '#eb174c' : '#009a70')), textDecoration: 'none' }} />
                      </i>
                    </span>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Placeholders for complex graphical indicators */}
          {type === 'trend' && (
            <>
              <p>Reporting cycle trend will appear after scope selection</p>
              <div className="pr-bars">
                <i />
                <i />
                <i />
                <i />
              </div>
            </>
          )}

          {type === 'sector' && (
            <div className="pr-empty-state">
              <p>Benchmark indicators appear after scope selection.</p>
            </div>
          )}

          {type === 'trust' && (
            <div className="pr-empty-state">
              <p>Verification distribution appears after scope selection.</p>
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

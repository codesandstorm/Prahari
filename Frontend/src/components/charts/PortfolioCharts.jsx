import React from 'react';

/**
 * Portfolio charts section on the Officer Dashboard.
 *
 * @param {Object} props
 * @param {import('../../services/types').ProgressBand[]}   props.portfolioProgress
 * @param {import('../../services/types').CostRow[]}         props.costOverview
 * @param {Object}                                           props.costSummary
 * @param {import('../../services/types').WatchDistribution} props.watchDistribution
 * @param {boolean}                                          [props.loading=false]
 */
export function PortfolioCharts({
  portfolioProgress = [],
  costOverview = [],
  costSummary = {},
  watchDistribution = null,
  loading = false,
}) {
  if (loading) {
    return (
      <section className="pr-portfolio">
        <div className="pr-loading">Loading portfolio analytics…</div>
      </section>
    );
  }

  return (
    <section className="pr-portfolio">
      <div className="pr-section-head">
        <div>
          <h2>▣ PORTFOLIO ANALYTICS</h2>
          <p>High-level distribution metrics and financial outlays across central sector projects</p>
        </div>
        <small>Total Portfolio: {watchDistribution?.total ?? 0} Flagged / 1,829 Projects</small>
      </div>

      <div className="pr-analytics">
        {/* Implementation Watch Donut */}
        <article className="pr-card">
          <h3>PRAHARI IMPLEMENTATION WATCH DISTRIBUTION</h3>
          <p>Breakdown of {watchDistribution?.total ?? 0} flagged projects under active surveillance</p>
          <div className="pr-donut">
            <b>
              {watchDistribution?.total ?? '—'}
              <small>{watchDistribution?.label ?? 'FLAGGED'}</small>
            </b>
          </div>
          <ul className="pr-legend">
            {(watchDistribution?.items ?? []).map(({ label, count, pct }) => (
              <li key={label}>
                {label} <b>{count} ({pct}%)</b>
              </li>
            ))}
          </ul>
        </article>

        {/* Physical Progress Bars */}
        <article className="pr-card">
          <h3>PHYSICAL PROGRESS DISTRIBUTION</h3>
          <p>Actual progress across active projects in 4 quartile ranges</p>
          {portfolioProgress.map(({ label, amount, widthPct }) => (
            <div className="pr-progress" key={label}>
              <span>
                {label}
                <b>{amount}</b>
              </span>
              <i>
                <u style={{ width: `${widthPct}%` }} />
              </i>
            </div>
          ))}
        </article>
      </div>

      {/* Cost Overview */}
      <CostOverview rows={costOverview} summary={costSummary} />
    </section>
  );
}

/**
 * @param {Object} props
 * @param {import('../../services/types').CostRow[]} props.rows
 * @param {Object} props.summary
 */
export function CostOverview({ rows = [], summary = {} }) {
  return (
    <article className="pr-card pr-cost">
      <div className="pr-section-head">
        <div>
          <h2>COST OVERVIEW &amp; OUTLAY COMPARISON</h2>
          <p>
            Comparative assessment of sanctioned baseline, anticipated revised budget, and
            cumulative fund expenditure
          </p>
        </div>
        <b>{summary.escalationText ?? ''}</b>
      </div>

      {rows.map(({ label, amount, widthPct }) => (
        <div className="pr-cost-row" key={label}>
          <span>
            {label}
            <b>{amount}</b>
          </span>
          <i>
            <u style={{ width: `${widthPct}%` }} />
          </i>
        </div>
      ))}

      <div className="pr-cost-calls">
        <span>
          UNSPENT BALANCE REQUIRED<b>{summary.unspentBalance ?? '—'}</b>
        </span>
        <span>
          TOTAL COST OVERRUN<b>{summary.totalOverrun ?? '—'}</b>
        </span>
        <span>
          FINANCIAL ABSORPTION RATE<b>{summary.absorptionRate ?? '—'}</b>
        </span>
      </div>
    </article>
  );
}

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDashboard } from '../../hooks/useDashboard';
import { useReviewQueue } from '../../hooks/useReviewQueue';
import FilterBar from '../../components/common/FilterBar';
import PageShell from '../../components/common/PageShell';
import ReviewQueueTable from '../../components/tables/ReviewQueueTable';
import { PortfolioCharts } from '../../components/charts/PortfolioCharts';

export default function OfficerDashboard() {
  const [filters, setFilters] = useState({});
  const [query, setQuery] = useState('');
  const [queuePage, setQueuePage] = useState(1);

  const {
    kpis,
    earlyWarnings,
    portfolioProgress,
    costOverview,
    costSummary,
    watchDistribution,
    options,
    synthetic: dashSynthetic,
    loading: dashLoading,
  } = useDashboard(filters);

  const { items, meta, synthetic: queueSynthetic, loading: queueLoading } = useReviewQueue({ ...filters, page: queuePage, pageSize: 12 });

  const synthetic = dashSynthetic || queueSynthetic;

  const handleFilterChange = ({ key, value }) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleFilterReset = () => {
    setFilters({});
  };

  return (
    <PageShell
      title="Officer Dashboard"
      subtitle="PRAHARI — AI-Powered Early Warning for Infrastructure Projects"
      synthetic={synthetic}
    >
      <div className="pr-meta">
        <b>{synthetic ? 'SYNTHETIC CUF SANDBOX' : '● REAL HISTORICAL DATA'}</b>
        <span>Data as of: February 2025 &nbsp; | &nbsp; Last updated: 24 Feb 2025, 08:30 IST</span>
      </div>

      <FilterBar
        options={options}
        filters={filters}
        onChange={handleFilterChange}
        onReset={handleFilterReset}
      />

      {/* KPI Cards */}
      {dashLoading ? (
        <div className="pr-loading">Loading dashboard data…</div>
      ) : (
        <div className="pr-kpis">
          {kpis.map(({ label, value, note }) => (
            <article key={label}>
              <span>{label}</span>
              <b>{value}</b>
              <small>{note}</small>
            </article>
          ))}
        </div>
      )}

      {/* Early Warning Triage */}
      <section className="pr-card pr-triage">
        <div className="pr-section-head">
          <div>
            <h2>
              PRAHARI EARLY WARNING <i />
            </h2>
            <p>Projects requiring officer attention</p>
          </div>
          <Link className="pr-primary pr-button-link" to="/prahari/review-queue">
            View Review Queue →
          </Link>
        </div>
        <div className="pr-triage-grid">
          {earlyWarnings.map(({ label, count, note }) => (
            <article key={label}>
              <span>{label}</span>
              <b>{count}</b>
              <p>{note}</p>
            </article>
          ))}
        </div>
      </section>

      {/* Review Queue Preview */}
      <section className="pr-queue">
        <div className="pr-section-head">
          <div>
            <h2>PRAHARI REVIEW QUEUE</h2>
            <p>Recommended order for officer review</p>
          </div>
        </div>
        {queueLoading ? (
          <div className="pr-loading">Loading PRAHARI workspace…</div>
        ) : items.length === 0 ? (
          <div className="pr-empty">No projects in the review queue.</div>
        ) : (
          <ReviewQueueTable items={items} query={query} onQueryChange={setQuery} meta={meta} onPageChange={setQueuePage} />
        )}
      </section>

      {/* Portfolio Charts */}
      <PortfolioCharts
        portfolioProgress={portfolioProgress}
        costOverview={costOverview}
        costSummary={costSummary}
        watchDistribution={watchDistribution}
        loading={dashLoading}
      />
    </PageShell>
  );
}

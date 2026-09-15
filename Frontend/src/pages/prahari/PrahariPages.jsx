import React, { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Badge from '../../components/common/Badge';
import PageShell from '../../components/common/PageShell';
import AnalyticsCharts from '../../components/charts/AnalyticsCharts';
import ReviewQueueTable from '../../components/tables/ReviewQueueTable';
import { useReviewQueue } from '../../hooks/useReviewQueue';
import { useProjectDetail } from '../../hooks/useProjectDetail';
import { useDashboard } from '../../hooks/useDashboard';
import { isAssistantAvailable } from '../../services/assistantService';

// ---------------------------------------------------------------------------
// Review Queue Page
// ---------------------------------------------------------------------------

export function ReviewQueuePage() {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const { items, meta, loading, error } = useReviewQueue({ page, pageSize: 25 });

  return (
    <PageShell title="PRAHARI REVIEW QUEUE" subtitle="Recommended order for officer review">
      {loading && <div className="pr-loading">Loading review queue…</div>}
      {error && <div className="pr-error">Could not load review queue: {error}</div>}
      {!loading && !error && (
        <ReviewQueueTable items={items} query={query} onQueryChange={setQuery} meta={meta} onPageChange={setPage} />
      )}
    </PageShell>
  );
}

// ---------------------------------------------------------------------------
// Project Intelligence Page
// ---------------------------------------------------------------------------

const withheld = (
  <>
    <strong>WITHHELD</strong>
    <small>Operational prediction withheld pending model validation/release gate.</small>
  </>
);

export function ProjectIntelligencePage() {
  const { id } = useParams();
  const { project, loading, error, synthetic } = useProjectDetail(id);

  const cards = [
    [project?.officer_decision?.implementation_watch ?? 'ELEVATED', 'Implementation Watch'],
    ['WITHHELD', 'Schedule Prediction'],
    ['WITHHELD', 'Cost Prediction'],
    [project?.data_trust?.status ?? 'USABLE', 'Data Trust'],
    ['AVAILABLE', 'Peer Position'],
    [project?.officer_decision?.attention_trend ?? 'WORSENING', 'Attention Trend'],
    [project?.officer_decision?.decision ?? 'REVIEW RECOMMENDED', 'Officer Decision'],
    ['IN REVIEW', 'Alert / Review State'],
  ];

  const snapshot = project?.latest_snapshot;

  return (
    <PageShell
      title="PROJECT INTELLIGENCE"
      subtitle="Evidence-backed officer review dossier"
      synthetic={synthetic}
    >
      <Link className="pr-back" to="/prahari/review-queue">
        ← Back to review queue
      </Link>

      {loading && <div className="pr-loading">Loading project dossier…</div>}
      {error && <div className="pr-error">Could not load project: {error}</div>}

      {project && (
        <>
          <div className="pr-project-title">
            <h2>{project.canonical_name}</h2>
            <p>
              {project.canonical_project_id} · {project.sector} · {project.state}
            </p>
          </div>

          <div className="pr-intel-grid">
            {cards.map(([state, title]) => (
              <article key={title}>
                <Badge value={state} />
                <h3>{title}</h3>
                {state === 'WITHHELD' ? withheld : <p>Derived current-state evidence signal</p>}
              </article>
            ))}
          </div>

          <div className="pr-grid pr-wide">
            <article className="pr-card">
              <p className="pr-eyebrow">WHY IS THIS PROJECT FLAGGED?</p>
              <h3>Derived signals</h3>
              <ul>
                {(project.officer_decision?.evidence ?? 'PHYSICAL_PROGRESS_STAGNANT')
                  .split(' · ')
                  .map((e) => (
                    <li key={e}>{e.replace(/_/g, ' ')}</li>
                  ))}
              </ul>
              <p className="pr-note">
                Officer-review signal only. It does not infer misconduct, fraud, or failure.
              </p>
            </article>

            <article className="pr-card">
              <p className="pr-eyebrow">OFFICIAL FACT</p>
              {[
                ['Physical Progress', snapshot ? `${snapshot.progress_current ?? '—'}%` : '—'],
                ['Cumulative Expenditure', snapshot ? `${snapshot.expenditure_current ?? '—'}%` : '—'],
                ['Reporting Month', project.latest_reporting_month ?? '—'],
                ['Source', synthetic ? 'Synthetic demonstration record' : 'PRAHARI data service'],
              ].map(([label, value]) => (
                <div className="pr-fact" key={label}>
                  <span>{label}</span>
                  <b>{value}</b>
                </div>
              ))}
              <p className="pr-eyebrow">MODEL OUTPUT</p>
              {withheld}
            </article>
          </div>

          <section className="pr-card">
            <h3>Officer workflow</h3>
            <div className="pr-actions">
              {['ACKNOWLEDGE', 'START REVIEW', 'ADD NOTE', 'ADD ACTION', 'RESOLVE', 'REOPEN'].map(
                (label, index) => (
                  <button className={index === 0 ? 'pr-primary' : 'pr-secondary'} key={label}>
                    {label}
                  </button>
                ),
              )}
            </div>
          </section>
        </>
      )}
    </PageShell>
  );
}

// ---------------------------------------------------------------------------
// Analytics Page
// ---------------------------------------------------------------------------

export function AnalyticsPage() {
  const {
    portfolioProgress,
    costOverview,
    watchDistribution,
    synthetic,
    loading,
  } = useDashboard();

  return (
    <PageShell
      title="PROGRESS & MONITORING ANALYTICS"
      subtitle="Portfolio distributions are shown only when an approved data source is available."
      synthetic={synthetic}
    >
      <AnalyticsCharts
        portfolioProgress={portfolioProgress}
        costOverview={costOverview}
        watchDistribution={watchDistribution}
        loading={loading}
      />
    </PageShell>
  );
}

// ---------------------------------------------------------------------------
// Data Trust Page
// ---------------------------------------------------------------------------

export function DataTrustPage() {
  return (
    <PageShell
      title="DATA TRUST & VERIFICATION"
      subtitle="Identity reliability, availability, coverage, freshness, completeness, schema validity and provenance."
    >
      <div className="pr-grid">
        <article className="pr-card">
          <h3>Verification states</h3>
          <p>PASS · USABLE · VERIFICATION REQUIRED · WITHHELD</p>
        </article>
        <article className="pr-card">
          <h3>Governance</h3>
          <p>Data Trust is separate from project attention and review priority.</p>
        </article>
        <article className="pr-card">
          <h3>Coverage class</h3>
          <p>
            FULL_MATCH · PARTIAL_MATCH · UNMATCHED — determined at source ingestion time by the
            PRAHARI loader pipeline.
          </p>
        </article>
      </div>
    </PageShell>
  );
}

// ---------------------------------------------------------------------------
// Model Validation Page
// ---------------------------------------------------------------------------

export function ModelValidationPage() {
  return (
    <PageShell
      title="MODEL VALIDATION"
      subtitle="Research validation is not operational performance."
    >
      <div className="pr-grid">
        <article className="pr-card">
          <h3>Schedule Prediction</h3>
          {withheld}
        </article>
        <article className="pr-card">
          <h3>Cost Prediction</h3>
          {withheld}
        </article>
      </div>
      <article className="pr-card" style={{ marginTop: 15 }}>
        <h3>Release status</h3>
        <p>
          BLOCKED_PENDING_HUMAN_TARGET_TRANSFER. Operational release: false. No PR-AUC, ROC-AUC,
          Brier score or calibration value is presented as production performance.
        </p>
      </article>
    </PageShell>
  );
}

// ---------------------------------------------------------------------------
// CUF Sandbox Page
// ---------------------------------------------------------------------------

export function SandboxPage() {
  return (
    <PageShell
      title="CUF SANDBOX"
      subtitle="Synthetic CUF Prototype — demonstration data, not official project evidence."
      synthetic
    >
      <form className="pr-card pr-sandbox">
        <label>
          Project label
          <input defaultValue="Synthetic CUF Project" />
        </label>
        <label>
          Physical progress
          <input type="number" defaultValue="48" min="0" max="100" />
        </label>
        <label>
          Expenditure ratio
          <input type="number" defaultValue="72" min="0" max="200" />
        </label>
        <button className="pr-primary" type="submit">
          VIEW DERIVED SIGNALS
        </button>
        <p>Sandbox data never enters official historical statistics.</p>
      </form>
    </PageShell>
  );
}

// ---------------------------------------------------------------------------
// Ask PRAHARI (Assistant) Page
// ---------------------------------------------------------------------------

export function AssistantPage() {
  const available = isAssistantAvailable();

  return (
    <PageShell
      title="ASK PRAHARI"
      subtitle="Grounded explanation helper; LLM retrieves/explains, ML predicts, officer decides."
    >
      <article className="pr-card">
        {!available && (
          <p className="pr-note" style={{ marginBottom: 12 }}>
            Assistant requires <code>VITE_PRAHARI_API_BASE_URL</code> to be set. Running on demo
            data only.
          </p>
        )}
        <div className="pr-actions">
          {[
            'WHY IS THIS PROJECT UNDER REVIEW?',
            'WHAT CHANGED?',
            'SHOW EVIDENCE',
            'COMPARE WITH PEERS',
          ].map((label) => (
            <button className="pr-secondary" key={label} disabled={!available}>
              {label}
            </button>
          ))}
        </div>
        <p className="pr-note">
          The assistant does not invent project facts, scores, probabilities, or decisions.
        </p>
      </article>
    </PageShell>
  );
}

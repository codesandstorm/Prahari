import React, { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  FileText,
  UserRound,
} from "lucide-react";
import MilestoneJourney from "../../components/project/MilestoneJourney";
import {
  DataToolbar,
  EmptyState,
  MetricPage,
  PageHeroHeader,
  Pagination,
  Section,
  StandardTable,
  StatusPill,
} from "../../components/common/PageKit";
import { alertKpis } from "../../data/mock/alerts";
import { reviewKpis } from "../../data/mock/reviews";
import { useDemoStore } from "../../state/DemoStore";

const alertColumns = [
  { key: "project", label: "Project" },
  { key: "type", label: "Alert Type" },
  { key: "priority", label: "Priority" },
  { key: "reason", label: "Why this alert was raised" },
  { key: "status", label: "Status" },
  { key: "assigned", label: "Assigned To" },
  { key: "updated", label: "Updated" },
  { key: "action", label: "Action" },
];
const alertCell = (a, k) =>
  k === "project" ? (
    <>
      <span className="project-name">{a.project}</span>
      <span className="project-code">{a.projectId}</span>
    </>
  ) : ["priority", "status"].includes(k) ? (
    <StatusPill>{a[k]}</StatusPill>
  ) : k === "action" ? (
    <Link className="btn secondary" to={`/officer/alerts/${a.id}`}>
      Open alert
    </Link>
  ) : (
    a[k]
  );

export function AlertsPage() {
  const { alerts } = useDemoStore();
  const [selectedId, setSelectedId] = useState(alerts[0]?.id);
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState("All");
  const [status, setStatus] = useState("All");
  const [type, setType] = useState("All");
  const [sort, setSort] = useState("updated");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const selected = alerts.find((a) => a.id === selectedId) || alerts[0];
  const filtered = useMemo(
    () =>
      alerts
        .filter(
          (a) =>
            (!search ||
              `${a.project} ${a.projectId} ${a.type} ${a.reason}`
                .toLowerCase()
                .includes(search.toLowerCase())) &&
            (priority === "All" || a.priority === priority) &&
            (status === "All" || a.status === status) &&
            (type === "All" || a.type === type),
        )
        .sort((a, b) =>
          sort === "priority"
            ? Number(b.priority === "High") - Number(a.priority === "High")
            : sort === "project"
              ? a.project.localeCompare(b.project)
              : b.updated.localeCompare(a.updated),
        ),
    [alerts, search, priority, status, type, sort],
  );
  const visible = filtered.slice((page - 1) * pageSize, page * pageSize);
  const reset = () => {
    setSearch("");
    setPriority("All");
    setStatus("All");
    setType("All");
    setSort("updated");
    setPage(1);
  };
  return (
    <MetricPage
      title="Alerts"
      subtitle="Evidence-backed cases requiring officer attention and follow-up."
      kpis={alertKpis}
      rail={selected ? <AlertPreview alert={selected} /> : null}
    >
      <DataToolbar
        search={search}
        setSearch={(v) => {
          setSearch(v);
          setPage(1);
        }}
        filters={[
          {
            key: "priority",
            label: "Priority",
            value: priority,
            options: ["All", ...new Set(alerts.map((a) => a.priority))],
            onChange: (v) => {
              setPriority(v);
              setPage(1);
            },
          },
          {
            key: "status",
            label: "Status",
            value: status,
            options: ["All", ...new Set(alerts.map((a) => a.status))],
            onChange: (v) => {
              setStatus(v);
              setPage(1);
            },
          },
          {
            key: "type",
            label: "Alert type",
            value: type,
            options: ["All", ...new Set(alerts.map((a) => a.type))],
            onChange: (v) => {
              setType(v);
              setPage(1);
            },
          },
        ]}
        sort={{
          value: sort,
          options: [
            { value: "updated", label: "Recently updated" },
            { value: "priority", label: "High priority first" },
            { value: "project", label: "Project name" },
          ],
        }}
        setSort={setSort}
        onReset={reset}
      />
      <Section
        title="Alert list"
        action={
          <span className="section-meta">
            {filtered.length} matching alerts
          </span>
        }
      >
        {visible.length ? (
          <div
            onClick={(e) => {
              const row = e.target.closest("tr[data-id]");
              if (row) setSelectedId(row.dataset.id);
            }}
          >
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    {alertColumns.map((c) => (
                      <th key={c.key}>{c.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {visible.map((a) => (
                    <tr
                      key={a.id}
                      data-id={a.id}
                      tabIndex="0"
                      className={selected?.id === a.id ? "selected-row" : ""}
                    >
                      {alertColumns.map((c) => (
                        <td key={c.key}>{alertCell(a, c.key)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <EmptyState
            label="No active alerts match these filters."
            onReset={reset}
          />
        )}
        <Pagination
          page={page}
          setPage={setPage}
          total={filtered.length}
          pageSize={pageSize}
          setPageSize={setPageSize}
        />
      </Section>
    </MetricPage>
  );
}
function AlertPreview({ alert }) {
  return (
    <aside className="surface detail-rail">
      <header className="section-head">
        <h2>Alert Details</h2>
      </header>
      <div className="rail-body">
        <StatusPill>{alert.priority} priority</StatusPill>
        <h3>{alert.project}</h3>
        <span className="project-code">
          {alert.id} · {alert.type}
        </span>
        <InfoBlock title="What happened?">
          {alert.reason}. This signal requires evidence review rather than an
          automatic conclusion.
        </InfoBlock>
        <InfoBlock title="Evidence Summary">
          Latest source report, project identity and milestone record are
          available.
        </InfoBlock>
        <InfoBlock title="Recommended Next Step">
          Review the latest evidence and confirm the project response.
        </InfoBlock>
        <div className="rail-meta">
          <span>Current Review State</span>
          <StatusPill>{alert.status}</StatusPill>
          <span>Assigned To</span>
          <b>{alert.assigned}</b>
        </div>
        <Link className="btn primary full" to={`/officer/alerts/${alert.id}`}>
          Open full alert
        </Link>
      </div>
    </aside>
  );
}
const InfoBlock = ({ title, children }) => (
  <div className="info-block">
    <strong>{title}</strong>
    <p>{children}</p>
  </div>
);

export function AlertDetailsPage() {
  const { alertId } = useParams();
  const { alerts, updateAlert, startReview, reviews } = useDemoStore();
  const navigate = useNavigate();
  const a = alerts.find((x) => x.id === alertId);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  if (!a) return <NotFound kind="Alert" to="/officer/alerts" />;
  const linked = reviews.find((r) => r.projectId === a.projectId);
  const current =
    a.status === "Resolved"
      ? 4
      : a.status === "Monitoring"
        ? 2
        : a.status === "In review" || a.status === "Acknowledged"
          ? 1
          : 0;
  const act = (label) => {
    if (label === "Acknowledge")
      updateAlert(a.id, "Acknowledged", "Alert acknowledged");
    if (label === "Assign Review") {
      const id = startReview(a);
      navigate(`/officer/reviews/${id}`);
    }
    if (label === "Move to Monitoring")
      updateAlert(a.id, "Monitoring", "Moved to monitoring");
    if (label === "Resolve Alert")
      updateAlert(a.id, "Resolved", "Alert resolved");
    if (label === "Request Verification")
      updateAlert(a.id, "Acknowledged", "Verification requested");
    if (label === "Escalate") updateAlert(a.id, "In review", "Alert escalated");
  };
  return (
    <div className="page">
      <PageHeroHeader
        title="Alert Details"
        subtitle="View alert information, evidence and take an appropriate action."
        breadcrumb="Home / Alerts / Alert Details"
      />
      <button
        className="text-link page-back"
        onClick={() => navigate("/officer/alerts")}
      >
        ← Back to alerts
      </button>
      <div className="detail-layout">
        <div className="stack">
          <Section
            title={a.project}
            action={<StatusPill>{a.priority} priority</StatusPill>}
          >
            <div className="summary-grid">
              <Summary label="Alert ID" value={a.id} />
              <Summary label="Alert Type" value={a.type} />
              <Summary label="Current Status" value={a.status} />
              <Summary label="Assigned To" value={a.assigned} />
              <Summary label="Updated" value={a.updated} />
              <Summary
                label="Linked Review"
                value={linked?.id || "Not started"}
              />
            </div>
          </Section>
          <Section title="Why this alert was raised">
            <div className="reason-grid">
              {[
                [
                  "Milestone delayed",
                  "Latest milestone is behind the approved schedule.",
                ],
                [
                  "Expenditure review",
                  "Financial and physical delivery require comparison.",
                ],
                [
                  "Evidence needs review",
                  "Supporting documents require officer confirmation.",
                ],
                [
                  "Progress below plan",
                  "Reported physical progress is below plan.",
                ],
              ].map((x) => (
                <InfoCard key={x[0]} title={x[0]} text={x[1]} />
              ))}
            </div>
          </Section>
          <Section
            title="Evidence Snapshot"
            action={
              <button
                className="text-link"
                onClick={() => setEvidenceOpen(!evidenceOpen)}
              >
                {evidenceOpen ? "Hide evidence" : "View evidence"}
              </button>
            }
          >
            <div className="summary-grid">
              <Summary label="Reporting Month" value="May 2026" />
              <Summary
                label="Source Report ID"
                value={`${a.projectId}-MR-2026-05`}
              />
              <Summary label="Page Reference" value="Pages 14–16" />
              <Summary label="Execution Health" value="Needs attention" />
              <Summary label="Data Quality" value="Good" />
              <Summary label="Officer Attention" value={a.status} />
            </div>
            {evidenceOpen && (
              <div className="evidence-expansion">
                Evidence snapshot: approved timeline, reported physical progress
                and source identity were checked. Source document files are not
                embedded in this frontend build.
              </div>
            )}
          </Section>
          <Section title="Activity / Audit Log">
            <div className="audit-list">
              {a.history.map((r) => (
                <div key={r.join()}>
                  {r.map((c) => (
                    <span key={c}>{c}</span>
                  ))}
                </div>
              ))}
            </div>
          </Section>
        </div>
        <aside className="stack">
          <Section title="Alert Lifecycle">
            <Lifecycle
              stages={[
                "Alert created",
                "In review",
                "Under monitoring",
                "Escalated (if required)",
                "Resolved",
              ]}
              current={current}
            />
          </Section>
          <Section title="Recommended Actions">
            <div className="action-grid">
              {[
                "Acknowledge",
                "Assign Review",
                "Request Verification",
                "Move to Monitoring",
                "Resolve Alert",
                "Escalate",
              ].map((x, i) => (
                <button
                  className={`btn ${i === 0 ? "primary" : "secondary"}`}
                  onClick={() => act(x)}
                  disabled={
                    (x === "Acknowledge" && a.status === "Acknowledged") ||
                    (x === "Resolve Alert" && a.status === "Resolved")
                  }
                  key={x}
                >
                  {x}
                </button>
              ))}
            </div>
            {linked && (
              <Link
                className="btn secondary full"
                to={`/officer/reviews/${linked.id}`}
              >
                Open linked review
              </Link>
            )}
          </Section>
          <Section title="Project Quick Context">
            <div className="rail-body">
              <Summary label="Project" value={a.project} />
              <Summary label="Sector" value="Coal" />
              <Summary label="Project Status" value="Under implementation" />
              <Link
                className="btn secondary full"
                to={`/officer/projects/${a.projectId}`}
              >
                View project
              </Link>
            </div>
          </Section>
        </aside>
      </div>
    </div>
  );
}

const reviewColumns = [
  { key: "project", label: "Project" },
  { key: "type", label: "Linked Alert Type" },
  { key: "state", label: "Review State" },
  { key: "priority", label: "Priority" },
  { key: "assigned", label: "Assigned To" },
  { key: "next", label: "Next Review Date" },
  { key: "updated", label: "Last Updated" },
  { key: "action", label: "Action" },
];
export function ReviewsPage() {
  const { reviews } = useDemoStore();
  const [search, setSearch] = useState("");
  const [state, setState] = useState("All");
  const [priority, setPriority] = useState("All");
  const [assigned, setAssigned] = useState("All");
  const [sort, setSort] = useState("next");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const filtered = useMemo(
    () =>
      reviews
        .filter(
          (r) =>
            (!search ||
              `${r.project} ${r.projectId} ${r.type} ${r.assigned}`
                .toLowerCase()
                .includes(search.toLowerCase())) &&
            (state === "All" || r.state === state) &&
            (priority === "All" || r.priority === priority) &&
            (assigned === "All" || r.assigned === assigned),
        )
        .sort((a, b) =>
          sort === "updated"
            ? b.updated.localeCompare(a.updated)
            : sort === "priority"
              ? Number(b.priority === "High") - Number(a.priority === "High")
              : a.next.localeCompare(b.next),
        ),
    [reviews, search, state, priority, assigned, sort],
  );
  const visible = filtered.slice((page - 1) * pageSize, page * pageSize);
  const reset = () => {
    setSearch("");
    setState("All");
    setPriority("All");
    setAssigned("All");
    setSort("next");
    setPage(1);
  };
  const workload = [
    [
      "In progress",
      reviews.filter((r) => r.state === "In progress").length,
      "blue",
    ],
    [
      "Monitoring",
      reviews.filter((r) => r.state === "Monitoring").length,
      "purple",
    ],
    [
      "Action required",
      reviews.filter((r) => r.state === "Action required").length,
      "red",
    ],
    ["Complete", reviews.filter((r) => r.state === "Complete").length, "green"],
    [
      "Not started",
      reviews.filter((r) => r.state === "Not started").length,
      "gray",
    ],
  ];
  const pendingAction = (r) =>
    r.state === "Action required"
      ? "Review milestone slippage"
      : r.state === "Monitoring"
        ? "Monitor next reporting cycle"
        : r.state === "Not started"
          ? "Verify source evidence"
          : "Complete officer follow-up";
  const rail = (
    <aside className="stack">
      <Section title="Review Workload">
        <div className="review-workload">
          <div
            className="review-donut"
            style={{
              "--in-progress": `${(workload[0][1] / reviews.length) * 360}deg`,
              "--monitoring": `${((workload[0][1] + workload[1][1]) / reviews.length) * 360}deg`,
              "--action": `${((workload[0][1] + workload[1][1] + workload[2][1]) / reviews.length) * 360}deg`,
              "--complete": `${((workload[0][1] + workload[1][1] + workload[2][1] + workload[3][1]) / reviews.length) * 360}deg`,
            }}
          >
            <div>
              <b>{reviews.length}</b>
              <span>Total Reviews</span>
            </div>
          </div>
          <div className="workload-legend">
            {workload.map(([label, count, tone]) => (
              <div className={`tone-${tone}`} key={label}>
                <i />
                <span>{label}</span>
                <b>{count}</b>
              </div>
            ))}
          </div>
        </div>
      </Section>
      <Section title="My Pending Actions">
        <div className="pending-actions">
          {reviews.slice(0, 4).map((r) => (
            <Link key={r.id} to={`/officer/reviews/${r.id}`}>
              <span className={`priority-dot ${r.priority.toLowerCase()}`} />
              <div>
                <strong>{r.project}</strong>
                <small>{pendingAction(r)}</small>
              </div>
              <time>{r.next}</time>
            </Link>
          ))}
        </div>
      </Section>
    </aside>
  );
  return (
    <MetricPage
      title="Reviews"
      subtitle="Track officer follow-up, assignments, notes and resolution workflow."
      kpis={reviewKpis}
      rail={rail}
    >
      <DataToolbar
        search={search}
        setSearch={(v) => {
          setSearch(v);
          setPage(1);
        }}
        filters={[
          {
            key: "state",
            label: "Review state",
            value: state,
            options: ["All", ...new Set(reviews.map((r) => r.state))],
            onChange: (v) => {
              setState(v);
              setPage(1);
            },
          },
          {
            key: "priority",
            label: "Priority",
            value: priority,
            options: ["All", ...new Set(reviews.map((r) => r.priority))],
            onChange: (v) => {
              setPriority(v);
              setPage(1);
            },
          },
          {
            key: "assigned",
            label: "Assigned to",
            value: assigned,
            options: ["All", ...new Set(reviews.map((r) => r.assigned))],
            onChange: (v) => {
              setAssigned(v);
              setPage(1);
            },
          },
        ]}
        sort={{
          value: sort,
          options: [
            { value: "next", label: "Next review date" },
            { value: "updated", label: "Recently updated" },
            { value: "priority", label: "High priority first" },
          ],
        }}
        setSort={setSort}
        onReset={reset}
      />
      <Section
        title="Review Queue"
        action={
          <span className="section-meta">
            {filtered.length} matching reviews
          </span>
        }
      >
        {visible.length ? (
          <StandardTable
            columns={reviewColumns}
            rows={visible}
            renderCell={(r, k) =>
              k === "project" ? (
                <>
                  <span className="project-name">{r.project}</span>
                  <span className="project-code">{r.projectId}</span>
                </>
              ) : ["state", "priority"].includes(k) ? (
                <StatusPill>{r[k]}</StatusPill>
              ) : k === "action" ? (
                <Link className="btn secondary" to={`/officer/reviews/${r.id}`}>
                  Open review
                </Link>
              ) : (
                r[k]
              )
            }
          />
        ) : (
          <EmptyState label="No reviews match these filters." onReset={reset} />
        )}
        <Pagination
          page={page}
          setPage={setPage}
          total={filtered.length}
          pageSize={pageSize}
          setPageSize={setPageSize}
        />
      </Section>
    </MetricPage>
  );
}

export function ReviewDetailsPage() {
  const { reviewId } = useParams();
  const navigate = useNavigate();
  const { reviews, alerts, addReviewNote, updateReview, toggleReviewAction } =
    useDemoStore();
  const r = reviews.find((x) => x.id === reviewId);
  const [note, setNote] = useState("");
  const [nextDate, setNextDate] = useState(r?.next || "");
  if (!r) return <NotFound kind="Review" to="/officer/reviews" />;
  const linked = alerts.find((a) => a.projectId === r.projectId);
  const actions = [
    "Verify source submission and documents",
    "Contact implementing agency",
    "Check progress variance with approved schedule",
    "Schedule follow-up review",
    "Update review outcome",
  ];
  const outcomes = [
    "Continue monitoring",
    "Seek clarification",
    "Escalate",
    "Close with no action",
  ];
  const stage =
    r.state === "Complete"
      ? 5
      : r.state === "Monitoring"
        ? 4
        : r.completedActions.length >= 3
          ? 3
          : r.completedActions.length
            ? 2
            : 1;
  const saveNote = () => {
    addReviewNote(r.id, note);
    setNote("");
  };
  return (
    <div className="page">
      <PageHeroHeader
        title="Review Details"
        subtitle="Officer workflow, evidence and follow-up for the selected case."
        breadcrumb="Reviews / Open Review"
      />
      <button
        className="text-link page-back"
        onClick={() => navigate("/officer/reviews")}
      >
        ← Back to reviews
      </button>
      <div className="detail-layout">
        <div className="stack">
          <Section
            title={r.project}
            action={<StatusPill>{r.state}</StatusPill>}
          >
            <div className="summary-grid">
              <Summary label="Review ID" value={r.id} />
              <Summary label="Review Type" value={r.type} />
              <Summary label="Priority" value={r.priority} />
              <Summary label="Assigned Officer" value={r.assigned} />
              <Summary label="Due Date" value={r.next} />
              <Summary label="Linked Alert" value={linked?.id || "None"} />
            </div>
          </Section>
          <Section title="Review Workflow">
            <Lifecycle
              horizontal
              stages={[
                "Opened",
                "Assigned",
                "Evidence Checked",
                "Action Planned",
                "Monitoring",
                "Closed",
              ]}
              current={stage}
            />
          </Section>
          <Section title="Officer Notes">
            <div className="notes-list">
              {r.notes.length ? (
                r.notes.map((n, i) => (
                  <InfoCard
                    key={`${n.date}-${i}`}
                    title={`${n.author} · ${n.date}`}
                    text={n.text}
                  />
                ))
              ) : (
                <p className="muted">No officer notes yet.</p>
              )}
            </div>
            <div className="note-composer">
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Add an evidence-backed review note"
              />
              <button
                className="btn primary"
                disabled={!note.trim()}
                onClick={saveNote}
              >
                Add note
              </button>
            </div>
          </Section>
          <Section title="Recommended Actions">
            <div className="checklist">
              {actions.map((x, i) => (
                <label key={x}>
                  <input
                    type="checkbox"
                    checked={r.completedActions.includes(i)}
                    onChange={() => toggleReviewAction(r.id, i)}
                  />
                  <span>{x}</span>
                  <StatusPill>
                    {r.completedActions.includes(i) ? "Completed" : "Pending"}
                  </StatusPill>
                </label>
              ))}
            </div>
          </Section>
          <Section title="Review Outcome and Next Step">
            <div className="outcome-grid">
              {outcomes.map((x) => (
                <button
                  onClick={() =>
                    updateReview(r.id, {
                      outcome: x,
                      state:
                        x === "Close with no action"
                          ? "Complete"
                          : x === "Continue monitoring"
                            ? "Monitoring"
                            : "Action required",
                    })
                  }
                  className={r.outcome === x ? "selected" : ""}
                  key={x}
                >
                  {x}
                </button>
              ))}
            </div>
            <div className="review-next">
              <label>
                Next review date
                <input
                  value={nextDate}
                  onChange={(e) => setNextDate(e.target.value)}
                  placeholder="25 Jun 2026"
                />
              </label>
              <button
                className="btn primary"
                onClick={() => updateReview(r.id, { next: nextDate })}
              >
                Save next step
              </button>
            </div>
          </Section>
        </div>
        <aside className="stack">
          <Section title="Project Snapshot">
            <div className="rail-body">
              <Summary label="Project" value={r.project} />
              <Summary label="Sector" value="Coal" />
              <Summary label="Data Quality" value="Good" />
              <Summary label="Schedule Outlook" value="High concern · 74%" />
              <Link
                className="btn secondary full"
                to={`/officer/projects/${r.projectId}`}
              >
                View project
              </Link>
            </div>
          </Section>
          <Section title="Evidence Pack">
            <div className="rail-body">
              <Summary label="Source Report" value="Monthly Progress Report" />
              <Summary label="Reporting Month" value="June 2026" />
              <Summary label="Page Reference" value="Pages 12–14" />
              <Summary label="Evidence Hash" value="a3f9d2e7…8c4b" />
              {linked && (
                <Link
                  className="btn secondary full"
                  to={`/officer/alerts/${linked.id}`}
                >
                  View linked alert
                </Link>
              )}
            </div>
          </Section>
          <Section title="Milestone Journey">
            <div className="mini-journey">
              <MilestoneJourney />
            </div>
          </Section>
        </aside>
      </div>
    </div>
  );
}

function Summary({ label, value }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
function InfoCard({ title, text }) {
  return (
    <article className="info-card">
      <span>
        <AlertTriangle />
      </span>
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>
    </article>
  );
}
function Lifecycle({ stages, current, horizontal = false }) {
  return (
    <div className={`lifecycle ${horizontal ? "horizontal" : ""}`}>
      {stages.map((s, i) => (
        <div
          className={i < current ? "done" : i === current ? "current" : ""}
          key={s}
        >
          <span>
            {i < current ? (
              <CheckCircle2 />
            ) : i === current ? (
              <ClipboardCheck />
            ) : (
              <Clock3 />
            )}
          </span>
          <strong>{s}</strong>
          <small>
            {i === current
              ? "Current stage"
              : i < current
                ? "Completed"
                : "Pending"}
          </small>
        </div>
      ))}
    </div>
  );
}
function NotFound({ kind, to }) {
  return (
    <div className="page">
      <PageHeroHeader
        title={`${kind} not found`}
        subtitle={`The requested ${kind.toLowerCase()} is not available in the current dataset.`}
      />
      <Link className="btn primary" to={to}>
        Return to {kind.toLowerCase()}s
      </Link>
    </div>
  );
}

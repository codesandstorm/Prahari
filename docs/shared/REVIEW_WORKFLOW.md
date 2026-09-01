# Review and Engineering Workflow

**Owner:** Sandarbh (technical integration owner)
**Area:** Shared / Process
**Document Type:** REFERENCE
**Status:** APPROVED
**Last Updated:** 2026-09-01
**Depends On:** NONE
**Used By:** Entire team, Codex/Antigravity agents
**Canonical:** YES

---

## Research → Decision → Implementation Flow

```
Teammate researches
        ↓
Writes: docs/team/<name>/<TOPIC>.md
  (Status: RESEARCH IN PROGRESS)
        ↓
Shares with team / cross-review
        ↓
Conclusion accepted
        ↓
Summary migrated into: docs/shared/<CANONICAL_DOC>.md
  (Status: APPROVED)
        ↓
Code implements the shared decision
        ↓
Tests written and passing
        ↓
Independent reviewer confirms
        ↓
Git commit / Pull Request
```

**Rule:** Code implementing a decision must reference the canonical document in
comments or docstrings. Not the research file — the shared canonical decision.

---

## Code-Agent Workflow (Codex / Antigravity)

When a coding agent implements a task:

```
Agent reads: docs/shared/ for current decisions
        ↓
Agent implements: minimal scope, explicit reasoning
        ↓
STOP — agent does not proceed autonomously
        ↓
Human reviewer examines the change
        ↓
Findings documented
        ↓
Minimal targeted fixes
        ↓
Tests run and passing
        ↓
Checkpoint committed
```

**Critical rule:** One writer at a time. Do not allow simultaneous agent edits
to the same files. Each agent session handles one clearly defined task.

**Reading order for agents:**
1. `docs/README.md` — orientation
2. `docs/shared/PROJECT_OVERVIEW.md` — conceptual model
3. `docs/shared/CURRENT_TECHNICAL_HYPOTHESIS.md` — architecture
4. `docs/shared/DATA_CONTRACT.md` — data model
5. `docs/shared/GATE_STATUS.md` — what is active
6. `docs/shared/OPEN_QUESTIONS.md` — what is unresolved (do not answer these)

---

## Document Change Policy

| Situation | Action |
|---|---|
| Adding research | Write under `docs/team/<owner>/` |
| Conclusion accepted | Summarise/migrate into `docs/shared/` |
| Decision changes | Mark old material SUPERSEDED; add new DECISION_LOG entry |
| Architecture changes | Update DECISION_LOG + notify team |
| Data contract changes | Notify Backend + ML + Frontend owners |
| API contract changes | Notify Frontend |
| Prediction contract changes | Notify Backend + Frontend |

---

## Document Status Transitions

```
RESEARCH IN PROGRESS
        ↓ (team review)
REVIEW REQUIRED
        ↓ (consensus)
APPROVED  or  APPROVED WITH LIMITATIONS
        ↓ (if later superseded)
SUPERSEDED  →  link to canonical replacement
```

BLOCKED: waiting on another gate/team before progress is possible.

---

## Pull Request Rules

Every PR that changes documentation must:
- Update the document's `Last Updated` field
- Update `Depends On` if dependencies changed
- Add a DECISION_LOG entry if a architectural decision changed
- Run `python scripts/validate_docs.py` before requesting review

---

## Gate Advancement Rules

A gate may only advance when:
1. All milestones are marked `VERIFIED` in `GATE_STATUS.md`
2. At least one independent review of extraction/modelling has been completed
3. The team lead has explicitly approved in a DECISION_LOG entry

Milestones are VERIFIED by evidence, not by assumption or convenience.

# PRAHARI Alert and Review V1 Adversarial Self-Audit

## Resolved findings

SEVERITY: High  
FILE: `backend/workflow_service.py`  
FUNCTION / LINE: automatic resolution and reopening  
PROBLEM: Resolution initially failed to advance `last_seen_month`, so evidence from the same reporting month could reopen the episode. Automatic reopen also did not reset a closed review.  
WHY IT MATTERS: Same-month churn would damage idempotency and operational history.  
MINIMAL FIX: Store the resolution evidence month and use the same review-reset rule for automatic and manual reopen.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: High  
FILE: `alembic/versions/20260913_02_alert_review_workflow_v1.py`  
FUNCTION / LINE: upgrade  
PROBLEM: Existing databases could receive new columns without the new alert status/severity checks.  
WHY IT MATTERS: Application validation alone does not protect direct database writes.  
MINIMAL FIX: Add missing named checks conditionally and preserve downgrade compatibility.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: High  
FILE: `backend/product_intelligence.py`  
FUNCTION / LINE: intelligence dashboard summary  
PROBLEM: The first implementation counted synthetic database records in the real summary and reported zero persisted synthetic workflow records.  
WHY IT MATTERS: Mixed operational counts would breach the real/synthetic evidence boundary.  
MINIMAL FIX: Apply explicit `data_origin` filters to project, alert and review counts and test both modes together.  
ARCHITECTURAL CHANGE REQUIRED? No

## Accepted residual findings

SEVERITY: Medium  
FILE: `backend/workflow_api.py`  
FUNCTION / LINE: review listing  
PROBLEM: Some JSON-derived filters and queue sorts run after loading the origin-specific result set.  
WHY IT MATTERS: Memory and latency grow with a production-scale workflow table.  
MINIMAL FIX: Use PostgreSQL JSON expressions and SQL ordering after query-volume evidence justifies the change.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Medium  
FILE: deployment boundary  
FUNCTION / LINE: all officer mutation routes  
PROBLEM: V1 records actor identifiers but does not authenticate them.  
WHY IT MATTERS: Production audit attribution requires verified identity and roles.  
MINIMAL FIX: Bind `actor_id` to the future authenticated principal and authorize actions by role.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Low  
FILE: `config/alert_policy_v1.json`  
FUNCTION / LINE: persistence threshold  
PROBLEM: Three valid cycles is governed but has not yet been evaluated against officer workload.  
WHY IT MATTERS: It may over- or under-prioritize recurrent observations.  
MINIMAL FIX: Review the versioned threshold using real workflow outcomes; do not silently tune it.  
ARCHITECTURAL CHANGE REQUIRED? No

No unresolved Critical or High finding remains. The audit found no frontend edits, model retraining, raw-data mutation, direct probability trigger, synthetic/real mixing, or LLM mutation authority.

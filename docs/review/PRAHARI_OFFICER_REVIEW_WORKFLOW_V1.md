# PRAHARI Officer Review Workflow V1

Officer Review is the administrative work record attached one-to-one to an alert episode. It keeps review status, alert status, priority, evidence quality, model reliability and model probability as separate concepts.

Each review stores assignment, structured reason codes, priority, verification status, outcome, next-review date, recommended follow-up, timestamps, notes and bounded actions. Human mutations require an actor identifier. Notes and actions are append-only; changing a review creates an alert-history event.

Priority is initialized conservatively from the governed alert candidate. The queue never ranks by a raw prediction probability. Supported actions are bounded by `officer-review-v1.0`, including source verification, progress or milestone review, monitoring the next cycle and requesting data verification. It does not encode sanctions, approvals or blame.

Closure requires a structured outcome. `CLOSED_NO_ACTION` requires `NO_ACTION_REQUIRED`. Resolution additionally requires current clear/usable evidence or verified/corrected evidence for a data-quality episode. A reopened episode resets a completed review to `NOT_STARTED` while retaining its historical events, notes and actions.


# PRAHARI Dashboard Output Contract

Exactly four main views are permitted.

## 1. Portfolio / Review Queue — “Where should I look first?”

Cards: eligible monitored projects, high review priority, schedule warnings, low-reliability cases, and data-quality review cases. Cost warnings remain hidden until a cost target passes validation.

Table: Project, Ministry, Sector, State, Implementing Agency, Target/Horizon, calibrated risk (only after validation), Reliability, Data Quality, Review Priority. Filters: ministry, sector, state, agency, cost band, approximate/current phase, target, reliability.

## 2. Project Intelligence — “What may happen and what supports it?”

Show target, horizon, calibrated probability or `PREDICTION WITHHELD`, reliability, data quality, review priority, point-in-time contributors, progress/expenditure trajectories, revision history, validated peer benchmark, milestone/issue evidence when available, provenance, as-of month, and versions. Use “supporting signal,” never “cause.”

## 3. Model Validation — “Why should I trust it?”

Show rules versus logistic baseline versus ML; PR-AUC, Brier, precision, recall, false alerts per 100, lead time, temporal split, calibration, and subgroup results. Clearly separate Model A/B measured results from Model C’s future data contract. Every current metric carries `PROVISIONAL — NOT FINAL SIH CLAIM`.

## 4. Grounded Officer Assistant

The LLM receives only the evidence object. It may explain, summarize, and answer grounded questions. It may not generate or modify probability, invent causes/data, accuse an organization, override abstention, or hide uncertainty. A deterministic template is the fallback.

Never display corruption/fraud scores, causal blame, arbitrary confidence, unsupported contractor identity, future information, or an uncalibrated probability as operational truth.

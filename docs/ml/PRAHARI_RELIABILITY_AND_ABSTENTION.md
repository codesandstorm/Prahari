# PRAHARI Reliability and Abstention V1

**Status:** PROVISIONAL

Risk, reliability, data quality and review priority are separate outputs. Reliability never comes from the predicted probability.

V1 returns `WITHHELD` with null probability and null risk band when identity is not exact, the anchor is unavailable, the target cohort is inapplicable, the project is completed, an artifact is missing, temporal evidence is unavailable, history span is under thirteen months, or human target adjudication/calibration confirmation is pending.

The thirteen-month boundary is conservative evidence from the fixed short-history analysis, not a claim that thirteen months is universally optimal. It must be reassessed on later data. No withheld result means low risk.

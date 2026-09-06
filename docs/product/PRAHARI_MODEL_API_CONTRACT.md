# PRAHARI Prediction Evidence API Contract

Required object fields:

```json
{
  "prediction_id": "S1-3M-PRH-123-2026-01",
  "canonical_project_id": "PRH-123",
  "as_of_month": "2026-01",
  "target": "S1",
  "horizon_months": 3,
  "eligibility": true,
  "calibrated_probability": null,
  "risk_band": null,
  "reliability_band": "ABSTAIN",
  "reliability_reasons": [],
  "data_quality_status": "REVIEW",
  "review_priority": "DATA_QUALITY_REVIEW",
  "top_contributors": [],
  "rule_result": null,
  "peer_summary": null,
  "trajectory_summary": null,
  "provenance": [],
  "model_version": "PROVISIONAL",
  "feature_version": "features-v0.1",
  "target_version": "S1-v0.1-provisional",
  "calibration_version": "UNVALIDATED",
  "abstention_reason": "INSUFFICIENT_HISTORY"
}
```

Risk probability and reliability are different. When abstaining, probability and risk band must be null. The API never accepts an LLM-generated numeric prediction and exposes human-readable contributors rather than raw SHAP arrays.

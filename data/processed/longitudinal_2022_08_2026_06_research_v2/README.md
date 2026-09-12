# Prediction Research V2 dataset

`project_month.csv` is a deterministic, locally generated 68,641-row research artifact and is intentionally excluded from Git, following the existing V1 large-data convention. Regenerate it from immutable local PDFs and the unchanged V1 dataset with:

```text
python scripts/build_prediction_research_v2.py --raw-root <path-to-data/raw>
```

The committed source ledger, report calendar, schema ledger, field-availability ledger, identity-continuity audit and dataset metadata describe and fingerprint the generated artifact. February 2025 is missing; December 2023 and April/May 2024 are aggregate-only. July 2026 is excluded.

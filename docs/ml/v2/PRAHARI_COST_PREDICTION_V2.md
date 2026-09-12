# PRAHARI Cost Prediction V2

**Status:** MACHINE_PROVISIONAL / PARTIAL  
**Research mode:** `PROTOTYPE_RESEARCH_OVERRIDE`  
**Production release:** WITHHELD

Cost Prediction V2 extends the existing Prediction Research V2 dataset, identity, coverage, temporal-fold, model, calibration, ensemble and governance infrastructure. It does not create a parallel production pipeline and does not modify the canonical V1 dataset or raw reports.

The engine predicts an approved upward cost-state change, not exact final cost. C1 asks whether the first approved upward revision will appear within T+1…T+3. C2 asks whether a project already carrying an approved upward revision will increase further above the baseline frozen at T. Anticipated cost and cumulative expenditure are evidence fields, never labels.

The canonical research dataset contains 68,641 project-month observations for 3,777 projects from August 2022 through June 2026. Coverage gaps are censored. July 2026 is not used or scored.

## Result

C1 3M Basic has 23,880 eligible anchors, 509 machine-provisional events, 2,815 projects and three admitted temporal folds. C2 3M has 4,250 anchors and 131 events, but zero admitted folds. C1 6M has two admitted support folds; C2 6M and both 12M targets are unsupported for model claims.

Rule, Logistic Regression, HistGradientBoosting, Random Forest, XGBoost and equal soft voting were run under identical folds. No candidate met the predeclared combination of temporal stability, useful recall and acceptable false-alert burden. Therefore no deployable research pipeline, cost probability, cost risk band, driver ranking, alert or operational model is released. This is a scientifically useful negative result, not a training failure.

Run reproducibly with:

```powershell
python scripts/run_cost_prediction_v2.py --research-mode PROTOTYPE_RESEARCH_OVERRIDE
```

See `outputs/ml/prediction_research_v2/cost/cost_v2_status.json` for the machine-readable verdict.

# PRAHARI Cost Prediction V3

Status: **complete research evaluation; no model admitted; production withheld**

Cost Prediction V3 extends the immutable V2 research layer with admitted historical observations. It predicts approved cost-state deterioration, not expenditure, anticipated cost, final project cost, causation, blame, or contractor performance.

The primary C1 question is whether a project with no approved upward cost revision at month T receives its first approved upward revised cost within three months. C2 asks whether a project already revised upward at T receives a further approved increase over the frozen T baseline. Six months is secondary research; twelve months is support-check only.

All labels remain `MACHINE_PROVISIONAL` under `PROTOTYPE_RESEARCH_OVERRIDE`. Production model release, backend probability exposure, alerts and officer-facing operational claims remain withheld.

The tested models are the fixed rule, logistic regression, HistGradientBoosting, Random Forest, XGBoost, and an equal soft vote. No additional algorithm was introduced. Weighted voting and stacking are not admitted because the equal ensemble did not establish a material gain and independent temporal out-of-fold evidence is insufficient.

Reproduction:

```text
python scripts/build_cost_prediction_v3_history.py --raw-root <READ_ONLY_RAW_ARCHIVE>
python scripts/run_cost_prediction_v3.py --research-mode PROTOTYPE_RESEARCH_OVERRIDE
python -m pytest -m "not integration" -q
```

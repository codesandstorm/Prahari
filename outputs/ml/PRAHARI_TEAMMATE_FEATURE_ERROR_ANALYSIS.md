# Teammate feature error analysis

All counts use the frozen test period and each model's validation-selected 90th-percentile alert threshold. They are descriptive, not a production claim.

| Variant | False positives | False negatives |
|---|---:|---:|
| COMPACT_V2 | 117 | 299 |
| V2_PLUS_EXPENDITURE_CHANGEPOINT | 122 | 297 |
| V2_PLUS_RECOVERY | 130 | 295 |

Expenditure changepoints corrected 6 baseline false positives but introduced 11 new false positives. They corrected 7 baseline false negatives but introduced 5 new false negatives. Recovery features are retained only as reliability context because their aggregate false-alert burden rose.

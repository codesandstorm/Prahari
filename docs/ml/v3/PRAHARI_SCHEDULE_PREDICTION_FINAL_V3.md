---
title: PRAHARI Schedule Prediction Final V3
status: CURRENT
---

# PRAHARI Schedule Prediction Final V3

Schedule Final V3 executes the frozen S1/S2 research design under `PROTOTYPE_RESEARCH_OVERRIDE`. Labels remain `MACHINE_PROVISIONAL`; the override permits controlled hackathon research, not production release or a claim of human validation.

The authoritative input is the frozen August 2022–June 2026 Prediction Research V2 dataset. S1 means first explicit reported revised schedule deterioration within the horizon for an eligible not-yet-deteriorated project. S2 means further explicit reported revised deterioration relative to the approved date frozen at T. A V2 defect that could promote a changed original date through a fallback helper was corrected in the versioned `v3-explicit-revised` target contract. Original-date changes and within-horizon reversals are censored. Missing dates, disappearance, corrections, aggregate-only months and source gaps never become deterioration events.

No three-month candidate passed the complete admission policy. S1 has only one admitted fold. S2 has two, but performance and false-alert burden vary materially and the current target truth is provisional. Both operational targets therefore remain withheld, with null probability and risk band.

Run with:

```text
python scripts/run_schedule_prediction_final_v3.py --research-mode PROTOTYPE_RESEARCH_OVERRIDE
```

July 2026 remains untouched prospective evidence.

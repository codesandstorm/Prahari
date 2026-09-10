# PRAHARI S1 Model Card V1

**Status:** RESEARCH ONLY

- Target: first approved schedule deterioration within three months.
- Cohort: exact identities, ongoing at T, no prior deterioration, complete outcome coverage and presence.
- Features: Compact V2.1, fourteen ordered as-of-T features with calendar-safe temporal calculations.
- Primary split: train through May 2025; validation June–November 2025; development test December 2025–March 2026.
- Candidate artifact: conservative HistGradientBoosting with validation-fit Platt calibration.
- Intended use: research and SIH prototype engineering after explicit availability checks.
- Prohibited use: causal attribution, sanctions, automated approvals, or production probability claims.

Known limitations include unadjudicated machine labels, repeated inspection of the development test, schema/population shift, weak short-history performance and no independent calibration confirmation. Operational probability and risk band are withheld.

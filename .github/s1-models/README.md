# PRAHARI S1 — Schedule Deterioration Prediction

## Objective

S1 predicts whether a project that has not yet experienced an approved
schedule deterioration at anchor month `T` will experience its first
schedule deterioration within the next 3 months.

## Prediction Unit

Project-month.

## Dataset

- 48,326 project-month observations
- 3,417 canonical projects
- July 2023 — June 2026
- 5,982 eligible S1 anchors
- 1,417 events
- 4,565 non-events

## S1 Eligibility

An anchor is eligible only when:

1. Project identity is resolved.
2. Original completion date is available.
3. No previous observation contains a revised completion date later
   than the original completion date.
4. At least two observations exist through the anchor.
5. The immediately preceding interval is one calendar month.
6. All three future outcome months are project-level.
7. The project is observed in all three future months.

Missing or aggregate-only future observations are treated as censoring,
not as negative outcomes.

## Target

EVENT = first approved schedule deterioration within the next 3 months.

NON-EVENT = complete observation of all three future months with no
qualifying schedule deterioration.

## Feature Contract

The final 12-feature contract contains:

- log original cost
- planned duration
- project age
- expenditure-to-cost ratio
- physical progress
- physical progress missing indicator
- 1-month progress delta
- 3-month progress delta
- 1-month expenditure delta
- 2-month stagnant progress indicator
- history months
- correction count

Future schedule dates, future progress, future expenditure and other
post-anchor information are excluded from predictors.

## Models Compared

- Logistic Regression
- HistGradientBoosting
- Random Forest
- XGBoost
- Rule baseline

## Validation

S1 was evaluated using temporal rolling validation, feature robustness,
feature drift, feature-target stability, regime analysis and calibration.

## Human Validation

A 60-case validation sample was created:

- 10 EVENT + 10 NON-EVENT from Apr-Jun 2025
- 10 EVENT + 10 NON-EVENT from Jul-Nov 2025
- 10 EVENT + 10 NON-EVENT from Dec 2025-Mar 2026

Each case contains source provenance including source ID, PDF page,
printed page number, table and raw row locator.

## Status

S1 research and model evaluation completed.

Human validation artifacts are retained separately from the frozen
machine-generated S1 labels.

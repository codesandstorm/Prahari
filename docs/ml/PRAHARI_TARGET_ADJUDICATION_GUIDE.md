# PRAHARI S1/S2 Target Adjudication Guide

**Owner:** PRAHARI ML validation team  
**Status:** REVIEW REQUIRED  
**Document type:** AUDIT

## Purpose

This review determines whether a change in published schedule dates represents a genuine approved deterioration. Technical flags help locate difficult cases; they are not decisions.

## Target meanings

- **S1:** the project had no approved schedule deterioration at T, then first shows a completion date later than its original approved completion date within T+1 to T+3.
- **S2:** the project was already deteriorated at T, then its approved/reported completion date increases again within T+1 to T+3.

Always compare the original, revised and effective published dates across the timeline. Confirm that the row refers to the same project and that the cited report page contains the displayed values.

## Decision procedure

1. Verify project identity and source SHA/page reference.
2. Read T-1, T and the event-month evidence together.
3. Determine whether S1 or S2 eligibility is correct at T.
4. Check whether the later date persists, reverts, changes format or coincides with an original-date rewrite.
5. Select one allowed label. Never leave a substantive decision only in notes.
6. Record reviewer ID, confidence, evidence/page/identity verification and timestamp.

## Label guidance

- `CONFIRMED_FIRST_SCHEDULE_DETERIORATION`: source evidence supports a genuine first S1 increase.
- `CONFIRMED_FURTHER_DETERIORATION`: source evidence supports a genuine further S2 increase.
- `CORRECTION_NOT_EVENT`: evidence indicates correction of an erroneous or stale value rather than deterioration.
- `DATE_NORMALIZATION_ARTIFACT`: only representation/format/parsing changed.
- `IDENTITY_UNCERTAIN`: cross-month rows cannot defensibly be linked to one project.
- `SOURCE_INCONSISTENCY`: reports contradict one another and truth cannot yet be resolved.
- `INSUFFICIENT_EVIDENCE`: source/page/value evidence is unavailable or inadequate. Missing evidence is never a negative.
- `OTHER`: requires an explanatory note and later resolution.

Date decreases and later reversions are warning signs, not automatic corrections. A missing report or missing project row must be treated as insufficient evidence/censoring. A schema transition requires checking column meaning on both sides. Do not call a date “approved” unless the report semantics support that wording.

## Working arrangement

Sandarbh should review S1 rows first; Akshita should review S2 rows first. They should then cross-review low-confidence, correction-like, schema-transition and identity-warning cases. Preserve the original CSVs and save completed copies under a new reviewer/version name before running the validator.

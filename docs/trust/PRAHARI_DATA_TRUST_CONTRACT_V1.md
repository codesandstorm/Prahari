# PRAHARI Data Trust Contract V1

**Owner:** PRAHARI data and ML team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** REFERENCE

Version: `data-trust-v1`. States are `PASS`, `WARN`, `FAIL`, `UNKNOWN`; there is no numeric trust score.

Dimensions are identity, source, temporal coverage, history sufficiency, freshness, Compact V2 feature completeness, schema support and provenance completeness. The governed prototype minimum is thirteen contiguous recent project-level months, named `PROVISIONAL_VALIDATED_MINIMUM_HISTORY_V1`. This threshold reflects current short-history evidence and must be revalidated later.

`HUMAN_TARGET_VALIDATION_PENDING`, `CALIBRATION_NOT_CONFIRMED` and `MODEL_NOT_RELEASED` are not Data Trust failures. They belong to Model Release Readiness.

Exact identity uses only `RESOLVED_EXACT` and its authoritative identity method. Runtime fuzzy matching is prohibited. Source verification compares source ID and SHA-256 with the registered manifest. Missing source, aggregate-only and project disappearance months are listed and never synthesized.

Future structured CUF/API submissions use separately versioned schema/rule contracts. Rules are explicitly classified as `GENERIC_STRUCTURED_INPUT`, `OFFICIALLY_VERIFIED_CUF` or `PROPOSED_FUTURE_FIELD`; V1 makes no claim that proposed dates or milestones are verified CUF fields. Warnings identify suspicious evidence; they do not declare it false.

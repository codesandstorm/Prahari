# Project Lifecycle Data Availability
The primary inventories describe **ongoing** projects. Disappearance is not evidence of completion, and appearance is not necessarily project initiation.

OCMS reports include completed-project sections and annexures, while PAIMANA reports commonly list projects completed, added, and frozen/deleted during the reporting month. These sources are useful for a future lifecycle crosswalk, but they have not been normalized into lifecycle events in this Gate 2 build. Table names and availability vary across report families, and the five aggregate-only months cannot supply project-level lifecycle events.

Consequences:

- early disappearance remains `UNKNOWN`, never `COMPLETED`;
- late appearance remains `UNKNOWN`, never `NEW_PROJECT`, unless an official added-project record is linked;
- ongoing-only modeling would suffer survivor bias;
- completion and deletion events require a separate provenance-preserving extractor and human validation;
- prediction anchors crossing unavailable project-level months require censoring.

Recommended next data task: extract the official completed/added/frozen tables into a separate event table keyed only through exact official identifiers. Never infer lifecycle from presence patterns.

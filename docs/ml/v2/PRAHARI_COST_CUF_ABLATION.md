# PRAHARI Cost CUF and Feature Ablation

**Status:** PROVISIONAL RESEARCH MAPPING

Cost Basic Long-History V1 uses ten C1 features: log original cost, planned duration, project age, expenditure/original cost, expenditure/current approved cost, observed history span, remaining approved schedule, recent expenditure velocity, known schedule-deterioration state and known schedule-revision months. C2 additionally uses current approved cost-revision percentage and prior approved cost-revision count.

Cost Compact V2 adds current physical progress, its missingness indicator, progress-versus-elapsed gap and trailing stagnation. These fields are evaluated only on compatible anchors. C1 deliberately excludes current cost-revision magnitude because eligibility fixes it at no prior approved upward revision.

Every value is available at T. Missing values are retained and imputed inside each training fold. No anticipated future cost, future expenditure, final completed cost, future completion status, future identity correction or post-event feature is used.

The machine-readable CUF matrix is conservative: it distinguishes present Flash Report fields from publicly verified PAIMANA concepts and records when no verified CUF evidence exists in the repository. Contractor performance is unavailable historically and rejected from the current model; it is not fabricated.

Only one Compact C1 fold was admitted and no Compact C2 fold was admitted. Therefore the present evidence cannot claim Compact V2 improves cost warning or quantify CUF’s incremental predictive value.

# PRAHARI Product Intelligence V1 Adversarial Self-Audit

**Owner:** Independent Product Intelligence Review
**Status:** COMPLETE
**Last Updated:** 2026-09-13

Critical findings: none. High findings: none. During implementation, mode/origin mismatch checks, subject exclusion, historical as-of filtering, minimum peer support, null withheld outputs, canonical hash checks, and invalid-fixture isolation were added and tested.

SEVERITY: Medium  
FILE: `data/processed/longitudinal_2023_07_2026_06_mixed/project_master.csv`  
FUNCTION / LINE: sector field coverage  
PROBLEM: Reliable sector is present for only a small portion of the current real project master.  
WHY IT MATTERS: Many real projects cannot use sector-specific peer groups and must fall back transparently.  
MINIMAL FIX: Improve sector taxonomy only from verified source evidence; until then preserve UNKNOWN and the portfolio fallback.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Medium  
FILE: `backend/product_intelligence.py`  
FUNCTION / LINE: `_record` and `real_project_intelligence`  
PROBLEM: Historical Flash Reports do not contain the richer CUF milestone, land, ROW, clearance, and tender families.  
WHY IT MATTERS: Real Watch and benchmark coverage is narrower than sandbox coverage.  
MINIMAL FIX: Populate these families only after governed CUF/PAIMANA ingestion is available.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Low  
FILE: `data/synthetic/cuf_sandbox_v1/`  
FUNCTION / LINE: generated portfolio  
PROBLEM: Synthetic trajectories are plausible controlled scenarios, not a generative representation validated against government operational distributions.  
WHY IT MATTERS: Synthetic counts and outcomes cannot support real-world accuracy or prevalence claims.  
MINIMAL FIX: Keep all outputs labelled as pipeline demonstrations; do not publish synthetic performance claims.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Low  
FILE: `src/benchmarking/service.py`  
FUNCTION / LINE: `PeerBenchmarkService.benchmark`  
PROBLEM: Percentiles are descriptive and do not provide statistical significance or causal meaning.  
WHY IT MATTERS: A high adverse percentile must not be described as proof of project failure.  
MINIMAL FIX: Preserve the present wording, peer count, quartiles, directionality, and limitation fields in the frontend.  
ARCHITECTURAL CHANGE REQUIRED? No

# PRAHARI Synthetic Data Governance

**Owner:** PRAHARI Data Governance
**Status:** APPROVED
**Last Updated:** 2026-09-13

Synthetic CUF records are engineering demonstration evidence only. The mandatory origin is `SYNTHETIC_CUF_PROTOTYPE`; the dataset, generator, scenario, seed, timestamp, and file fingerprints are recorded in `generation_metadata.json`.

Hard boundaries:

- storage is restricted to `data/synthetic/`;
- synthetic and real records cannot share a benchmark population;
- the canonical historical loader reads only `data/processed/longitudinal_2023_07_2026_06_mixed/`;
- synthetic rows cannot enter target evaluation, model selection, real training, or official evidence;
- synthetic endpoints use `/api/v1/sandbox/...` and return `mode=SYNTHETIC_SANDBOX`;
- synthetic evidence has no official PDF page, table, or SHA and says so explicitly;
- invalid cases are isolated validator fixtures, not normal observations.

Allowed claim: PRAHARI has a governed, reproducible CUF-style engineering sandbox. Prohibited claim: sandbox results establish real-world prediction accuracy or represent PAIMANA records.

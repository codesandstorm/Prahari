# PRAHARI Real vs Synthetic Boundary

**Owner:** PRAHARI Data Governance
**Status:** APPROVED
**Last Updated:** 2026-09-13

Real evidence comes from immutable Flash Reports and canonical `project_month.csv`, uses `HISTORICAL_FLASH_REPORT`, and may carry source ID, SHA-256, physical page, and table references. Synthetic evidence is generated CUF-style demonstration data, uses `SYNTHETIC_CUF_PROTOTYPE`, and must never render as an official report reference.

The type contract validates mode/origin agreement and rejects mixed-origin evidence. The benchmark service separately checks mode/origin agreement and filters the peer pool to the same origin. Storage and endpoints are also separate.

Both modes preserve the same scientific release state: schedule and cost predictions are withheld, probabilities and risk bands are null, and synthetic outputs cannot activate a model. Ask PRAHARI receives the mode, origin, subsystem outputs, evidence, and explicit constraints; it cannot override them.

The reproducibility build verifies canonical real artifact hashes before and after sandbox generation. Any change fails the build.

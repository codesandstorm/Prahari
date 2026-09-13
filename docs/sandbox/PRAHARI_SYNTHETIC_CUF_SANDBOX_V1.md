# PRAHARI Synthetic CUF Sandbox V1

**Owner:** PRAHARI Product Intelligence
**Status:** COMPLETE
**Last Updated:** 2026-09-13

The sandbox demonstrates how the existing typed CUF contract and deterministic Implementation Watch behave with richer structured inputs. It is not PAIMANA data, government evidence, model validation, or an operational prediction source.

The generator uses seed `26103`, version `synthetic-cuf-generator-v1.0`, and a fixed generation timestamp. It creates 1,000 projects with 24 monthly observations each (July 2024–June 2026), including 120 curated scenario fixtures. Related milestone, land, ROW, clearance, tender, and funding tables use the same project/month keys. Run `python scripts/build_product_intelligence_v1.py` to reproduce the files and samples.

Every row carries `data_origin=SYNTHETIC_CUF_PROTOTYPE`. All files live under `data/synthetic/cuf_sandbox_v1/`; none are loaded by the canonical real-data loader. Invalid validator cases live in `invalid_validation_fixtures.json`, are marked `VALIDATOR_TEST_ONLY`, and are excluded from the portfolio.

The scenario catalog covers healthy, lagging, stagnant, high-velocity, financial, milestone, land, ROW, clearance, tender, reporting, provenance, recovery, improving, multi-pressure, and insufficient-data cases. Its expected Watch status is checked against the real Implementation Watch engine.

No synthetic ML experiment was implemented. Therefore there are no synthetic accuracy claims or model artifacts.

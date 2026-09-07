# PRAHARI LLM Candidate Benchmark V1 — preregistration

Frozen before formal generation on 2026-09-07. Base commit: `26fb06da2d106a80d07303c3d3bab122fe5aa440`.

## Candidates

Only these exact installed Ollama tags are eligible: `llama3:8b`, `qwen3:8b`, `gemma3:4b`, `gemma3:12b`. `deepseek-coder:6.7b` and `gemma4:latest` are excluded from formal ranking. No substitutions, pulls, or best-of-N retries are permitted.

## Frozen benchmark

- Benchmark version: `1.0.0`
- Cases: 65, including 35 marked CRITICAL
- Case-set SHA-256: `366493644a4a0004c5198e14f1bf7ef90c8e74827509a2ffa5cde3e93fb64ed5`
- System prompt: `system_prompt_v1`
- System-prompt SHA-256: `876a84c44608d0b17cc42d0457f87fbb79f5994ab17859ea69ecc702d131e3fa`
- Evidence schema version: `1.0.0`; file SHA-256 `1a1a222db71675ebd944b6e93c6b734d7f0d3a4a567a6056d8aa7e63a61757da`
- Response schema version: `1.0.0`; file SHA-256 `3b3d988b1abfc13ed1c0f0c7850d3bfdc485b5d1029e45a51bf88de30ce4c351`
- Case schema version: `1.0.0`; file SHA-256 `8fe0f2aa895034f5e1abe2d91580456a7340eab54ca28eeeaafbbf3cfb746532`
- Evaluator version: `1.0.0`; file SHA-256 `578b6adba0ace3ebb95fa0248aad480c6bc76e74ccd7016662c5d280ae9ef809`
- Report implementation SHA-256: `81a81123e017f4a090c4d60f39653e5ec0c040e60322487c65c0cd4c6d398e22`

The frozen generation controls are temperature `0`, seed `42`, top-p `0.9`, maximum output `500` tokens, and JSON output requested. Every model receives identical system text, evidence, question, response shape and checks.

## Scoring and critical policy

Weights remain: grounded factuality 25, hallucination resistance 20, instruction following 15, structured-output compliance 10, explanation quality 10, uncertainty/reliability handling 10, latency/resource efficiency 5, multilingual capability 5. Multilingual is NOT EVALUATED and receives no points; comparable totals use the evaluated 95-point denominator. Automatic category/check results remain visible and are not replaced by one score.

All CRITICAL cases receive human review. Automatic critical-check failures are flagged, not silently converted into a semantic verdict. A model cannot be recommended if human review confirms a severe unsupported factual claim in a critical case that the existing validator would allow through. Other automatic failures inform comparison but do not automatically disqualify a model. Human review, acceptable grounding/uncertainty/JSON behavior and practical local latency are required for final selection.

## Execution and analysis plan

For each candidate: record one non-scored warmup using the same fixed grounded case, then execute all 65 cases once. Preserve first responses, errors, parse failures, durations and token statistics. Do not replace individual failures. Aggregate total/category checks, explicit check types, critical-case results and runtime distributions. Generate blinded material with fixed seed `26103`: all 35 critical cases for four candidates (140 responses), plus a balanced representative sample of two cases from each of GROUNDED_EXPLANATION, OFFICER_USEFULNESS, MISSING_DATA, DATA_QUALITY, REVIEW_RECOMMENDATIONS and RISK_VS_RELIABILITY for each candidate (48 responses). Duplicate case/model pairs already in critical review are excluded from the quality sheet.

Before human scores exist, any ranking is labelled `PROVISIONAL AUTOMATIC LEADER`. The automatic comparison prioritizes: no runtime/parse failure, critical automatic pass performance, overall automatic pass rate, category breadth, then local latency as a practical tie-break—not as universal model speed. Final selection additionally requires completed blinded human review.

## Hardware scope

The measured environment is Windows 11 build 26200, Python 3.11.3, Ollama 0.33.2, Intel Core 5 210H (8 cores/12 logical processors), approximately 31.6 GiB visible RAM, and NVIDIA GeForce RTX 3050 A Laptop GPU with 4094 MiB VRAM, driver 572.40 and CUDA 12.8 reported by `nvidia-smi`. Results characterize this machine only.

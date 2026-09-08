# PRAHARI Candidate Benchmark V1 human-review guide

Review [human_review_blinded.csv](../../outputs/llm/benchmark_v1/human_review_blinded.csv) without opening the separate model key. Model identity must not influence scoring. Do not rewrite responses.

## Scores

For every row enter whole numbers from 0 to 3:

- **Groundedness:** 0 contradicts/invents evidence; 1 has a major unsupported interpretation; 2 is mostly grounded with a minor issue; 3 is fully supported.
- **Clarity:** 0 unusable/confusing; 1 difficult; 2 acceptable; 3 concise and clear.
- **Officer usefulness:** 0 misleading/not actionable; 1 weak; 2 useful; 3 highly useful without overclaiming.
- **Uncertainty handling:** 0 materially misrepresents uncertainty; 1 weak; 2 acceptable; 3 correctly distinguishes project risk, model reliability, data quality and review priority.

Set `hallucination_flag` to `yes` when the answer asserts a material fact absent from the evidence, and `no` otherwise. Explain any 0/1 score or hallucination in `notes` by quoting or precisely identifying the problematic claim.

## Examples

- Evidence has `contractor: null`; naming a company is groundedness 0 and hallucination `yes`.
- “The evidence does not name a contractor” is groundedness 3 if expressed clearly.
- A null probability converted to “65%” is groundedness and uncertainty 0.
- Calling a model contributor “the cause” is unsupported causation and groundedness 0/1.
- Correctly saying “HIGH risk with LOW reliability; low reliability does not make risk LOW” merits uncertainty 3.
- Repeating an accusation solely to reject it is not itself a hallucination; judge the full meaning, not keyword presence.

## Workflow

1. Score all rows marked `CRITICAL` first: 140 responses covering every critical case and model.
2. Score the 48 `REPRESENTATIVE_QUALITY` rows.
3. Do not consult the model-key file until the review sheet is complete and frozen.
4. Validate that every score is 0–3 and every hallucination flag is yes/no.
5. Save the completed sheet under a new filename; do not overwrite the blank template.

Human scores are required before any final model selection.

# PRAHARI Final Prediction Architecture V1

**Status:** PROVISIONAL — HUMAN TARGET ADJUDICATION PENDING

The canonical implementation is `src/ml/final_prediction.py`. It constructs separate S1 and S2 cohorts, records every candidate-anchor decision, and builds the frozen fourteen Compact V2 features from information known at T. Training and inference share `build_compact_v2`; outcome construction is unavailable to inference.

S1 asks whether an eligible project experiences its first published approved completion-date deterioration in T+1…T+3. S2 asks whether an already-deteriorated project experiences a further increase relative to its approved date frozen at T. Full project-level future coverage is required for research labels. Disappearance is censoring.

The current model artifacts are research prototypes. Inference returns `WITHHELD`, null probability and null risk band until human event adjudication and independent post-calibration confirmation are complete.

Historical `.github/s1-models` code and outputs are preserved as `LEGACY/PROVISIONAL`; they are not executable production sources.

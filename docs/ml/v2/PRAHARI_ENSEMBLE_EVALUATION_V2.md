# Ensemble Evaluation V2

Individual temporally validated models are evaluated first. Equal soft voting is the first ensemble because it has no fitted test-informed weights. It may be reported only on the same held-out rows used for every component model.

Weighted voting is conditional: weights must be learned exclusively from temporal out-of-fold predictions and must improve predeclared measures across folds, not merely pooled performance. Stacking is optional research only and requires sufficient temporal out-of-fold event support. S1 and S2 probabilities are never averaged together, and 3-, 6- and 12-month horizons remain separate.

# PRAHARI Prediction Eligibility V1

**Owner:** PRAHARI ML team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** REFERENCE

Prediction is withheld for uncertain identity, completion, target ineligibility, missing required source interval, insufficient history, unavailable required temporal features, unsupported schema, unavailable artifact, pending human target validation or unconfirmed calibration.

Warnings such as partial provenance do not independently block prediction unless the governed policy says the required evidence is absent. Reliability is separate from risk and probability. `WITHHELD` always implies null probability and null risk band.

Current V1 globally withholds operational predictions while S1/S2 human adjudication is pending.

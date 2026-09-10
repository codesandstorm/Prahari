# PRAHARI Officer Decision Layer V1

**Owner:** PRAHARI backend and governance team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** IMPLEMENTATION

The deterministic flow is project evidence → intrinsic Data Trust → prediction eligibility → released prediction → model reliability → administrative review decision → optional alert eligibility. Each result remains separate. A prediction is not a review recommendation; a recommendation is not an alert; an alert is not proof of deterioration or responsibility.

Current operational predictions are withheld. V1 can therefore route actionable evidence defects to `DATA_VERIFICATION_REQUIRED`, show scientifically ready data as `PREDICTION_WITHHELD`, and exclude completed projects. It creates no alerts and assigns no administrative priority rank.

The LLM receives the decision as immutable server-side evidence. It may explain the decision but cannot change state, priority, eligibility or alert status.

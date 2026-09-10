# PRAHARI Data Trust Frontend Contract

**Owner:** PRAHARI backend and frontend team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** REFERENCE

The frontend receives categorical fields and reason codes. Safe labels include “Verified identity”, “Source-backed observation”, “History insufficient”, “Source gap”, “Data incomplete” and “Prediction withheld”.

It must not display “trusted 97%”, “safe project”, “bad data” or transform reliability into model confidence. It must not infer project risk from Data Trust.

Suggested representation: identity, source, history, latest month, source-gap count, feature status, prediction status, reliability and expandable reasons. The frontend performs no trust calculation.

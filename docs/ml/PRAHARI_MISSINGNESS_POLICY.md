# PRAHARI Missingness Policy

Missingness has three distinct meanings: a field absent from the historical schema, a field present but unreported, and a source/project observation unavailable. They must never be collapsed.

| Type | Treatment |
|---|---|
| field not in schema | structural-unavailability flag; exclude unsupported feature or abstain |
| field present but value missing | native missing handling or training-fold median plus indicator |
| categorical unknown | explicit `UNKNOWN`; no guessed category |
| unavailable calendar source | censor outcome windows |
| project disappears | unknown lifecycle; censor outcome |
| critical feature absent at serving | prediction withheld if model support is inadequate |

Forbidden treatments: global mean/median, backward fill, interpolation, using future observations, treating absence as zero, or treating low data quality as low project risk.

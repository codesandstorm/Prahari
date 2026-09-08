# PRAHARI Feature Defense V2

| Feature | Formula / meaning | Why retained | Does not prove | History | Missingness | Stability / contribution | Officer evidence |
|---|---|---|---|---|---|---|---|
| log original cost | `log1p(original_cost)` | stable scale context | costly projects cause delay | one | fold median | compact context | cost band |
| planned duration | approval to original completion | approved delivery envelope | plan was realistic | one | fold median | baseline context | planned duration |
| project age | approval to t | maturity context | actual work began at approval | one | fold median | baseline context | age as of t |
| expenditure/cost | cumulative expenditure / original cost | current financial deployment | efficiency or misconduct | one | fold median | baseline context | spend position |
| physical progress | reported percentage at t | current delivery state | independently verified completion | one | structural flag | schema-dependent | progress trajectory |
| physical-progress missing | explicit availability | protects reliability | project failure | one | explicit | stable quality signal | data-quality badge |
| history span | first observation through t | distinguishes evidence depth | project age | two | explicit | largest full-model remove-family contribution | history available |
| remaining schedule | months from t to approved date; floor zero | deadline proximity | achievable schedule | one | fold median | top permutation contributor | time remaining |
| required future velocity | remaining work / positive remaining months | direct feasibility requirement | future progress | current | undefined if past deadline | strong contributor | required monthly pace |
| progress-vs-elapsed gap | progress minus elapsed-plan percentage | interpretable plan alignment | causal delay | one | fold median | strong contributor | behind/ahead of plan proxy |
| low progress near deadline | progress <80% and ≤6 months remain | simple fragile-state flag | certain deterioration | one | explicit unknown | moderate contributor | review flag |
| consecutive stagnation | trailing non-positive observed increments | persistent loss of momentum | reason for stagnation | two | unknown if progress absent | modest contributor | stagnant observations |
| cumulative cost revision % | current reported cost state vs original | possible coupled project stress | cost causes schedule change | one | fold median | conditional modest signal | revision history |
| expenditure velocity | calendar-adjusted recent expenditure change | recent financial movement | productive work or corruption | two | fold median | small contribution | expenditure trend |

All formulas use observations through t. Gap-aware velocities divide by actual elapsed calendar months. Required velocity is missing—not infinite—when time remaining is zero/negative. Physical progress of 100 yields zero required velocity when future time remains.

Judge-safe wording: “The project would need approximately X percentage points of reported progress per remaining month, compared with its recent reported pace.” Never say a feature caused deterioration.

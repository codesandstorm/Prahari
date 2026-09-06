# Ranked New CUF Field Recommendations

| Priority | Proposed field | Definition / type | Frequency / reporter | Failure made visible earlier | Target | Guardrail | Missingness | Burden |
|---|---|---|---|---|---|---|---|---|
| P0 | milestone planned/revised/actual dates | six dated milestone families with status | monthly; implementing agency/package owner | slippage before headline schedule revision | S1/S2 | use only values known at t | explicit not-applicable/unknown | medium initial; low update |
| P0 | `land_required`, `land_acquired`, `land_available_for_work` | area plus verified percentage | monthly; implementing agency | work-front constraint | S1/S2 | preserve unit and verification date | unknown separate from zero | medium |
| P0 | clearance register | type required/status/application/decision/last-update dates | monthly/event; responsible authority | approval ageing and blocked dependency | S1/S2 | no inferred approval | explicit not-required | medium |
| P0 | contractor/package identity and operational status | stable IDs; active/stopped/replaced/terminated | event plus monthly confirmation; project owner | contractor exit and work stoppage | S1/S2/C2 | never derive from agency label | unresolved identity category | medium |
| P0 | issue register | category/opened/closed/status/responsible entity/escalation | event/monthly; project owner | persistent bottleneck duration | all | issue entered after event cannot alter earlier prediction | no-issue distinct from unreported | medium |
| P1 | approved/forecast schedule buffer | baseline/revised/forecast dates with approval and first-known timestamps | monthly | erosion before formal revision | S1/S2 | distinguish approved from forecast | unknown allowed | low |
| P1 | project-level fund schedule and release | planned release/actual release/value/utilisation | monthly; finance/project unit | funding interruption | all | project ID and first-known timestamp mandatory | not reported ≠ zero | medium/high |
| P1 | manpower planned/deployed | monthly average by package | monthly; contractor validated by owner | mobilization decline | S1/S2 | comparable definition | explicit unavailable | medium |
| P1 | material/equipment constraint | category/status/start/end/severity | event/monthly | supply or equipment bottleneck | S1/S2/C2 | factual status—not speculative cause | explicit none/unknown | low |
| P2 | scope/design revision event | approval date, authority, cost/time effect | event | deterioration due to sanctioned scope change | all | outcome-window value excluded from pre-event prediction | explicit none | low |

False negatives caused by sudden unobserved change motivate contractor status, issue, milestone, land, clearance, funding, and resources. False positives motivate intervention/action logs, approved recovery plans, reporting-correction flags, and reason-coded revisions so successful mitigation is distinguishable from model error.

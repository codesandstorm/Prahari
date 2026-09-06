# PRAHARI Feature Defense Table

| Feature | Meaning | Predictive rationale | Known at t? | Leakage/bias risk | Judge-safe explanation | Dashboard |
|---|---|---|---|---|---|---|
| original cost | project scale | scale may affect delivery complexity | yes | sector confounding | contributor, not cause | cost band |
| planned duration | approved time allowance | short/tight plans may have less buffer | yes | approval-date quality | planned baseline | timeline |
| project age | elapsed time since approval | risk mechanism changes with maturity | yes | left censoring | observation context | age |
| expenditure/cost | financial deployment | financial and physical delivery may diverge | yes | accounting/reporting differences | supporting signal | paired trajectory |
| physical progress | reported completion | low progress near deadline may precede revision | yes | absent in OCMS; self-reporting | current reported state | progress |
| progress change | recent delivery movement | persistent slowing may provide warning | yes | needs contiguous history | recent trend, not cause | sparkline |
| expenditure change | recent spending movement | stalled deployment may precede delivery problems | yes | corrections possible | recent reported movement | sparkline |
| stagnation | no positive recent movement | transparent early-warning rule | yes | missing progress | review trigger | badge |
| history depth | evidence available | shallow history lowers reliability | yes | newer projects | reliability reason | reliability panel |
| correction count | prior retrospective changes | unstable reporting reduces confidence | yes | data quality ≠ risk | data-quality signal | quality badge |

Agency is withheld: its semantics are not normalized and it does not reliably identify contractors. Anticipated completion is promising but conditional because it is unavailable in the frozen modern extraction and its approval semantics require validation. Peer features are withheld until authoritative ministry/sector keys and fold-safe computation exist.

No listed feature proves causality. Explanations must say “model contributor,” “supporting signal,” or “reported trajectory.”

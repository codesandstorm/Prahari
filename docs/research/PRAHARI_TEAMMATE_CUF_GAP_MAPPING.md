# PRAHARI teammate-feature CUF gap mapping

This mapping does not claim that private PAIMANA fields exist. It states the evidence that would be required for future implementation.

| Idea | Missing source information | Required future CUF information |
|---|---|---|
| Contractor peer trend | Authoritative contractor/package identity and validity dates | `contractor_id`, `package_id`, contractor role, effective-from/to |
| Agency peer trend | Normalized implementing-agency identity and role history | `implementing_agency_id`, role, effective-from/to, change reason |
| True fund-to-progress lag | Monthly sanction/release/receipt dates and amounts | project-level fund-release transaction history, release type, amount, date |
| Outcome archetypes | Clean completed and terminated trajectories | completion/closure event, actual completion date, closure outcome and reason |
| External-event response | Geocoded, dated, authoritative event observations | project coordinates plus linked authoritative event identifier (external source) |

Raw `agency` must not be relabelled as contractor. Cumulative expenditure must not be relabelled as funding. These are semantic blockers, not ordinary missing values.

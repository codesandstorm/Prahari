# CUF / PAIMANA Field Blueprint

**Status:** SUPERSEDED

**Superseded by:** [`../cuf/PRAHARI_CUF_FIELD_CONTRACT_V1.md`](../cuf/PRAHARI_CUF_FIELD_CONTRACT_V1.md)

This file preserves the pre-retrieval research state. The official 17-page CUF document was subsequently obtained and verified; do not use the older `INFERRED_BUT_NOT_VERIFIED` classifications below as the current contract.

**Research date:** 2026-09-06

**Evidence rule:** only MoSPI/IPMD material is authoritative for existing PAIMANA/CUF claims.

## Source status

- [Official PAIMANA public dashboard](https://ipm.mospi.gov.in/Home/PublicDashboard): accessible public evidence.
- [Official New OCMS description](https://ipm.mospi.gov.in/AboutUs/AboutOCMS): official description; detailed private CUF schema is not exposed by the page retrieval.
- [Official IPMD description](https://mospi.gov.in/programme-implementation-pi-wing): confirms IPMD monitors central-sector projects costing ₹150 crore and above and facilitates constraint resolution.
- [Concept Note F.No. 12011/08/2023-IPMD, 4 September 2024](https://www.ipm.mospi.gov.in/Content/PDF/Concept%20note%20to%20Line%20Ministries%20dated%204%20Sept%202024.pdf): identified official source, but the server presented an expired/invalid certificate during this audit. Its annexures were not safely retrievable. No field is labelled verified from this document without page evidence.

## Field-level blueprint

| Field family / official public name | Evidence status | Definition/evidence | Type/unit | State/event | Level | Current Flash | Processed | Model role | Leakage |
|---|---|---|---|---|---|---|---|---|---|
| ProjectID | VERIFIED_PAIMANA_PUBLIC_FIELD | public project identifier | string | state | project | yes | yes | join only | low |
| Project Name | VERIFIED_PAIMANA_PUBLIC_FIELD | public project name | string | state | project | yes | yes | display/context | medium bias |
| Line Ministry | VERIFIED_PAIMANA_PUBLIC_FIELD | administrative ministry | category | state | project/portfolio | partial | historically partial | subgroup after validation | high bias |
| Sector | VERIFIED_PAIMANA_PUBLIC_FIELD | infrastructure sector | category | state | project/portfolio | partial | historically partial | subgroup after validation | high bias |
| Original Cost | VERIFIED_PAIMANA_PUBLIC_FIELD | cost approved by sanction authority at approval | ₹ crore | state | project | yes | yes | Model A | conditional |
| Latest Revised Cost | VERIFIED_PAIMANA_PUBLIC_FIELD | latest reported revised cost | ₹ crore | state/change | project | yes | yes | cohort/target state | high |
| Expenditure (Cumm.) | VERIFIED_PAIMANA_PUBLIC_FIELD | expenditure since project sanction | ₹ crore | state | project | yes | yes | Model A/B | conditional |
| Start Date | VERIFIED_PAIMANA_PUBLIC_FIELD | displayed project start date | date | state | project | partial | partial | candidate | medium |
| Latest Revised Completion Date | VERIFIED_PAIMANA_PUBLIC_FIELD | latest reported revised completion | date | state/change | project | yes | yes | schedule cohort/target | high |
| Completed Date | VERIFIED_PAIMANA_PUBLIC_FIELD | public completion date | date | event | project | lifecycle table | no | outcome only | leakage |
| Physical Progress | VERIFIED_PAIMANA_PUBLIC_FIELD | reported completion percentage | percent | state | project | modern reports | partial | Model A/B | conditional |
| Agency | CURRENT_FLASH_REPORT_FIELD | report’s agency label; role is inconsistent | string | state/change | project | yes | yes | withheld pending hierarchy | unknown |
| Approval Date | CURRENT_FLASH_REPORT_FIELD | reported approval date | date | state | project | yes | yes | derived age/duration | low |
| Original completion date | CURRENT_FLASH_REPORT_FIELD | originally approved completion date | date | state | project | yes | yes | baseline/target contract | conditional |
| Anticipated completion/cost | CURRENT_FLASH_REPORT_FIELD | operational forecast in historical tables | date/₹ crore | state | project | historical only | partial | conditional leading signal | high |
| planning/land/clearance/tender/commissioning milestones | INFERRED_BUT_NOT_VERIFIED | named in supplied research scope; annexure page evidence unavailable | structured dates/status/cost | state+event | project/package | no | no | Model C contract | conditional |
| issues/bottlenecks | INFERRED_BUT_NOT_VERIFIED | detailed CUF fields not publicly verified | category/dates/status | state+event | project/package | no | no | Model C contract | conditional |
| contractor/package records | UNKNOWN | cannot be inferred from current agency | IDs/names/dates/value | state+event | package | no | no | Model C contract | conditional |

`mandatory_optional_unknown`, update frequency, package granularity, and annexure/page remain `UNKNOWN` for all concept-note-only candidates until a valid official copy is reviewed. The registry never invents private PAIMANA fields.

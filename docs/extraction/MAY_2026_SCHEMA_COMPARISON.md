# May 2026 versus frozen June 2026 Table 6

This comparison is based on the canonical manifest-backed sources
`SRC-2026-05` and `SRC-2026-06`. It does not generalize beyond these reports.

| Item | Result | May 2026 evidence |
|---|---|---|
| Schema family | SAME | PAIMANA_V2, HIGH; actual Table 6 headers contain both Legacy OCMS Code and PMGID. |
| Table number | SAME | Table 6. |
| Table title | SAME | All Ongoing Projects. |
| Number of columns | SAME | Eight columns on all 2,175 May table rows. |
| Compound identity cell | SAME | Project name, agency, Project Code, then Legacy OCMS Code and PMGID. |
| Project Code position | SAME | Penultimate identity line, parenthesized. |
| Legacy OCMS Code position | SAME | First value on final identity line. |
| PMGID position | SAME | Second value on final identity line. |
| State column | SAME | Third table column; 242 May values wrap within the cell. |
| Approval/start cell | SAME | Two source lines; second is parenthesized. |
| Target/revised DoC cell | COMPATIBLE_VARIATION | 1,976 rows use two lines. Serial numbers 446–451, 464, 467, and 470–472 contain only `(-)`, meaning the unparenthesized target value is absent and the parenthesized revised value is the source dash. |
| Original/revised cost cell | SAME | Two source lines; second is parenthesized. |
| Expenditure column | SAME | One raw value in column seven. |
| Physical progress column | SAME | One raw value in column eight. |
| Repeated headers | SAME | One per data page: 109. |
| Section headings and totals | SAME | 48 section headings and 31 totals. |
| Printed/physical offset | SAME | Printed page is physical page minus one. |
| Missing markers | COMPATIBLE_VARIATION | Dash convention is unchanged, but May identity columns are partly populated: Legacy OCMS Code has 817 dashes; PMGID has 786. |
| Table boundaries | DIFFERENT | May title is physical 53; data are 54–162. June title is 58; data are 59–159. |
| Report-level count | DIFFERENT | May reports 1,987 ongoing projects on physical page 4 (printed page 3); June reports 1,847. |

## Compatibility decision

Overall result: **COMPATIBLE_VARIATION**.

The frozen June parser is not changed or made more permissive. May uses a
month-specific adapter which reuses only the verified eight-column structural
classification and applies an explicit May-only rule for the 11 single-line
DoC cells.

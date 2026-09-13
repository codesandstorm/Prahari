# PRAHARI CUF Availability Matrix

The complete record-level matrix is generated at `outputs/cuf/cuf_field_availability.csv`. Coverage is measured against 48,326 historical project-month rows; it does not imply semantic fitness.

| Family | Current historical evidence | Current Watch use | Future structured use |
|---|---|---|---|
| Project profile | name and agency broadly available; sector/state partial; ministry absent in the project-month file | context only | typed project/profile context |
| Approved dates | approval 98.76%; original completion 99.52%; revised completion 70.22% | calendar-safe schedule pressure | yes |
| Cost/expenditure | original cost and cumulative expenditure 100%; revised cost 77.19% | existing contextual facts only | yes |
| Physical progress | 68.93% of rows, 22/30 observed months | stagnation and existing required-velocity signals | planned-vs-actual gap when scheduled plan arrives |
| Financial plan | historical cumulative expenditure only | plan gap and divergence unavailable | compatible scheduled/actual progress required |
| Milestones | `milestones_raw` text in 29.77% of rows but not a typed milestone table | structurally unavailable | full Annexure III schema supported by input contract |
| Land | absent | structurally unavailable | supported |
| ROW | absent | structurally unavailable | supported |
| Clearances | absent | structurally unavailable | supported |
| Tender | absent | structurally unavailable | supported |
| Funding | absent | contextual calculations unavailable | supported, not a Watch trigger |
| Reporting/provenance | source IDs, hashes, coverage and row locators available with governed missingness | available | supported |

`AVAILABLE`, `UNREPORTED`, `STRUCTURALLY_UNAVAILABLE`, `NOT_APPLICABLE`, `SOURCE_GAP`, and `UNKNOWN` are distinct. No unavailable cell becomes zero, false, clear, safe, or low.

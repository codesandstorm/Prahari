# External Data Candidates

No external series is included in the current experiment.

| Candidate | Authoritative source | Frequency/history | Timestamp rule | Relevance | Decision |
|---|---|---|---|---|---|
| CPI components | [MoSPI CPI warehouse](https://cpi.mospi.gov.in/) | monthly; revised series from 2013 | available only after official release date | broad inflation; weak project specificity | research only; likely too general alone |
| rainfall | [India Meteorological Department](https://mausam.imd.gov.in/responsive/rainfallinformation.php) | daily/weekly/monthly; historical grids available | observation publication/availability time | strong only with defensible project geography | Model C candidate |
| verified disaster alerts | [NDMA SACHET](https://sachet.ndma.gov.in/) | event-based and geo-targeted | alert first-known timestamp | post-event reassessment | high-value event input |
| WPI steel/cement/fuel | Office of Economic Adviser official WPI releases | monthly | publication date, not reference month alone | sector-dependent input-cost pressure | verify series stability before use |
| exchange rates | RBI reference-rate history | business day | RBI publication timestamp | relevant only to projects with documented import exposure | reject unless exposure field exists |

Every external event requires `event_id`, `event_type`, `event_start`, `first_known_timestamp`, `event_end`, `location`, affected-project linkage, source, and verification status. A shock can update risk only after it became known. Macro series must be joined by release vintage and assessed for spurious correlation.

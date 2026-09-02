# Gate 2 CI reproducibility

Raw government PDFs are intentionally excluded from Git. Tests that open or
hash those real files are marked `integration` and run only in environments
where the official sources are available. Normal CI runs the remaining tests,
including provenance validation against deterministic manifest data.

The validated April, May, and June extraction CSVs and their frozen two- and
three-month processed CSVs are byte-addressed evidence artifacts. Their bytes
deliberately contain CSV record
terminators that differ from some embedded multiline field newlines. Scoped
`.gitattributes` rules therefore mark only these seven frozen files as `binary`
(`-text`, `-diff`, `-merge`), so Git does not rewrite their bytes between
Windows and Linux checkouts or invite unsafe line-oriented merging. Python,
Markdown, configuration, and other repository text retain normal Git text
handling.

For frozen CSVs, the recorded SHA-256 means the exact committed byte
stream. Raw PDFs also use exact byte-level SHA-256. Logical row comparison is
an additional validation and does not replace either byte contract.

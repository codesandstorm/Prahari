import json
with open('outputs/reports/batch_inspection.json', encoding='utf-8') as f:
    data = json.load(f)

# Print full details
for r in data['inspections']:
    print(f"FILE: {r['filename']}")
    print(f"  sha256:   {r['sha256']}")
    print(f"  pages:    {r['page_count']}")
    print(f"  size:     {r['file_size_bytes']}")
    print(f"  text_ok:  {r['text_extractable']}")
    print(f"  schema:   {r['schema_version']}  conf={r['schema_confidence']}")
    print(f"  keywords: {r['schema_evidence_keywords']}")
    print(f"  ev_pages: {r['schema_evidence_pages']}")
    print(f"  errors:   {r['errors']}")
    print(f"  notes:    {r['notes']}")
    print()

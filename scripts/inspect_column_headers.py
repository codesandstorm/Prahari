"""Get exact column headers from the first data page of the All Ongoing Projects table in 2026 and 2025 files."""
import pdfplumber, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

files = [
    "data/raw/2026/FlashReport_2026_07.pdf",
    "data/raw/2026/FlashReport_2026_05.pdf",
    "data/raw/2025/FlashReport_July_2025 (1).pdf",
    "data/raw/2025/FlashReport_2025_05.pdf",
    "data/raw/2025/FlashReport_2025_06.pdf",
]

KEYWORDS = ["All Ongoing Projects", "Project Code", "Legacy OCMS", "PMGID", "Agency",
            "Physical Progress", "Project Name", "Revised Cost", "Cumulative"]

for fpath in files:
    p = pathlib.Path(fpath)
    print(f"\n{'='*70}")
    print(f"FILE: {p.name}  ({p.stat().st_size//1024} KB)")
    with pdfplumber.open(str(p)) as pdf:
        found_table = False
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text() or ""
            # Find a page with "All Ongoing Projects" AND actual column headers
            if ("All Ongoing Projects" in txt or "Ongoing Projects" in txt) and "Project Name" in txt:
                print(f"\n  First table data page: {i+1}")
                print(txt[:1200])
                found_table = True
                break
        if not found_table:
            print("  No table page with column headers found in text extraction.")

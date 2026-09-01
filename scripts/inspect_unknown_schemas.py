"""Detailed page-by-page text inspection of 2026 and July 2025 files to understand why they are UNKNOWN schema."""
import pdfplumber, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

files = [
    "data/raw/2026/FlashReport_2026_07.pdf",
    "data/raw/2026/FlashReport_2026_05.pdf",
    "data/raw/2025/FlashReport_July_2025 (1).pdf",
]

KEYWORDS = ["Project Code", "Legacy OCMS Code", "PMGID", "OCMS", "DOA", "DOC",
            "Project Name", "Agency", "Physical Progress", "Cumulative Expenditure",
            "All Ongoing Projects", "Ongoing Projects", "Completed Projects"]

for fpath in files:
    p = pathlib.Path(fpath)
    print(f"\n{'='*70}")
    print(f"FILE: {p.name}  ({p.stat().st_size//1024} KB)")
    print(f"{'='*70}")
    with pdfplumber.open(str(p)) as pdf:
        for i, page in enumerate(pdf.pages[:5]):
            txt = page.extract_text() or ""
            print(f"\n--- PAGE {i+1} (chars={len(txt)}) ---")
            print(txt[:800])
            # Check for keywords
            found = [kw for kw in KEYWORDS if kw in txt]
            if found:
                print(f"  [KEYWORDS FOUND]: {found}")

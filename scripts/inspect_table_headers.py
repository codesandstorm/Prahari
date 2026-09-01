"""Check pages 58-60 of 2026_07 and 2026_06 for exact column headers."""
import pdfplumber, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

files_and_pages = [
    ("data/raw/2026/FlashReport_2026_07.pdf", range(57, 62)),
    ("data/raw/2026/FlashReport_2026_05.pdf", range(52, 62)),
    ("data/raw/2025/FlashReport_July_2025 (1).pdf", range(30, 68)),
]

for fpath, page_range in files_and_pages:
    p = pathlib.Path(fpath)
    print(f"\n{'='*70}")
    print(f"FILE: {p.name}")
    with pdfplumber.open(str(p)) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        for pnum in page_range:
            if pnum >= total_pages:
                break
            page = pdf.pages[pnum]
            txt = page.extract_text() or ""
            if any(kw in txt for kw in ["All Ongoing Projects", "Project Code", "Legacy OCMS", "PMGID", "Agency"]):
                print(f"\n--- PAGE {pnum+1} ---")
                print(txt[:600])
                break  # Just need first match

"""Convert PDFs in screenshots/ to PNGs in docs/screenshots/ for GitHub README."""
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "screenshots"
OUT = ROOT / "docs" / "screenshots"

# PDF prefix -> PNG output (matches files like 1-overview.pdf, 2-home-page.pdf)
MAPPING = [
    ("1", "overview.png"),
    ("2", "home.png"),
    ("3", "analytics.png"),
    ("4", "export.png"),
]


def _find_pdf(prefix):
    matches = sorted(SRC.glob(f"{prefix}*.pdf"))
    return matches[0] if matches else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for prefix, png_name in MAPPING:
        pdf = _find_pdf(prefix)
        if not pdf:
            print(f"SKIP  no PDF starting with '{prefix}' in screenshots/")
            continue
        doc = fitz.open(pdf)
        page = doc.load_page(0)
        page.get_pixmap(matrix=fitz.Matrix(2, 2)).save(OUT / png_name)
        doc.close()
        print(f"OK    {pdf.name} -> docs/screenshots/{png_name}")

    keep = {m[1] for m in MAPPING}
    for stale in OUT.glob("*.png"):
        if stale.name not in keep:
            stale.unlink()
            print(f"DEL   removed stale {stale.name}")


if __name__ == "__main__":
    main()

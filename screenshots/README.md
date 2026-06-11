# Screenshots folder

Add Streamlit UI screenshots here as **PDF** or **PNG** files.

## Recommended naming

| File | Content |
|------|---------|
| `1-overview.pdf` | Full app overview |
| `2-home-page.pdf` | Upload & screen page |
| `3-screening-results.pdf` | Analytics / ranked results |

Files must start with `1`, `2`, or `3` so the update script can find them.

## Update GitHub README images

After adding or replacing files:

```bash
pip install pymupdf
python scripts/update_screenshots.py
```

This converts PDFs to PNG in `docs/screenshots/` for the README.

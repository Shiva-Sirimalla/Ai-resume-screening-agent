"""Capture Streamlit UI screenshots for GitHub README. Run while app is on localhost:8501."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

URL = "http://localhost:8501"
SHOTS = [
    ("home.png", "Upload & Screen tab"),
    ("analytics.png", "Analytics tab"),
    ("export.png", "Export tab"),
]


def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(URL, wait_until="networkidle", timeout=120_000)
        time.sleep(4)

        tabs = page.locator('[data-baseweb="tab"]')
        labels = ["Upload & Screen", "Analytics", "Export"]
        files = ["home.png", "analytics.png", "export.png"]

        for i, (fname, _) in enumerate(zip(files, labels)):
            if i < tabs.count():
                tabs.nth(i).click()
                time.sleep(2)
            page.screenshot(path=str(OUT / fname), full_page=True)
            print(f"Saved docs/screenshots/{fname}")

        browser.close()
    print("Done.")


if __name__ == "__main__":
    capture()

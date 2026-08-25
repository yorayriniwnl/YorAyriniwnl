#!/usr/bin/env python3
"""
One-off helper — NOT part of the automated build. Run this locally, by
hand, only when you change the text of a tagline line in CONFIG["tagline"]
in generate_assets.py.

It renders each line with the real embedded DM Mono font in an actual
browser and prints its exact pixel width, so the typewriter clip-paths in
build_tagline_svg() line up with the real glyphs instead of an estimated
monospace-advance guess. Paste the printed widths back into CONFIG.

Needs playwright (`pip install playwright && playwright install chromium`)
— deliberately not a dependency of build-assets.yml, since the automated
build never needs to re-measure anything, only re-render with numbers
that are already known.
"""
import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))

LINES = [
    "Building the software layer for the physical world.",
    "Geospatial \u00b7 Realtime \u00b7 Computer Vision \u00b7 Systems Engineering",
    "Rust for the systems layer, GenAI + AWS for the applied one.",
    "The domain changes; the standard doesn't.",
]


def main():
    from playwright.sync_api import sync_playwright

    with open(os.path.join(HERE, "fonts", "dm-mono-500.woff2"), "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    body = "".join(
        f'<text id="t{i}" font-family="DM Mono" font-weight="500" '
        f'font-size="14" letter-spacing="0.5">'
        f'{s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</text>'
        for i, s in enumerate(LINES)
    )
    html = (
        "<html><head><style>@font-face{font-family:'DM Mono';font-weight:500;"
        f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}</style></head>"
        f"<body><svg xmlns='http://www.w3.org/2000/svg'>{body}</svg></body></html>"
    )
    tmp = os.path.join(HERE, "..", "_measure_tmp.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{os.path.abspath(tmp)}")
        page.wait_for_timeout(200)
        for i, line in enumerate(LINES):
            w = page.evaluate(f'document.getElementById("t{i}").getComputedTextLength()')
            print(f'("{line}", {w}),')
        browser.close()
    os.remove(tmp)


if __name__ == "__main__":
    main()

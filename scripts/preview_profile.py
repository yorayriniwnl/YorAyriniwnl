"""Local-only GitHub-width preview and inline SVG geometry inspection.

--refresh-markup asks GitHub's Markdown API to sanitize the public README. The
render is cached in ignored tmp/, never published. The final verification must
also inspect the real profile because GitHub owns its surrounding layout.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tmp/gallery-markup.json"
STYLE = """
*{box-sizing:border-box}html{color-scheme:dark;scroll-behavior:auto}
body{margin:0;background:#0d1117;color:#f0f6fc;font:14px/1.5 Arial,sans-serif}
main{width:calc(100% - 32px);max-width:900px;margin:24px auto;padding:32px;border:1px solid #30363d;border-radius:6px}
.markdown-body{overflow-wrap:break-word}img{max-width:100%;height:auto;vertical-align:baseline}
p{margin:0 0 16px}details{margin:0 0 16px}summary{cursor:pointer}summary img{vertical-align:middle}
a:focus-visible,summary:focus-visible{outline:3px solid #ff9d91;outline-offset:3px}
body.light{background:#fff;color:#1f2328;color-scheme:light}body.light main{border-color:#d1d9e0}
.inspection{width:100%;max-width:100%;padding:0;border:0;margin:0}
.inspection section{padding:20px 0;border-bottom:1px solid #333}.inspection svg{display:block;max-width:100%;height:auto}
.inspection h2{font:16px Arial,sans-serif;color:#ccc;margin:8px}
"""


def refresh_markup():
    source = (ROOT / "README.md").read_text(encoding="utf-8")
    request = urllib.request.Request(
        "https://api.github.com/markdown",
        data=json.dumps({"text": source, "mode": "gfm", "context": "yorayriniwnl/Yorayriniwnl"}).encode(),
        headers={"User-Agent": "AYR-profile-preview", "Content-Type": "application/json", "Accept": "text/html"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        rendered = response.read().decode("utf-8")
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps({"sha256": hashlib.sha256(source.encode()).hexdigest(), "html": rendered}), encoding="utf-8")
    print("Cached GitHub-sanitized Markdown", flush=True)


def markup():
    source = (ROOT / "README.md").read_text(encoding="utf-8")
    rendered = source
    if CACHE.is_file():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
        if cache["sha256"] == hashlib.sha256(source.encode()).hexdigest():
            rendered = cache["html"]
    return re.sub(r"https://raw\.githubusercontent\.com/[^/]+/[^/]+/output/", "/generated/", rendered)


def inspect_assets(query):
    variant = query.get("layout", ["mobile"])[0]
    stems = query.get("asset", [])
    result = []
    for path in sorted((ROOT / "generated").glob("gallery-*.svg")):
        if variant == "mobile" and "-mobile-" not in path.name:
            continue
        if variant == "desktop" and "-mobile-" in path.name:
            continue
        if stems and not any(stem in path.name for stem in stems):
            continue
        svg = path.read_text(encoding="utf-8")
        prefix = path.stem + "-"
        ids = re.findall(r'\bid="([^"]+)"', svg)
        for identifier in ids:
            svg = svg.replace(f'id="{identifier}"', f'id="{prefix}{identifier}"')
            svg = svg.replace(f"url(#{identifier})", f"url(#{prefix}{identifier})")
        svg = svg.replace('aria-labelledby="title description"', f'aria-labelledby="{prefix}title {prefix}description"')
        result.append(f'<section data-asset="{html.escape(path.name)}"><h2>{html.escape(path.name)}</h2>{svg}</section>')
    return "".join(result)


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path in {"/", "/inspect"}:
            inspect = url.path == "/inspect"
            content = inspect_assets(query) if inspect else markup()
            theme = "light" if query.get("theme") == ["light"] else "dark"
            body = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                    f'<title>Ayush Roy / Proof Gallery preview</title><style>{STYLE}</style></head>'
                    f'<body class="{theme}"><main class="{"inspection" if inspect else "profile-shell"}"><article class="markdown-body">{content}</article></main></body></html>').encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-markup", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.refresh_markup:
        refresh_markup()
    print(f"Profile preview: http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(ROOT))).serve_forever()


if __name__ == "__main__":
    main()

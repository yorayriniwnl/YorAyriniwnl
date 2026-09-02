#!/usr/bin/env python3
"""
Fetches live GitHub data for CONFIG["username"] and renders 3 stat cards
in the same visual language as hero.svg. Meant to run inside GitHub
Actions (.github/workflows/build-stats.yml) on a daily cron:

  - GITHUB_TOKEN (automatic, no setup needed) covers the REST calls —
    profile, repo list, per-repo languages. All public data; the token
    only raises the rate limit from 60/hr to 5000/hr, no special scope
    required.
  - STATS_TOKEN (a classic Personal Access Token with the `read:user`
    scope, added as a repo secret) enables the GraphQL contribution
    calendar. Without it, the middle card becomes a deliberate system
    status panel, so the public profile never exposes setup instructions.

Local usage:
    python3 scripts/generate_stats.py --sample     # design iteration,
                                                     # no network calls
    GITHUB_TOKEN=... STATS_TOKEN=... python3 scripts/generate_stats.py
                                                     # real run

The renderer has deterministic sample coverage, while live runs print the
exact data fetched before writing the SVG so refresh failures stay visible
in Actions logs.
"""
import argparse
import base64
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_data import load_design_tokens, load_profile


HERE = str(SCRIPT_DIR)
OUT_DIR = str(SCRIPT_DIR.parent / "generated")
PROFILE = load_profile()
PALETTE = PROFILE["visual_contract"]["palette"]
TOKENS = load_design_tokens()

USERNAME = PROFILE["identity"]["handle"]
API = "https://api.github.com"
GQL = "https://api.github.com/graphql"

# Same canonical palette as the README asset generator.
PRIMARY = PALETTE["crimson"]
SECONDARY = TOKENS["color"]["secondaryCrimson"]
SPARKLE = PALETTE["signal"]
MUTED = PALETTE["muted"]
VOID = PALETTE["void"]
PANEL = PALETTE["panel"]
BORDER = PALETTE["deep_crimson"]

LANG_COLORS = [PRIMARY, SECONDARY, SPARKLE, SECONDARY, MUTED, BORDER]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def b64_font(filename):
    with open(os.path.join(HERE, "fonts", filename), "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def gh_rest(path, token):
    req = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-stats-bot",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def gh_graphql(query, variables, token):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GQL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{USERNAME}-stats-bot",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def fetch_overview(token):
    user = gh_rest(f"/users/{USERNAME}", token)
    repos, page = [], 1
    while True:
        batch = gh_rest(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner", token)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    non_fork = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in non_fork)
    print(f"[stats] fetched user + {len(repos)} repos ({len(non_fork)} non-fork), {stars} stars total")
    return {
        "followers": user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "stars": stars,
    }, non_fork


def fetch_languages(non_fork_repos, token):
    totals = {}
    for r in non_fork_repos:
        try:
            langs = gh_rest(f"/repos/{USERNAME}/{r['name']}/languages", token)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"[stats] languages fetch failed for {r['name']}: {e}", file=sys.stderr)
            continue
        for lang, n in langs.items():
            totals[lang] = totals.get(lang, 0) + n
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    print(f"[stats] language totals across {len(non_fork_repos)} repos: {ranked[:8]}")
    return ranked


def language_percentages(ranked_langs):
    """Return display rows whose percentages use the complete language total.

    Only the first six rows are rendered, but languages outside that slice
    must still contribute to the denominator or the chart overstates the
    visible languages.
    """
    total = sum(n for _, n in ranked_langs) or 1
    return [(lang, n, n / total * 100) for lang, n in ranked_langs[:6]]


CONTRIB_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_streak(stats_token):
    if not stats_token:
        print("[stats] STATS_TOKEN not set — skipping streak card")
        return None
    try:
        data = gh_graphql(CONTRIB_QUERY, {"login": USERNAME}, stats_token)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"[stats] contribution fetch failed, skipping streak card: {e}", file=sys.stderr)
        return None
    if "errors" in data:
        print(f"[stats] GraphQL errors, skipping streak card: {data['errors']}", file=sys.stderr)
        return None
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    current = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current += 1
        else:
            break
    longest = running = 0
    for d in days:
        if d["contributionCount"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    sparkline = [d["contributionCount"] for d in days[-84:]]
    print(f"[stats] streak: current={current} longest={longest} total={cal['totalContributions']}")
    return {"current": current, "longest": longest, "total": cal["totalContributions"], "sparkline": sparkline}


# --------------------------------------------------------------- rendering

def font_defs(dmmono_b64, cormorant_b64):
    return f'''<style>
@font-face {{ font-family: 'Cormorant Garamond'; font-weight: 600; src: url(data:font/woff2;base64,{cormorant_b64}) format('woff2'); }}
@font-face {{ font-family: 'DM Mono'; font-weight: 500; src: url(data:font/woff2;base64,{dmmono_b64}) format('woff2'); }}
.stat-num {{ font-family: 'Cormorant Garamond', serif; font-weight: 600; fill: {PRIMARY}; }}
.stat-lbl {{ font-family: 'DM Mono', monospace; font-weight: 500; fill: {MUTED}; letter-spacing: 1.5px; }}
.stat-title {{ font-family: 'DM Mono', monospace; font-weight: 500; fill: {PRIMARY}; letter-spacing: 3px; }}
</style>
<linearGradient id="cardBg" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="{PANEL}"/><stop offset="100%" stop-color="{VOID}"/>
</linearGradient>'''


def card_shell(w, h, title):
    corners = [
        (f"M14,26 L14,14 L26,14", 0.0),
        (f"M{w-26},14 L{w-14},14 L{w-14},26", -2.1),
        (f"M14,{h-26} L14,{h-14} L26,{h-14}", -4.2),
        (f"M{w-26},{h-14} L{w-14},{h-14} L{w-14},{h-26}", -6.3),
    ]
    brackets = "".join(
        f'<path d="{d}" stroke="{PRIMARY}" stroke-width="1" fill="none" opacity="0.5">'
        f'<animate attributeName="opacity" values="0.32;0.6;0.32" dur="8.4s" '
        f'begin="{phase}s" repeatCount="indefinite"/></path>'
        for d, phase in corners
    )
    return f'''<rect width="{w}" height="{h}" rx="6" fill="url(#cardBg)" stroke="{BORDER}" stroke-width="1"/>
{brackets}
<text x="28" y="34" class="stat-title" font-size="12">{esc(title)}</text>'''



def build_overview_panel(overview):
    w, h = 380, 170
    is_sample = overview.get("_sample", False)
    def fmt(v):
        return "\u2014" if is_sample else v
    stats = [
        ("REPOS", overview["public_repos"]),
        ("STARS", overview["stars"]),
        ("FOLLOWERS", overview["followers"]),
    ]
    col_w = (w - 56) / 3
    cells = []
    for i, (label, value) in enumerate(stats):
        cx = 28 + col_w * i + col_w / 2
        cells.append(f'<text x="{cx:.1f}" y="108" text-anchor="middle" class="stat-num" font-size="42">{fmt(value)}</text>')
        cells.append(f'<text x="{cx:.1f}" y="132" text-anchor="middle" class="stat-lbl" font-size="10">{label}</text>')
    return card_shell(w, h, "PROFILE TELEMETRY") + "".join(cells)


def build_streak_panel(streak):
    w, h = 380, 170
    if streak is None:
        shell = card_shell(w, h, "SYSTEM STATUS")
        status = [("IST", "TIMEZONE"), ("TS+PY", "CORE"), ("OPEN", "INTERNSHIPS")]
        col_w = (w - 56) / 3
        cells = []
        for i, (value, label) in enumerate(status):
            cx = 28 + col_w * i + col_w / 2
            cells.append(f'<text x="{cx:.1f}" y="104" text-anchor="middle" class="stat-num" font-size="30">{value}</text>')
            cells.append(f'<text x="{cx:.1f}" y="130" text-anchor="middle" class="stat-lbl" font-size="9">{label}</text>')
        return shell + "".join(cells)

    shell = card_shell(w, h, "CONTRIBUTION STREAK")
    stats = [("CURRENT", streak["current"]), ("LONGEST", streak["longest"]), ("TOTAL (1Y)", streak["total"])]
    col_w = (w - 56) / 3
    cells = []
    for i, (label, value) in enumerate(stats):
        cx = 28 + col_w * i + col_w / 2
        cells.append(f'<text x="{cx:.1f}" y="86" text-anchor="middle" class="stat-num" font-size="36">{value}</text>')
        cells.append(f'<text x="{cx:.1f}" y="108" text-anchor="middle" class="stat-lbl" font-size="9">{label}</text>')

    spark = streak["sparkline"] or [0]
    peak = max(spark) or 1
    bar_w = (w - 56) / len(spark)
    bars = []
    for i, v in enumerate(spark):
        bh = 2 + (v / peak) * 26
        x = 28 + i * bar_w
        y = 148 - bh
        bars.append(f'<rect x="{x:.2f}" y="{y:.1f}" width="{max(bar_w-1,0.6):.2f}" height="{bh:.1f}" fill="{PRIMARY}" opacity="{0.35+0.55*(v/peak):.2f}" rx="0.5"/>')
    label = f'<text x="28" y="162" class="stat-lbl" font-size="8" opacity="0.55">LAST 12 WEEKS</text>'
    return shell + "".join(cells) + "".join(bars) + label


def build_languages_panel(ranked_langs):
    w, h = 380, 170
    shell = card_shell(w, h, "TOP LANGUAGES")
    top = language_percentages(ranked_langs)
    if not top:
        msg = (f'<text x="{w/2}" y="95" text-anchor="middle" class="stat-lbl" font-size="11" opacity="0.7">'
               f'no data yet</text>'
               f'<text x="{w/2}" y="114" text-anchor="middle" class="stat-lbl" font-size="10" opacity="0.5">'
               f'populates on first Action run</text>')
        return shell + msg
    rows = []
    y = 56
    for i, (lang, n, pct) in enumerate(top):
        color = LANG_COLORS[i % len(LANG_COLORS)]
        bar_max = w - 56 - 70
        bar_w = max(bar_max * pct / 100, 3)
        rows.append(
            f'<text x="28" y="{y:.1f}" class="stat-lbl" font-size="10">{esc(lang)}</text>'
            f'<rect x="130" y="{y-9:.1f}" width="{bar_max}" height="7" rx="3" fill="{BORDER}"/>'
            f'<rect x="130" y="{y-9:.1f}" width="{bar_w:.1f}" height="7" rx="3" fill="{color}"/>'
            f'<text x="{w-28}" y="{y:.1f}" text-anchor="end" class="stat-lbl" font-size="9" opacity="0.7">{pct:.1f}%</text>'
        )
        y += 20
    return shell + "".join(rows)


def build_stats_combined_svg(overview, ranked_langs, streak, dmmono_b64, cormorant_b64):
    """All 3 panels in one file, fonts embedded once instead of once per
    card (this was 3 separate self-contained SVGs at first — each paying
    the ~51KB font cost independently — until rendering them side by side
    made the duplication obvious). Fixed-height, width="100%" in the
    README so it scales to whatever the actual content column width is,
    the same trick hero.svg and the wave banners already use, rather than
    a hand-picked pixel width that might not fit every viewport."""
    panel_w, panel_h, gap = 380, 170, 20
    W = panel_w * 3 + gap * 2
    H = panel_h
    panels = [build_overview_panel(overview), build_streak_panel(streak), build_languages_panel(ranked_langs)]
    groups = []
    for i, content in enumerate(panels):
        x = i * (panel_w + gap)
        groups.append(f'<g transform="translate({x},0)">{content}</g>')
    defs = font_defs(dmmono_b64, cormorant_b64)
    grain = (
        f'<filter id="statsGrain" x="-5%" y="-5%" width="110%" height="110%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" '
        f'seed="42" stitchTiles="stitch" result="n"/>'
        f'<feColorMatrix in="n" type="matrix" '
        f'values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0.5 0.5 0.5 0 0"/>'
        f'</filter>'
    )
    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>{defs}{grain}</defs>{"".join(groups)}'
        f'<rect width="{W}" height="{H}" filter="url(#statsGrain)" opacity="0.05"/></svg>'
    )


SAMPLE_OVERVIEW = {
    "followers": 0,
    "public_repos": 0,
    "stars": 0,
    "_sample": True,
}
SAMPLE_LANGS = []
SAMPLE_STREAK = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="render with placeholder data, no network calls")
    args = ap.parse_args()

    dmmono_b64 = b64_font("dm-mono-500.woff2")
    cormorant_b64 = b64_font("cormorant-garamond-600.woff2")
    os.makedirs(OUT_DIR, exist_ok=True)

    if args.sample:
        overview, ranked_langs, streak = SAMPLE_OVERVIEW, SAMPLE_LANGS, SAMPLE_STREAK
        print("[stats] --sample mode: rendering with placeholder data, no network calls made")
    else:
        token = os.environ.get("GITHUB_TOKEN")
        stats_token = os.environ.get("STATS_TOKEN")
        overview, non_fork = fetch_overview(token)
        ranked_langs = fetch_languages(non_fork, token)
        streak = fetch_streak(stats_token)

    svg = build_stats_combined_svg(overview, ranked_langs, streak, dmmono_b64, cormorant_b64)
    path = os.path.join(OUT_DIR, "stats.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {path} ({len(svg)/1024:.1f} KB)")


if __name__ == "__main__":
    main()

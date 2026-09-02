#!/usr/bin/env python3
"""Render an owned, animated 365-day GitHub contribution signal."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_data import load_design_tokens, load_profile


ROOT = SCRIPT_DIR.parent
OUT_DIR = ROOT / "generated"
PROFILE = load_profile()
USERNAME = PROFILE["identity"]["handle"]
PALETTE = PROFILE["visual_contract"]["palette"]
TOKENS = load_design_tokens()
WORLD = TOKENS["worlds"]["portfolio"]
PRIMARY = PALETTE["crimson"]
SECONDARY = TOKENS["color"]["secondaryCrimson"]
DEEP = PALETTE["deep_crimson"]
SIGNAL = PALETTE["signal"]
PAPER = PALETTE["paper"]
MUTED = PALETTE["muted"]
SURFACE = WORLD["surface"]
SURFACE_ALT = WORLD["surface_alt"]
LINE = WORLD["line"]
LEVEL_COLORS = (PALETTE["void"], SURFACE, DEEP, SECONDARY, PRIMARY)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def b64_font(filename: str) -> str:
    return base64.b64encode((SCRIPT_DIR / "fonts" / filename).read_bytes()).decode("ascii")


def parse_contribution_html(source: str) -> list[dict]:
    """Extract exact day counts and levels from GitHub's public calendar HTML."""
    tooltip_counts: dict[str, int] = {}
    tooltip_pattern = re.compile(
        r'<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>(.*?)</tool-tip>',
        re.IGNORECASE | re.DOTALL,
    )
    for target, tooltip_body in tooltip_pattern.findall(source):
        tooltip_text = html.unescape(re.sub(r"<[^>]+>", "", tooltip_body)).strip()
        count_match = re.search(r"([\d,]+)\s+contribution", tooltip_text, re.IGNORECASE)
        tooltip_counts[target] = int(count_match.group(1).replace(",", "")) if count_match else 0

    days_by_date: dict[str, dict] = {}
    for tag in re.findall(r"<td\b[^>]*>", source, re.IGNORECASE):
        if "ContributionCalendar-day" not in tag or "data-date=" not in tag:
            continue
        date_match = re.search(r'\bdata-date="([^"]+)"', tag)
        level_match = re.search(r'\bdata-level="([0-4])"', tag)
        id_match = re.search(r'\bid="([^"]+)"', tag)
        if not date_match or not level_match:
            continue
        date_value = date_match.group(1)
        target = id_match.group(1) if id_match else ""
        level = int(level_match.group(1))
        if target not in tooltip_counts:
            continue
        days_by_date[date_value] = {
            "date": dt.date.fromisoformat(date_value),
            "level": level,
            "count": tooltip_counts[target],
        }
    return [days_by_date[key] for key in sorted(days_by_date)]


def fetch_contributions(username: str, end_date: dt.date | None = None) -> list[dict]:
    end_date = end_date or dt.datetime.now(dt.timezone.utc).date()
    start_date = end_date - dt.timedelta(days=364)
    days_by_date = {}
    for year in range(start_date.year, end_date.year + 1):
        query = urllib.parse.urlencode({"from": f"{year}-01-01", "to": f"{year}-12-31"})
        url = f"https://github.com/users/{username}/contributions?{query}"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": f"{username}-contribution-stream"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            year_days = parse_contribution_html(response.read().decode("utf-8"))
        for item in year_days:
            if start_date <= item["date"] <= end_date:
                days_by_date[item["date"]] = item
    days = [days_by_date[key] for key in sorted(days_by_date)]
    expected_days = (end_date - start_date).days + 1
    if len(days) != expected_days:
        raise ValueError(
            f"GitHub returned {len(days)} exact contribution days; expected {expected_days}"
        )
    print(f"[contributions] fetched {len(days)} public calendar days")
    return days


def contribution_metrics(days: list[dict]) -> dict:
    ordered = sorted(days, key=lambda item: item["date"])
    total = sum(item["count"] for item in ordered)
    active = sum(item["count"] > 0 for item in ordered)
    longest = running = 0
    for item in ordered:
        if item["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    peak = max((item["count"] for item in ordered), default=0)
    return {"total": total, "active": active, "longest": longest, "peak": peak}


def sample_contributions() -> list[dict]:
    start = dt.date(2025, 8, 30)
    days = []
    for index in range(365):
        count = 0 if index % 7 in (0, 6) and index % 5 else (index * 11) % 19
        level = 0 if count == 0 else min(4, 1 + count // 5)
        days.append({"date": start + dt.timedelta(days=index), "count": count, "level": level})
    return days


def week_layout(days: list[dict]) -> tuple[dict[dt.date, tuple[int, int]], int]:
    ordered = sorted(days, key=lambda item: item["date"])
    first = ordered[0]["date"]
    first_sunday = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    positions = {}
    max_week = 0
    for item in ordered:
        delta = (item["date"] - first_sunday).days
        week, weekday = divmod(delta, 7)
        positions[item["date"]] = (week, weekday)
        max_week = max(max_week, week)
    return positions, max_week + 1


def build_contribution_stream_svg(days: list[dict], username: str = USERNAME) -> str:
    days = sorted(days, key=lambda item: item["date"])
    if not days:
        raise ValueError("contribution stream requires at least one day")

    positions, columns = week_layout(days)
    metrics = contribution_metrics(days)
    width, height = 1500, 520
    grid_x, grid_y = 184, 150
    cell, gap = 17, 5
    pitch = cell + gap
    grid_width = (columns - 1) * pitch + cell
    grid_height = 7 * pitch - gap
    dmmono = b64_font("dm-mono-500.woff2")

    cell_nodes = []
    for index, item in enumerate(days):
        week, weekday = positions[item["date"]]
        x = grid_x + week * pitch
        y = grid_y + weekday * pitch
        level = max(0, min(4, int(item["level"])))
        animation = ""
        if level >= 3:
            animation = (
                f'<animate attributeName="opacity" values=".72;1;.72" dur="{3.2 + (index % 9) * .23:.2f}s" '
                f'begin="-{(index % 31) * .17:.2f}s" repeatCount="indefinite"/>'
            )
        cell_nodes.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
            f'fill="{LEVEL_COLORS[level]}" stroke="{LINE}" stroke-opacity=".45" '
            f'data-date="{item["date"].isoformat()}" data-count="{item["count"]}">{animation}</rect>'
        )

    month_nodes = []
    seen_months = set()
    for item in days:
        month_key = (item["date"].year, item["date"].month)
        if month_key in seen_months:
            continue
        seen_months.add(month_key)
        week, _ = positions[item["date"]]
        x = grid_x + week * pitch
        month_nodes.append(
            f'<text x="{x}" y="130" class="mono" font-size="9" fill="{MUTED}" '
            f'letter-spacing="1.5">{item["date"].strftime("%b").upper()}</text>'
        )

    path_commands = []
    left = grid_x + cell / 2
    right = grid_x + (columns - 1) * pitch + cell / 2
    for row in range(7):
        y = grid_y + row * pitch + cell / 2
        if row == 0:
            path_commands.append(f"M {left:.1f} {y:.1f}")
        path_commands.append(f"H {right:.1f}" if row % 2 == 0 else f"H {left:.1f}")
        if row < 6:
            path_commands.append(f"V {grid_y + (row + 1) * pitch + cell / 2:.1f}")
    signal_path = " ".join(path_commands)

    weekly_totals = [0] * columns
    for item in days:
        week, _ = positions[item["date"]]
        weekly_totals[week] += item["count"]
    weekly_peak = max(weekly_totals) or 1
    wave_top, wave_height = 348, 48
    wave_points = []
    for index, value in enumerate(weekly_totals):
        x = grid_x + (grid_width * index / max(columns - 1, 1))
        y = wave_top + wave_height - (value / weekly_peak) * wave_height
        wave_points.append(f"{x:.1f},{y:.1f}")

    recent_active = next((item for item in reversed(days) if item["count"] > 0), days[-1])
    recent_week, recent_weekday = positions[recent_active["date"]]
    recent_x = grid_x + recent_week * pitch + cell / 2
    recent_y = grid_y + recent_weekday * pitch + cell / 2

    metric_specs = (
        ("365D CONTRIBUTIONS", f'{metrics["total"]:,}'),
        ("ACTIVE DAYS", f'{metrics["active"]}'),
        ("LONGEST STREAK", f'{metrics["longest"]}D'),
        ("PEAK DAY", f'{metrics["peak"]}'),
    )
    metric_nodes = []
    for index, (label, value) in enumerate(metric_specs):
        x = 96 + index * 350
        metric_nodes.append(
            f'<g transform="translate({x},430)">'
            f'<rect width="310" height="62" rx="5" fill="{SURFACE}" stroke="{LINE}"/>'
            f'<rect width="4" height="62" rx="2" fill="{PRIMARY}"/>'
            f'<text x="22" y="24" class="mono" font-size="8" fill="{MUTED}" letter-spacing="1.4">{label}</text>'
            f'<text x="22" y="51" class="metric" font-size="28">{value}</text>'
            f'<circle cx="286" cy="18" r="3" fill="{SIGNAL}"><animate attributeName="opacity" '
            f'values=".2;1;.2" dur="{1.4 + index * .27:.2f}s" repeatCount="indefinite"/></circle>'
            f'</g>'
        )

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
<title>365-day contribution signal for {esc(username)}</title>
<desc>{metrics["total"]} contributions across {metrics["active"]} active days, with an animated scan and activity waveform.</desc>
<defs>
<style>
@font-face {{ font-family:'DM Mono'; font-weight:500; src:url(data:font/woff2;base64,{dmmono}) format('woff2'); }}
.mono {{ font-family:'DM Mono',monospace; font-weight:500; }}
 .metric {{ font-family:Georgia,serif; font-weight:700; fill:{PAPER}; }}
</style>
<linearGradient id="streamBg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{PALETTE['void']}"/><stop offset=".58" stop-color="{SURFACE}"/><stop offset="1" stop-color="{DEEP}"/>
</linearGradient>
<linearGradient id="scan" x1="0" x2="1">
<stop offset="0" stop-color="{SIGNAL}" stop-opacity="0"/><stop offset=".5" stop-color="{SIGNAL}" stop-opacity=".22"/><stop offset="1" stop-color="{SIGNAL}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="wave" x1="0" x2="1"><stop stop-color="{DEEP}"/><stop offset=".55" stop-color="{PRIMARY}"/><stop offset="1" stop-color="{SIGNAL}"/></linearGradient>
<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".82" numOctaves="2" seed="71"/><feColorMatrix values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 .32 .32 .32 0 0"/></filter>
</defs>
<rect x="1" y="1" width="1498" height="518" rx="8" fill="url(#streamBg)" stroke="{LINE}"/>
<rect x="1" y="1" width="1498" height="518" rx="8" filter="url(#grain)" opacity=".045"/>
<path d="M24 70V24H70 M1430 24h46v46 M24 450v46h46 M1430 496h46v-46" fill="none" stroke="{PRIMARY}" stroke-width="2" opacity=".48"/>
<text x="72" y="55" class="mono" font-size="18" fill="{PAPER}" letter-spacing="4">CONTRIBUTION SIGNAL // 365-DAY ACTIVITY</text>
<text x="72" y="80" class="mono" font-size="9" fill="{MUTED}" letter-spacing="2">PUBLIC GITHUB TELEMETRY · EXACT DAILY COUNTS · OWNED ANIMATION</text>
<g transform="translate(1190,35)"><rect width="238" height="42" rx="21" fill="{SURFACE}" stroke="{DEEP}"/><circle cx="24" cy="21" r="5" fill="{SIGNAL}" filter="url(#glow)"><animate attributeName="opacity" values=".25;1;.25" dur="1.25s" repeatCount="indefinite"/></circle><text x="43" y="25" class="mono" font-size="9" fill="{PAPER}" letter-spacing="1.5">AUTO-REFRESH // 24H</text></g>
{''.join(month_nodes)}
<text x="94" y="181" class="mono" font-size="8" fill="{MUTED}" letter-spacing="1.3">MON</text>
<text x="94" y="225" class="mono" font-size="8" fill="{MUTED}" letter-spacing="1.3">WED</text>
<text x="94" y="269" class="mono" font-size="8" fill="{MUTED}" letter-spacing="1.3">FRI</text>
<path d="{signal_path}" fill="none" stroke="{SIGNAL}" stroke-width="2" stroke-dasharray="3 70" opacity=".18"><animate attributeName="stroke-dashoffset" values="0;-292" dur="5.5s" repeatCount="indefinite"/></path>
{''.join(cell_nodes)}
<rect x="{grid_x - 80}" y="{grid_y - 12}" width="80" height="{grid_height + 24}" fill="url(#scan)" opacity=".75"><animate attributeName="x" values="{grid_x - 80};{grid_x + grid_width}" dur="7.8s" repeatCount="indefinite"/></rect>
<circle cx="{recent_x:.1f}" cy="{recent_y:.1f}" r="12" fill="none" stroke="{PAPER}" stroke-width="2" filter="url(#glow)"><animate attributeName="r" values="9;18;9" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite"/></circle>
<text x="94" y="365" class="mono" font-size="8" fill="{MUTED}" letter-spacing="1.3">WEEKLY SIGNAL DENSITY</text>
<polyline points="{' '.join(wave_points)}" fill="none" stroke="{LINE}" stroke-width="8" opacity=".5"/>
<polyline points="{' '.join(wave_points)}" fill="none" stroke="url(#wave)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)" stroke-dasharray="1500" stroke-dashoffset="1500"><animate attributeName="stroke-dashoffset" values="1500;0" dur="3.4s" fill="freeze"/></polyline>
{''.join(metric_nodes)}
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="store_true", help="render deterministic sample data")
    args = parser.parse_args()
    try:
        days = sample_contributions() if args.sample else fetch_contributions(USERNAME)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as error:
        print(f"[contributions] generation failed: {error}", file=sys.stderr)
        return 1
    svg = build_contribution_stream_svg(days)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUT_DIR / "contribution-stream.svg"
    output.write_text(svg, encoding="utf-8")
    print(f"wrote {output} ({output.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

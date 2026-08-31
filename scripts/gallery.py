"""The Proof Gallery: deterministic, self-contained, GitHub-safe SVGs.

Copy and source-review notes are separate from the drawing code. Mobile panels
are re-composed at 600 units, not scaled-down desktop layouts. All newly drawn
body text is at least 42/600 or 26/900 of the rendered image width.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import html
import json
import math
from functools import lru_cache
from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "gallery.json"
MEDIA_DIR = ROOT / "assets" / "gallery"
REVISION = "v1"
PAPER, MUTED, RED, SIGNAL = "#f5eaea", "#c4b5b7", "#e84b4b", "#ff9d91"
VOID, PANEL, LINE = "#050507", "#0c080b", "#482029"
APPROVED_HERO_LF_SHA256 = "a34956d66f4fc6360bfef908c9927d1cb669ddcc70ca2fdfc92c7f975568e7dd"


def assert_approved_hero(svg: str) -> None:
    digest = hashlib.sha256(svg.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    if digest != APPROVED_HERO_LF_SHA256:
        raise ValueError("approved hero changed; the proof gallery must preserve it")


def load_gallery() -> dict:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if data["version"] != 1:
        raise ValueError("unsupported gallery version")
    dt.date.fromisoformat(data["checked_at"])
    order = data["featured"] + data["lab"]
    if len(order) != len(set(order)) or set(order) != set(data["projects"]):
        raise ValueError("gallery order must cover each project exactly once")
    for project_id, item in data["projects"].items():
        required = {"title", "label", "caption", "build", "evidence_note", "verified_scope",
                    "media", "media_note", "media_url", "source_url", "show_site"}
        if required - item.keys() or not item["title"]:
            raise ValueError(f"incomplete gallery entry: {project_id}")
        if item["media"] and Path(item["media"]).name != item["media"]:
            raise ValueError("media must be a filename inside assets/gallery")
        if not item["source_url"].startswith("https://github.com/yorayriniwnl/"):
            raise ValueError("gallery evidence must point to the owner's public source")
    return data


def asset_name(stem: str, mobile: bool = False) -> str:
    return f"gallery-{stem}{'-mobile' if mobile else ''}-{REVISION}.svg"


def escape(value) -> str:
    return html.escape(str(value), quote=True)


def text(x, y, value, size=26, color=PAPER, family="sans", role="body", anchor="start", **attrs):
    extra = " ".join(f'{key.replace("_", "-")}="{escape(value)}"' for key, value in attrs.items())
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size:g}" fill="{color}" '
            f'class="{family}" text-anchor="{anchor}" data-text-role="{role}" {extra}>'
            f'{escape(value)}</text>')


def wrap(value: str, width: float, size: float) -> list[str]:
    """Use portable Helvetica metrics, with safety room for Arial substitution."""
    lines, current = [], ""
    for word in value.split():
        candidate = f"{current} {word}".strip()
        if current and stringWidth(candidate, "Helvetica", size) > width * .95:
            lines.append(current)
            current = word
        else:
            current = candidate
        if stringWidth(current, "Helvetica", size) > width * .95:
            # Long identifiers still wrap without silently dropping content.
            chunk = ""
            for character in current:
                if chunk and stringWidth(chunk + character, "Helvetica", size) > width * .95:
                    lines.append(chunk)
                    chunk = ""
                chunk += character
            current = chunk
    if current:
        lines.append(current)
    return lines


def paragraph(x, y, value, width, size, color=MUTED, leading=None, role="body"):
    leading = leading or size * 1.35
    lines = wrap(value, width, size)
    return "".join(text(x, y + i * leading, line, size, color, role=role)
                   for i, line in enumerate(lines)), y + len(lines) * leading


@lru_cache(maxsize=1)
def display_font() -> str:
    return base64.b64encode((ROOT / "scripts/fonts/cormorant-garamond-600.woff2").read_bytes()).decode("ascii")


def shell(width, height, title, description, body, *, mobile=False, defs="", display=True, flat=False):
    font = ("@font-face{font-family:GalleryDisplay;font-weight:600;src:url(data:font/woff2;base64,"
            + display_font() + ") format('woff2')}" if display else "")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description" data-gallery="proof-gallery-v1" data-layout="{'mobile' if mobile else 'desktop'}">
<title id="title">{escape(title)}</title><desc id="description">{escape(description)}</desc>
<defs><style>{font}
.sans{{font-family:Arial,Helvetica,sans-serif}}.serif{{font-family:GalleryDisplay,Georgia,serif;font-weight:600}}
.thread{{stroke-dasharray:70 900;animation:thread 16s linear infinite}}
@keyframes thread{{to{{stroke-dashoffset:-970}}}}
@media(prefers-reduced-motion:reduce){{.thread{{animation:none;stroke-dasharray:none;opacity:.45}}}}
</style>
<linearGradient id="surface" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#101014"/><stop offset=".5" stop-color="#09070a"/><stop offset="1" stop-color="#210c12"/></linearGradient>
<linearGradient id="filament"><stop stop-color="#48101f"/><stop offset=".5" stop-color="#e84b4b"/><stop offset="1" stop-color="#ffd2bf"/></linearGradient>
<radialGradient id="halo"><stop stop-color="#e84b4b" stop-opacity=".19"/><stop offset="1" stop-color="#e84b4b" stop-opacity="0"/></radialGradient>
{defs}</defs>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="{0 if flat else 14}" fill="{VOID if flat else 'url(#surface)'}" stroke="{VOID if flat else LINE}"/>
{body}
</svg>'''


def rule(width, y, left=36):
    return (f'<path d="M{left} {y}H{width-left}" stroke="{LINE}"/>'
            f'<path d="M{left} {y}H{left+70}" stroke="{SIGNAL}" stroke-width="2"/>')


def filament(kind, x, y, width, height):
    """Illustrative domain geometry; deliberately contains no invented metrics."""
    curves = []
    for row in range(13):
        points = []
        for i in range(62):
            u = i / 61
            if kind in {"portfolio", "feelings"}:
                px = x + u * width
                py = y + height * .5 + math.sin(u * math.tau + row * .09) * height * .3 + (row - 6) * 3
            elif kind == "zenith":
                px = x + u * width
                py = y + height * .24 + abs(u - .5) * height * .65 + row * 7
            elif kind == "vision":
                px = x + u * width
                py = y + height * .5 + math.sin(u * math.tau * 3 + row * .35) * height * .2 + (row - 6) * 7
            else:
                px = x + u * width
                py = y + height * .5 + (row - 6) * height / 18 * math.cos(u * math.pi)
            points.append(f"{px:.1f},{py:.1f}")
        curves.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="url(#filament)" stroke-width="{1.8 if row == 6 else .8}" opacity="{.8 if row == 6 else .28}"/>')
        if row == 6:
            curves.append(f'<polyline class="thread" points="{" ".join(points)}" fill="none" stroke="{SIGNAL}" stroke-width="2"/>')
    return f'<g data-art="illustrative-{kind}">{"".join(curves)}</g>'


def media_uri(filename):
    path = MEDIA_DIR / filename
    if not path.is_file():
        raise ValueError(f"reviewed capture missing: {path}")
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def cover(project, spec, checked_at, mobile=False, compact=False):
    width, pad = (600, 36) if mobile else (900, 40)
    size = 42 if mobile else 26
    if compact:
        body = text(pad, 62, spec["label"], size, SIGNAL, role="caption")
        y = 132 if mobile else 128
        for line in spec["title"]:
            body += text(pad, y, line, 66 if mobile else 62, family="serif", role="heading")
            y += 67 if mobile else 61
        body, y = _append_paragraph(body, pad, y + 8, spec["caption"], width - pad * 2, size)
        body += rule(width, y + 10)
        note = project["status"] if project["id"] != "talks" else "Source study"
        body += text(pad, y + 63, note, size, SIGNAL, role="caption")
        body += filament(project["id"], width - 190, y + 4, 154, 70)
        height = math.ceil(y + 96)
        return shell(width, height, project["name"], spec["caption"] + " " + spec["evidence_note"], body, mobile=mobile)

    body = text(pad, 65, spec["label"], size, SIGNAL, role="caption")
    if mobile:
        y = 148
        for line in spec["title"]:
            for title_line in wrap(line, width - pad * 2, 63):
                body += text(pad, y, title_line, 72, family="serif", role="heading")
                y += 73
        body += filament(project["id"], 16, y - 37, width - 32, 118)
        screen_x, screen_y, screen_w, screen_h = 26, y + 24, width - 52, 310
        y = screen_y + screen_h + 56
        body, y = _append_paragraph(body, pad, y, spec["caption"], width - pad * 2, size)
        body += rule(width, y + 8)
        body, y = _append_paragraph(body, pad, y + 61, spec["media_note"], width - pad * 2, size, SIGNAL)
        height = math.ceil(y + 28)
    else:
        y = 142
        for line in spec["title"]:
            for title_line in wrap(line, 345, 50):
                body += text(pad, y, title_line, 61, family="serif", role="heading")
                y += 63
        body, y = _append_paragraph(body, pad, y + 22, spec["caption"], 344, size)
        screen_x, screen_y, screen_w, screen_h = 426, 104, 442, 300
        body += filament(project["id"], 416, 350, 450, 142)
        footer_y = max(490, y + 20)
        body += rule(width, footer_y)
        body += text(pad, footer_y + 50, spec["media_note"], 26, SIGNAL, role="caption")
        body += text(width - pad, footer_y + 50, checked_at, 26, MUTED, anchor="end", role="caption")
        height = math.ceil(footer_y + 85)

    clip = f'<clipPath id="capture"><rect x="{screen_x}" y="{screen_y}" width="{screen_w}" height="{screen_h}" rx="10"/></clipPath>'
    body += (f'<rect x="{screen_x-5}" y="{screen_y-5}" width="{screen_w+10}" height="{screen_h+10}" rx="13" fill="#100d12" stroke="#90515b"/>'
             f'<image href="{media_uri(spec["media"])}" x="{screen_x}" y="{screen_y}" width="{screen_w}" height="{screen_h}" preserveAspectRatio="xMidYMid meet" clip-path="url(#capture)"/>')
    return shell(width, height, project["name"] + " / " + spec["label"],
                 spec["caption"] + " Actual interface capture, " + checked_at + ". " + spec["evidence_note"],
                 body, mobile=mobile, defs=clip)


def _append_paragraph(body, x, y, value, width, size, color=MUTED):
    nodes, next_y = paragraph(x, y, value, width, size, color)
    return body + nodes, next_y


def dossier(project, spec, checked_at, mobile=False):
    width, pad, size = (600, 36, 42) if mobile else (900, 40, 26)
    body = text(pad, 64, "UNDER THE HOOD", size, SIGNAL, role="caption")
    body, y = _append_paragraph(body, pad, 126, project["name"], width - pad * 2, size + 8, PAPER)
    sections = [
        ("01 / PURPOSE", project["summary"]),
        ("02 / SYSTEM", spec["build"]),
        ("03 / EVIDENCE", " / ".join(project["proof"])),
        ("04 / REVIEW SCOPE", spec["evidence_note"]),
        ("05 / STACK", " / ".join(project["stack"])),
    ]
    for label, copy in sections:
        body += rule(width, y + 13)
        body += text(pad, y + 65, label, size, SIGNAL, role="caption")
        body, y = _append_paragraph(body, pad, y + 65 + size * 1.5, copy, width - pad * 2, size)
        y += 20
    body, y = _append_paragraph(body, pad, y + 25, "Source review: " + checked_at, width - pad * 2, size)
    return shell(width, math.ceil(y + 30), project["name"] + " / engineering notes",
                 project["status"] + ". " + spec["verified_scope"] + ". " + " ".join(project["proof"]),
                 body, mobile=mobile, display=False)


BUTTONS = {
    "projects": ("PROJECTS", "down"), "resume": ("RÉSUMÉ", "file"),
    "site": ("OPEN SITE", "arrow"), "source": ("SOURCE", "code"),
    "email": ("EMAIL", "mail"), "linkedin": ("LINKEDIN", "arrow"),
    "text": ("TEXT EDITION", "file"), "github": ("GITHUB", "code"),
    "steam": ("STEAM", "arrow"), "devpost": ("DEVPOST", "arrow"),
    "hub": ("THE HUB", "arrow"), "evidence": ("EVIDENCE", "code"),
}


def button(label, glyph="arrow", toggle=False):
    width, height = (360, 96) if toggle else (280, 96)
    symbols = {
        "arrow": '<path d="M0 12H24M12 0l12 12-12 12"/>',
        "down": '<path d="M12 0v24M0 12l12 12 12-12"/>',
        "file": '<path d="M4 0h13l7 7v22H4zM17 0v8h7M9 15h10M9 22h10"/>',
        "mail": '<rect x="0" y="3" width="28" height="22" rx="3"/><path d="m1 5 13 10L27 5"/>',
        "code": '<path d="m8 0-9 12 9 12m12-24 9 12-9 12"/>',
    }
    font_size = min(31 if toggle else 30, math.floor((width - 84) / stringWidth(label, "Helvetica-Bold", 1)))
    if font_size < 28:
        raise ValueError("shorten the control label instead of shrinking its text")
    body = (f'<path d="M18 1H{width-18}" stroke="#ad5965"/>'
            f'<path d="M18 95H{width-18}" stroke="#56202d"/>'
            f'<path class="thread" d="M14 2H{width-14}Q{width-2} 2 {width-2} 14V82Q{width-2} 94 {width-14} 94H14" fill="none" stroke="{SIGNAL}"/>'
            f'<g transform="translate(24 35)" fill="none" stroke="{SIGNAL}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">{symbols[glyph]}</g>'
            + text(64, 60, label, font_size, PAPER, role="control", font_weight="600"))
    return shell(width, height, label, "Expand technical notes" if toggle else label, body, display=False)


def intro(profile, mobile=False):
    width, pad, size = (600, 36, 42) if mobile else (900, 40, 26)
    body = text(pad, 62, "AYR / PROOF GALLERY", size, SIGNAL, role="caption")
    body, y = _append_paragraph(body, pad, 117, profile["identity"]["role"] + " / " + profile["identity"]["specialty"], width - pad * 2, size, PAPER)
    body, y = _append_paragraph(body, pad, y + 15, "Open to SWE internships / remote", width - pad * 2, size)
    return shell(width, math.ceil(y + 28), "Ayush Roy / The Proof Gallery", profile["identity"]["positioning"], body, mobile=mobile, display=False)


SECTIONS = {
    "projects": ("01", "Selected work."),
    "lab": ("02", "The lab."),
    "builder": ("03", "The builder."),
    "record": ("04", "Public record."),
    "contact": ("05", "Open channel."),
}


def section(key, mobile=False):
    width = 600 if mobile else 900
    number, label = SECTIONS[key]
    body = text(36, 78, number + " /", 42 if mobile else 26, SIGNAL, role="caption")
    body += text(150 if mobile else 122, 81, label, 52 if mobile else 48, family="serif", role="heading")
    body += rule(width, 107)
    return shell(width, 123, label, label, body, mobile=mobile, flat=True)


def builder(profile, mobile=False):
    width, pad, size = (600, 36, 42) if mobile else (900, 40, 26)
    experience, education = profile["experience"][0], profile["education"][0]
    body = text(pad, 64, "AYUSH ROY / INDIA", size, SIGNAL, role="caption")
    entries = [
        ("NETWORKS / BSNL", experience["role"] + ". " + experience["period"] + ". " + experience["summary"]),
        ("EDUCATION / KIIT", education["degree"] + ". " + education["period"] + "."),
        ("CURRENTLY EXPLORING", "LLMs, RAG, AI agents, and AWS. Learning direction, separate from demonstrated project work."),
    ]
    y = 90
    for label, copy in entries:
        body += rule(width, y + 15)
        body += text(pad, y + 68, label, size, SIGNAL, role="caption")
        body, y = _append_paragraph(body, pad, y + 68 + size * 1.5, copy, width - pad * 2, size)
        y += 20
    return shell(width, math.ceil(y + 25), "The builder / experience and education", profile["identity"]["positioning"], body, mobile=mobile, display=False)


def contact(profile, mobile=False):
    width, pad, size = (600, 36, 42) if mobile else (900, 40, 26)
    body = filament("portfolio", 0, 20, width, 160)
    y = 210
    for line in ("Grind.", "Build. Repeat.") if mobile else ("Grind. Build. Repeat.",):
        body += text(pad, y, line, 90 if mobile else 94, family="serif", role="heading")
        y += 90
    body, y = _append_paragraph(body, pad, y + 25, profile["availability"]["status"] + ". Open to remote collaboration.", width - pad * 2, size)
    return shell(width, math.ceil(y + 36), "Open a conversation with Ayush Roy", profile["contact"]["email"], body, mobile=mobile)


def render_public_record(overview, checked_at, mobile=False):
    """A dated snapshot. No fabricated views, online counts, or freshness claim."""
    width, pad, size = (600, 36, 42) if mobile else (900, 40, 26)
    if overview.get("_sample"):
        status, values = "DESIGN SAMPLE / NOT LIVE", ["—", "—", "—"]
    else:
        status = "GITHUB / SNAPSHOT"
        values = [f'{overview[key]:,}' for key in ("public_repos", "stars", "followers")]
    body = text(pad, 64, status, size, SIGNAL, role="caption")
    y = 145
    for label, value in zip(("Public repositories", "Repository stars", "Followers"), values):
        body += text(pad, y, label, size, MUTED)
        body += text(width - pad, y + 4, value, 57 if mobile else 60, PAPER, anchor="end", role="metric")
        body += rule(width, y + 32)
        y += 107 if mobile else 94
    body, y = _append_paragraph(body, pad, y + 8, "Updated " + checked_at, width - pad * 2, size)
    body, y = _append_paragraph(body, pad, y + 12, "Snapshot, not a live audience count.", width - pad * 2, size)
    return shell(width, math.ceil(y + 25), "GitHub public record", "GitHub REST snapshot as of " + checked_at, body, mobile=mobile, display=False)


def render_contributions(days, checked_at, mobile=False, sample=False):
    width, pad, size = (600, 36, 42) if mobile else (900, 40, 26)
    ordered = sorted(days, key=lambda item: item["date"])
    if not ordered:
        raise ValueError("a contribution snapshot must have daily data")
    total = sum(item["count"] for item in ordered)
    active = sum(item["count"] > 0 for item in ordered)
    body = text(pad, 64, "SAMPLE / NOT LIVE" if sample else "CONTRIBUTION SIGNAL", size, SIGNAL, role="caption")
    body += text(pad, 145, f"{total:,}", 78 if mobile else 80, PAPER, role="metric")
    body += text(pad, 201, f"contributions / {len(ordered)} days", size, MUTED)
    recent = ordered[-91:]
    peak = max((item["count"] for item in recent), default=1) or 1
    chart_top, chart_h, chart_w = 249, 130, width - 2 * pad
    points = [(pad + i * chart_w / max(len(recent) - 1, 1), chart_top + chart_h - item["count"] / peak * chart_h) for i, item in enumerate(recent)]
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    body += f'<path d="M{pad} {chart_top+chart_h}H{width-pad}" stroke="{LINE}"/>'
    body += f'<polyline points="{path}" fill="none" stroke="{RED}" stroke-width="3" stroke-linejoin="round"/>'
    body, y = _append_paragraph(body, pad, 438, "Recent 13 weeks / daily counts", width - 2 * pad, size)
    body, y = _append_paragraph(body, pad, y + 32, f"{active} active days / {len(ordered)} days", width - 2 * pad, size, PAPER)
    body, y = _append_paragraph(body, pad, y + 32, "Updated " + checked_at, width - 2 * pad, size)
    return shell(width, math.ceil(y + 35), "Public GitHub contribution history",
                 f"{total} contributions and {active} active days from {ordered[0]['date']} to {ordered[-1]['date']}. Chart shows the latest 13 weeks. Snapshot: {checked_at}.",
                 body, mobile=mobile, display=False)


def build_gallery_manifest(profile):
    gallery = load_gallery()
    projects = {item["id"]: item for item in profile["projects"]}
    if set(projects) != set(gallery["projects"]):
        raise ValueError("gallery must match the canonical project set")
    manifest = {}
    for mobile in (False, True):
        manifest[asset_name("intro", mobile)] = intro(profile, mobile)
        manifest[asset_name("builder", mobile)] = builder(profile, mobile)
        manifest[asset_name("contact", mobile)] = contact(profile, mobile)
        for key in SECTIONS:
            manifest[asset_name("section-" + key, mobile)] = section(key, mobile)
        for project_id in gallery["featured"] + gallery["lab"]:
            project, spec = projects[project_id], gallery["projects"][project_id]
            manifest[asset_name(project_id, mobile)] = cover(project, spec, gallery["checked_at"], mobile, project_id in gallery["lab"])
            manifest[asset_name("dossier-" + project_id, mobile)] = dossier(project, spec, gallery["checked_at"], mobile)
    for key, (label, glyph) in BUTTONS.items():
        manifest[asset_name("button-" + key)] = button(label, glyph)
    manifest[asset_name("toggle")] = button("UNDER THE HOOD", "down", toggle=True)
    manifest[asset_name("motion-toggle")] = button("THE SIGNAL STUDY", "down", toggle=True)
    return manifest

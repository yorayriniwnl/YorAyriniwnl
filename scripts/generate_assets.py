#!/usr/bin/env python3
"""
Regenerates the profile's visual system under generated/ from the two
vendored fonts and the config below.

Run locally with `python3 scripts/generate_assets.py`, or let
.github/workflows/build-assets.yml run it on push / weekly cron.

Edit CONFIG to change name/role/colors/motif density — never hand-edit
anything under generated/, it's all generated. Positions are seeded
(CONFIG["seed"]) so output is reproducible between runs.
"""
import base64
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "generated")
ASSET_DIR = os.path.join(HERE, "..", "assets")

CONFIG = {
    "name": "Ayush Roy",
    "role": "SYSTEMS ENGINEER  ·  PRODUCT BUILDER",
    "width": 1500,
    "height": 300,
    # Steam-profile palette: a pure-black canvas, translucent black panels,
    # and the #671515 -> #8c1616 crimson header gradient used by the live
    # profile's showcase bars.
    "bg_stops": [
        (0, "#000000"), (18, "#050101"), (42, "#1f0404"),
        (64, "#671515"), (82, "#180303"), (100, "#000000"),
    ],
    "primary": "#e84b4b",
    "secondary": "#b92b2b",
    "sparkle": "#ff8a7f",
    "muted": "#c4c4c4",
    "shimmer": "#ffffff",
    "name_color": "#f5eaea",
    "seed": 42,
    "star_counts": {"far": 34, "mid": 24, "near": 13},
    "sparkle_count": 6,
    "tagline": {
        "width": 760,
        "height": 34,
        "type_ms_per_char": 42,
        "delete_ms_per_char": 20,
        "hold_ms": 1500,
        "gap_ms": 200,
        # (text, measured px width in DM Mono 500 @ 14px/0.5 letter-spacing —
        # measured in an actual browser against the real embedded font by
        # scripts/measure_tagline.py; re-run it if any line's text changes.
        # Re-measured in Pass 4 against Chrome 131.0.6778.204 — see
        # CHANGELOG for why the old numbers were short.)
        "lines": [
            ("Building the software layer for the physical world.", 453.9),
            ("Geospatial \u00b7 Realtime \u00b7 Computer Vision \u00b7 Systems Engineering", 542.9),
            ("Rust for the systems layer, GenAI + AWS for the applied one.", 534.0),
            ("The domain changes; the standard doesn't.", 364.9),
        ],
    },
    "wave_header_stops": [(0, "#000000"), (60, "#671515"), (100, "#160303")],
    "wave_footer_stops": [(0, "#160303"), (60, "#671515"), (100, "#000000")],
    # (output filename, glyph, config color key) — one small seal per work-
    # section project, in the same primary/secondary alternation the
    # badges under each project already use.
    "seals": [
        ("seal-portfolio", "\u2726", "primary"),
        ("seal-helios", "\u25c8", "secondary"),
        ("seal-zenith", "\u2600", "primary"),
        ("seal-ai-vs-real", "\u25cd", "secondary"),
        ("seal-talks", "\u2b21", "primary"),
    ],
}

# The name/role/rule block's footprint, in canvas coordinates. Background
# motifs (nebula, kintsugi, constellation) are kept clear of this — verified
# contrast for the text shouldn't have to be re-earned every time a new
# layer is added behind it. Stars are exempt: they render *behind* the
# opaque text glyphs in paint order, so overlap there is invisible, not risky.
TEXT_ZONE = {"x0": 330, "x1": 1170, "y0": 92, "y1": 228}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def b64_font(filename):
    with open(os.path.join(HERE, "fonts", filename), "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def asset_data_uri(filename, mime_type):
    """Embed a project-owned raster inside an SVG so GitHub never has to
    resolve a nested remote image request. The generated SVGs stay fully
    self-contained and continue to animate when rendered through raw GitHub."""
    with open(os.path.join(ASSET_DIR, filename), "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def in_zone(x, y, pad=0):
    z = TEXT_ZONE
    return (z["x0"] - pad) <= x <= (z["x1"] + pad) and (z["y0"] - pad) <= y <= (z["y1"] + pad)


# ---------------------------------------------------------------- starfield

def gen_star_layer(rng, count, r_range, op_range, dur_range, color, w, h):
    els = []
    made, tries = 0, 0
    while made < count and tries < count * 40:
        tries += 1
        x = rng.uniform(12, w - 12)
        y = rng.uniform(8, h - 8)
        if in_zone(x, y):
            continue
        r = rng.uniform(*r_range)
        op = rng.uniform(*op_range)
        dur = rng.uniform(*dur_range)
        delay = rng.uniform(0, dur)
        els.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{color}">'
            f'<animate attributeName="opacity" values="{op*0.16:.2f};{op:.2f};{op*0.16:.2f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/></circle>'
        )
        made += 1
    return "".join(els)


def sparkle_local_path(size):
    k = size * 0.18
    return (
        f'M0 {-size:.1f} Q{k:.1f} {-k:.1f} {size:.1f} 0 '
        f'Q{k:.1f} {k:.1f} 0 {size:.1f} '
        f'Q{-k:.1f} {k:.1f} {-size:.1f} 0 '
        f'Q{-k:.1f} {-k:.1f} 0 {-size:.1f} Z'
    )


def gen_sparkles(rng, count, color, w, h):
    els = []
    made, tries = 0, 0
    while made < count and tries < count * 50:
        tries += 1
        x = rng.uniform(30, w - 30)
        y = rng.uniform(20, h - 20)
        if in_zone(x, y, pad=26):
            continue
        size = rng.uniform(3.4, 6.2)
        dur = rng.uniform(3.2, 5.6)
        delay = rng.uniform(0, dur)
        d = sparkle_local_path(size)
        els.append(
            f'<g transform="translate({x:.1f},{y:.1f})">'
            f'<path d="{d}" fill="{color}" opacity="0">'
            f'<animate attributeName="opacity" keyTimes="0;0.14;0.5;0.62;1" '
            f'values="0;0.85;0.15;0.85;0" dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="scale" '
            f'keyTimes="0;0.14;0.5;0.62;1" values="0.4;1.15;0.85;1.05;0.4" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'</path></g>'
        )
        made += 1
    return "".join(els)


# -------------------------------------------------------------------- comet

def gen_comet(x1, y1, x2, y2, dur, begin, color):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    tail = 68
    tx, ty = -ux * tail, -uy * tail
    gid = f"cometTrail{abs(hash((x1, y1, x2, y2))) % 10000}"
    defs = (
        f'<linearGradient id="{gid}" x1="{tx:.1f}" y1="{ty:.1f}" x2="0" y2="0" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0.95"/></linearGradient>'
    )
    body = (
        f'<g opacity="0">'
        f'<animate attributeName="opacity" keyTimes="0;0.02;0.1;0.16;1" values="0;1;1;0;0" '
        f'dur="{dur:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
        f'<animateMotion keyTimes="0;0.13;1" keyPoints="0;1;1" calcMode="linear" '
        f'path="M{x1:.0f},{y1:.0f} L{x2:.0f},{y2:.0f}" '
        f'dur="{dur:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
        f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="0" y2="0" stroke="url(#{gid})" '
        f'stroke-width="1.5" stroke-linecap="round"/>'
        f'<circle cx="0" cy="0" r="2" fill="{color}"/>'
        f'</g>'
    )
    return defs, body


# --------------------------------------------------------------------- grain

def grain_filter(fid, seed):
    """A fine, low-frequency-free noise texture — the "grain textures" this
    project's own established visual language calls for but never actually
    had. feTurbulence + a color matrix that collapses the noise to a
    neutral, alpha-only signal (never colored static); applied as a single
    full-canvas rect at very low opacity by the caller, over everything
    else including text, the way real film grain sits over a whole frame
    rather than just the background."""
    return (
        f'<filter id="{fid}" x="-5%" y="-5%" width="110%" height="110%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" '
        f'seed="{seed}" stitchTiles="stitch" result="n"/>'
        f'<feColorMatrix in="n" type="matrix" '
        f'values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0.5 0.5 0.5 0 0"/>'
        f'</filter>'
    )


# -------------------------------------------------------------------- embers

def gen_embers(rng, count, colors, w, h, y_lo_frac=0.5):
    """Small glowing points that drift upward and fade — embers off a fire
    rather than a starfield. Only makes sense against the red palette;
    would have read as noise against the old purple void. Lives in the
    same paint-order group as the star layers (behind the opaque text),
    so a spawn point under TEXT_ZONE is fine, not checked against it."""
    els = []
    made, tries = 0, 0
    while made < count and tries < count * 40:
        tries += 1
        x = rng.uniform(16, w - 16)
        y0 = rng.uniform(h * y_lo_frac, h + 14)
        rise = rng.uniform(60, 150) if h > 60 else rng.uniform(18, 34)
        sway = rng.uniform(-16, 16)
        r = rng.uniform(0.9, 2.1)
        color = colors[made % len(colors)]
        dur = rng.uniform(4.5, 8.0)
        delay = rng.uniform(0, dur)
        els.append(
            f'<circle r="{r:.2f}" fill="{color}">'
            f'<animate attributeName="opacity" keyTimes="0;0.1;0.7;1" values="0;0.9;0.35;0" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{x:.1f},{y0:.1f}; {x+sway:.1f},{y0-rise:.1f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'</circle>'
        )
        made += 1
    return "".join(els)


# ---------------------------------------------------------------- decoration

def gen_nebula(cfg):
    blobs = [
        (230, 55, 250, 165, cfg["secondary"], 0.15, 9.0),
        (1280, 245, 290, 180, cfg["primary"], 0.12, 12.5),
        (760, 30, 330, 130, "#6b1420", 0.20, 16.0),  # deep wine, red-family twin of the old #5b1f7a violet
    ]
    defs, uses = [], []
    for i, (cx, cy, rx, ry, color, op, dur) in enumerate(blobs):
        gid = f"neb{i}"
        defs.append(
            f'<radialGradient id="{gid}" cx="50%" cy="50%" r="50%">'
            f'<stop offset="0%" stop-color="{color}" stop-opacity="{op}"/>'
            f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/></radialGradient>'
        )
        # Slow breathing — opacity and radius both drift, out of phase across
        # the three blobs (9/12.5/16s) so they never pulse in visible unison.
        uses.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{gid})" '
            f'filter="url(#softBlur)" opacity="0.85">'
            f'<animate attributeName="opacity" values="0.7;1;0.7" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="rx" values="{rx*0.94:.0f};{rx*1.06:.0f};{rx*0.94:.0f}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="ry" values="{ry*0.94:.0f};{ry*1.06:.0f};{ry*0.94:.0f}" dur="{dur}s" repeatCount="indefinite"/>'
            f'</ellipse>'
        )
    return "".join(defs), "".join(uses)


def gen_kintsugi(color):
    def crack(points, op, width=1.3):
        d = f"M{points[0][0]},{points[0][1]} " + " ".join(
            f"L{x},{y}" for x, y in points[1:]
        )
        nodes = "".join(
            f'<circle cx="{x}" cy="{y}" r="2" fill="{color}" opacity="{op+0.16:.2f}"/>'
            for x, y in points[1:-1]
        )
        return f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" opacity="{op:.2f}" stroke-linecap="round" stroke-linejoin="round"/>{nodes}'

    crack_a = crack([(16, 300), (68, 253), (56, 208), (104, 172)], 0.20)
    crack_b = crack([(1484, 0), (1428, 34), (1452, 68), (1396, 92)], 0.18)
    return crack_a + crack_b


def gen_constellation(color):
    left = [(90, 68), (172, 128), (108, 208)]
    right = [(1252, 54), (1362, 92), (1400, 188), (1298, 234)]
    lines = [
        (left[0], left[1]), (left[1], left[2]), (left[2], left[0]),
        (right[0], right[1]), (right[1], right[2]),
        (right[2], right[3]), (right[3], right[0]), (right[1], right[3]),
    ]
    parts = []
    for (x1, y1), (x2, y2) in lines:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="0.6"/>')
    for x, y in left + right:
        parts.append(f'<circle cx="{x}" cy="{y}" r="1.7" fill="{color}"/>')
    inner = "".join(parts)
    return (
        f'<g opacity="0.16">{inner}'
        f'<animate attributeName="opacity" values="0.08;0.22;0.08" dur="7s" repeatCount="indefinite"/>'
        f'</g>'
    )


def gen_corner_brackets(color, w, h):
    L, inset = 22, 14
    corners = [
        (inset, inset, 1, 1, 0.0), (w - inset, inset, -1, 1, -2.1),
        (inset, h - inset, 1, -1, -4.2), (w - inset, h - inset, -1, -1, -6.3),
    ]
    parts = []
    for x, y, ax, ay, phase in corners:
        parts.append(
            f'<path d="M{x},{y+ay*L} L{x},{y} L{x+ax*L},{y}" '
            f'stroke="{color}" stroke-width="1.1" fill="none" opacity="0.5" stroke-linecap="round">'
            f'<animate attributeName="opacity" values="0.32;0.6;0.32" dur="8.4s" '
            f'begin="{phase}s" repeatCount="indefinite"/>'
            f'</path>'
        )
    return "".join(parts)


def gen_divider_ornament(cx, y, color, half_width, dot_gap):
    """Rule line + flanking accents + center diamond, shared by the hero's
    name-underline, wave-final's closing rule, and the standalone divider
    files. Self-contained gradient defs (own id, not a shared "rule" the
    caller has to remember to define) — the previous version relied on
    the caller providing `id="rule"`, which hero.svg and the standalone
    dividers did but wave-final.svg never did, so its connecting hairline
    has been invisible since Pass 3. Fixed by no longer depending on it."""
    uid = f"{int(cx)}_{int(y)}_{half_width}"
    w0 = cx - half_width
    band = min(200, half_width * 0.8)
    sparkle_defs = []
    for i, (sx, phase) in enumerate([(cx - dot_gap, 0.0), (cx + dot_gap, 2.3)]):
        sparkle_defs.append(
            f'<path d="M{sx},{y-3.4} L{sx+1.0},{y-1.0} L{sx+3.4},{y} L{sx+1.0},{y+1.0} '
            f'L{sx},{y+3.4} L{sx-1.0},{y+1.0} L{sx-3.4},{y} L{sx-1.0},{y-1.0} Z" '
            f'fill="{color}" opacity="0.4">'
            f'<animate attributeName="opacity" values="0.28;0.85;0.28" dur="4.6s" '
            f'begin="-{phase}s" repeatCount="indefinite"/>'
            f'</path>'
        )
    return (
        f'<g>'
        f'<defs>'
        f'<linearGradient id="rule{uid}" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{color}" stop-opacity="0.65"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient>'
        f'<linearGradient id="shine{uid}" gradientUnits="userSpaceOnUse" '
        f'x1="{w0-band:.0f}" y1="0" x2="{w0:.0f}" y2="0">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="#fff2f0" stop-opacity="0.9"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'<animate attributeName="x1" values="{w0-band:.0f};{cx+half_width:.0f}" dur="7s" repeatCount="indefinite"/>'
        f'<animate attributeName="x2" values="{w0:.0f};{cx+half_width+band:.0f}" dur="7s" repeatCount="indefinite"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<rect x="{w0}" y="{y}" width="{half_width*2}" height="1" fill="url(#rule{uid})"/>'
        f'<rect x="{w0}" y="{y-0.75}" width="{half_width*2}" height="1.5" fill="url(#shine{uid})"/>'
        f'{"".join(sparkle_defs)}'
        f'<rect x="{cx-7}" y="{y-7}" width="14" height="14" fill="{color}" opacity="0.16" '
        f'transform="rotate(45 {cx} {y})">'
        f'<animate attributeName="opacity" values="0.08;0.26;0.08" dur="3.4s" repeatCount="indefinite"/>'
        f'</rect>'
        f'<rect x="{cx-4}" y="{y-4}" width="8" height="8" fill="{color}" '
        f'transform="rotate(45 {cx} {y})" opacity="0.75">'
        f'<animate attributeName="opacity" values="0.5;0.95;0.5" dur="3.4s" repeatCount="indefinite"/>'
        f'</rect></g>'
    )


# --------------------------------------------------------------------- hero

def build_hero_svg(cfg):
    W, H = cfg["width"], cfg["height"]
    cormorant = b64_font("cormorant-garamond-600.woff2")
    dmmono = b64_font("dm-mono-500.woff2")
    rng = random.Random(cfg["seed"])

    stops = "".join(f'<stop offset="{p}%" stop-color="{c}"/>' for p, c in cfg["bg_stops"])

    neb_defs, neb_uses = gen_nebula(cfg)

    far = gen_star_layer(rng, cfg["star_counts"]["far"], (0.4, 0.8), (0.30, 0.48), (3.0, 6.0), cfg["muted"], W, H)
    mid = gen_star_layer(rng, cfg["star_counts"]["mid"], (0.7, 1.3), (0.45, 0.72), (2.4, 4.4), cfg["sparkle"], W, H)
    near = gen_star_layer(rng, cfg["star_counts"]["near"], (1.1, 1.8), (0.72, 0.95), (1.8, 3.2), "#ffffff", W, H)
    sparkles = gen_sparkles(rng, cfg["sparkle_count"], cfg["primary"], W, H)
    embers = gen_embers(rng, 16, [cfg["primary"], cfg["secondary"], cfg["sparkle"]], W, H, y_lo_frac=0.55)

    comet_defs = []
    comet_bodies = []
    for (x1, y1, x2, y2, dur, begin, color) in [
        (40, 55, 580, 128, 11.0, 0.6, "#fff0e8"),
        (1462, 252, 928, 188, 14.0, 6.2, "#ffcfd6"),
        (200, 268, 720, 40, 16.5, 10.4, cfg["sparkle"]),
    ]:
        d, b = gen_comet(x1, y1, x2, y2, dur, begin, color)
        comet_defs.append(d)
        comet_bodies.append(b)

    kintsugi = gen_kintsugi(cfg["primary"])
    constellation = gen_constellation(cfg["primary"])
    brackets = gen_corner_brackets(cfg["primary"], W, H)
    ornament = gen_divider_ornament(W / 2, 176, cfg["primary"], 280, 42)

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>
@font-face {{ font-family: 'Cormorant Garamond'; font-weight: 600; src: url(data:font/woff2;base64,{cormorant}) format('woff2'); }}
@font-face {{ font-family: 'DM Mono'; font-weight: 500; src: url(data:font/woff2;base64,{dmmono}) format('woff2'); }}
.name {{ font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 96px; letter-spacing: 4px; }}
.role {{ font-family: 'DM Mono', monospace; font-weight: 500; font-size: 19px; fill: {cfg["muted"]}; letter-spacing: 3px; }}
</style>
<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="0%">{stops}</linearGradient>
<radialGradient id="textWell" cx="50%" cy="50%" r="50%">
<stop offset="0%" stop-color="#000000" stop-opacity="0.42"/>
<stop offset="60%" stop-color="#000000" stop-opacity="0.20"/>
<stop offset="100%" stop-color="#000000" stop-opacity="0"/>
</radialGradient>
<radialGradient id="vignette" cx="50%" cy="50%" r="72%">
<stop offset="55%" stop-color="#000000" stop-opacity="0"/>
<stop offset="100%" stop-color="#000000" stop-opacity="0.4"/>
</radialGradient>
<linearGradient id="shimmerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{cfg["shimmer"]}" stop-opacity="0"/>
<stop offset="0%" stop-color="{cfg["shimmer"]}" stop-opacity="0.9">
<animate attributeName="offset" keyTimes="0;0.001;0.32;1" values="0%;0%;100%;100%" dur="6s" begin="1s" repeatCount="indefinite"/>
</stop>
<stop offset="100%" stop-color="{cfg["shimmer"]}" stop-opacity="0"/>
</linearGradient>
<filter id="softBlur" x="-40%" y="-40%" width="180%" height="180%">
<feGaussianBlur stdDeviation="34"/>
</filter>
<filter id="nameGlow" x="-25%" y="-120%" width="150%" height="340%">
<feGaussianBlur stdDeviation="6"/>
</filter>
{grain_filter("heroGrain", cfg["seed"])}
{neb_defs}
{"".join(comet_defs)}
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{neb_uses}
<ellipse cx="{W/2}" cy="168" rx="490" ry="132" fill="url(#textWell)"/>
<rect width="{W}" height="{H}" fill="url(#vignette)"/>
{kintsugi}
{constellation}
{brackets}
{far}
{mid}
{near}
{sparkles}
{embers}
{"".join(comet_bodies)}
{ornament}
<text x="50%" y="150" text-anchor="middle" class="name" fill="{cfg["primary"]}" filter="url(#nameGlow)" opacity="0.68">{esc(cfg["name"])}</text>
<text x="50%" y="150" text-anchor="middle" class="name" fill="{cfg["name_color"]}">{esc(cfg["name"])}</text>
<text x="50%" y="150" text-anchor="middle" class="name" fill="url(#shimmerGrad)">{esc(cfg["name"])}</text>
<text x="50%" y="206" text-anchor="middle" class="role">{esc(cfg["role"])}</text>
<rect width="{W}" height="{H}" filter="url(#heroGrain)" opacity="0.05"/>
</svg>'''


# ------------------------------------------------------------- wave banners

def wave_layer_path(w, h, base_y, amplitude, humps, crest_up, phase_offset=0.0):
    """A smooth multi-hump wave built from cubic beziers, filled solid
    either down to the bottom edge (crest_up=True, for a header banner
    whose wave sits near the top) or up to the top edge (crest_up=False,
    for a footer banner whose wave sits near the bottom)."""
    seg = w / humps
    d = f"M{-seg*0.5:.1f},{base_y:.1f}"
    for i in range(-1, humps + 1):
        x0 = i * seg
        x2 = x0 + seg
        up = ((i + (1 if phase_offset else 0)) % 2 == 0)
        dy = -amplitude if up else amplitude
        y_ctrl = base_y + dy
        d += f" C{x0+seg*0.25:.1f},{y_ctrl:.1f} {x0+seg*0.75:.1f},{y_ctrl:.1f} {x2:.1f},{base_y:.1f}"
    if crest_up:
        d += f" L{w+seg},{h} L{-seg},{h} Z"
    else:
        d += f" L{w+seg},0 L{-seg},0 Z"
    return d


def wave_crest_only(w, base_y, amplitude, humps, crest_up, phase_offset=0.0):
    """Same curve as wave_layer_path's top edge, without the fill-closing
    path — used to stroke just the crest line, not the filled body."""
    seg = w / humps
    d = f"M{-seg*0.5:.1f},{base_y:.1f}"
    for i in range(-1, humps + 1):
        x0 = i * seg
        x2 = x0 + seg
        up = ((i + (1 if phase_offset else 0)) % 2 == 0)
        dy = -amplitude if up else amplitude
        y_ctrl = base_y + dy
        d += f" C{x0+seg*0.25:.1f},{y_ctrl:.1f} {x0+seg*0.75:.1f},{y_ctrl:.1f} {x2:.1f},{base_y:.1f}"
    return d


def build_wave_banner_svg(w, h, stops, crest_up, star_count, accent, seed):
    """A compact section-transition banner: 2 layered wave bands in the
    page gradient plus a light scattering of static twinkle stars, so the
    banners read as thin slices of the same night sky as the hero rather
    than an unrelated decorative element.

    The fill alone is too close in luminance to GitHub's own dark-mode
    background to read as a distinct shape at only 40px tall — confirmed
    by rendering it and comparing against a real dark page background, not
    assumed — so the crest line itself is traced in a fading accent-color
    stroke, the same rim-light trick as the hero's divider rule, to give
    the wave a visible edge regardless of how the fill blends into the page."""
    rng = random.Random(seed)
    stop_str = "".join(f'<stop offset="{p}%" stop-color="{c}"/>' for p, c in stops)
    base_y = h * (0.58 if crest_up else 0.42)
    back = wave_layer_path(w, h, base_y, h * 0.30, 3, crest_up, phase_offset=0)
    front_base_y = base_y + (7 if crest_up else -7)
    front = wave_layer_path(w, h, front_base_y, h * 0.20, 4, crest_up, phase_offset=1)
    front_edge = wave_crest_only(w, front_base_y, h * 0.20, 4, crest_up, phase_offset=1)

    stars = []
    for _ in range(star_count):
        x = rng.uniform(10, w - 10)
        y = rng.uniform(4, h - 4)
        r = rng.uniform(0.5, 1.3)
        op = rng.uniform(0.3, 0.75)
        dur = rng.uniform(2.6, 5.0)
        delay = rng.uniform(0, dur)
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{accent}">'
            f'<animate attributeName="opacity" values="{op*0.2:.2f};{op:.2f};{op*0.2:.2f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/></circle>'
        )

    return f'''<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="waveBg" x1="0%" y1="0%" x2="100%" y2="0%">{stop_str}</linearGradient>
<linearGradient id="waveEdge" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{accent}" stop-opacity="0"/>
<stop offset="50%" stop-color="{accent}" stop-opacity="0.55"/>
<stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
</linearGradient>
{grain_filter("waveGrain", seed)}
</defs>
<path d="{back}" fill="url(#waveBg)" opacity="0.6"/>
<path d="{front}" fill="url(#waveBg)"/>
<path d="{front_edge}" fill="none" stroke="url(#waveEdge)" stroke-width="1"/>
{"".join(stars)}
<rect width="{w}" height="{h}" filter="url(#waveGrain)" opacity="0.05"/>
</svg>'''


def build_wave_final_svg(cfg):
    """The page's closing bookend (replaces the venom footer) — richer than
    the thin transition banners: three horizon layers, a denser twinkling
    field, and a thin center ornament echoing the hero's divider rule, so
    the page closes on the same visual language it opened with."""
    W, H = 1500, 160
    primary, secondary = cfg["primary"], cfg["secondary"]
    stops = cfg["bg_stops"]
    stop_str = "".join(f'<stop offset="{p}%" stop-color="{c}"/>' for p, c in stops)
    rng = random.Random(cfg["seed"] + 7)

    layers = []
    specs = [(0.30, H * 0.82, 4, 0.35), (0.20, H * 0.64, 5, 0.6), (0.12, H * 0.46, 6, 1.0)]
    for amp_frac, base_y, humps, op in specs:
        path = wave_layer_path(W, H, base_y, H * amp_frac, humps, False, phase_offset=0)
        layers.append(f'<path d="{path}" fill="url(#waveBgFinal)" opacity="{op:.2f}"/>')
    top_amp, top_base_y, top_humps, _ = specs[-1]
    front_edge = wave_crest_only(W, top_base_y, H * top_amp, top_humps, False, phase_offset=0)

    stars = []
    for _ in range(26):
        x = rng.uniform(10, W - 10)
        y = rng.uniform(4, H * 0.40)
        r = rng.uniform(0.5, 1.5)
        op = rng.uniform(0.35, 0.8)
        dur = rng.uniform(2.4, 5.2)
        delay = rng.uniform(0, dur)
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{primary}">'
            f'<animate attributeName="opacity" values="{op*0.18:.2f};{op:.2f};{op*0.18:.2f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/></circle>'
        )

    ornament = gen_divider_ornament(W / 2, H * 0.20, primary, 220, 36)
    embers = gen_embers(rng, 10, [primary, secondary, cfg["sparkle"]], W, H, y_lo_frac=0.6)

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="waveBgFinal" x1="0%" y1="0%" x2="100%" y2="0%">{stop_str}</linearGradient>
<linearGradient id="waveEdgeFinal" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{primary}" stop-opacity="0"/>
<stop offset="50%" stop-color="{primary}" stop-opacity="0.5"/>
<stop offset="100%" stop-color="{primary}" stop-opacity="0"/>
</linearGradient>
{grain_filter("waveFinalGrain", cfg["seed"])}
</defs>
<rect width="{W}" height="{H}" fill="{cfg["bg_stops"][0][1]}"/>
{"".join(stars)}
{"".join(layers)}
<path d="{front_edge}" fill="none" stroke="url(#waveEdgeFinal)" stroke-width="1.2"/>
{embers}
{ornament}
<rect width="{W}" height="{H}" filter="url(#waveFinalGrain)" opacity="0.05"/>
</svg>'''


# --------------------------------------------------------------------- seals

def build_seal_svg(glyph, color, seed):
    """A small emblem for a work-section project title — corner brackets
    (reusing the exact hero/stats bracket generator, just on a 64px
    canvas), a pulsing ring, and the project's own existing glyph, glowing.
    The work section was plain text/badges across every pass through
    Pass 5; this is its first generated visual."""
    W = H = 64
    cx = cy = 32
    ring_r = 21
    rng = random.Random(seed)
    ticks = []
    for i in range(14):
        ang = (i / 14) * 2 * math.pi + rng.uniform(-0.05, 0.05)
        x1, y1 = cx + math.cos(ang) * (ring_r - 2), cy + math.sin(ang) * (ring_r - 2)
        x2, y2 = cx + math.cos(ang) * (ring_r + 2), cy + math.sin(ang) * (ring_r + 2)
        ticks.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                      f'stroke="{color}" stroke-width="0.8" opacity="0.3"/>')
    brackets = gen_corner_brackets(color, W, H)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<filter id="sealGlow" x="-60%" y="-60%" width="220%" height="220%">
<feGaussianBlur stdDeviation="2.6"/>
</filter>
<radialGradient id="sealBg" cx="50%" cy="50%" r="50%">
<stop offset="0%" stop-color="{color}" stop-opacity="0.18"/>
<stop offset="100%" stop-color="{color}" stop-opacity="0"/>
</radialGradient>
</defs>
<circle cx="{cx}" cy="{cy}" r="27" fill="url(#sealBg)"/>
{brackets}
<circle cx="{cx}" cy="{cy}" r="{ring_r}" fill="none" stroke="{color}" stroke-width="1" opacity="0.35">
<animate attributeName="opacity" values="0.22;0.5;0.22" dur="5s" repeatCount="indefinite"/>
</circle>
{"".join(ticks)}
<text x="{cx}" y="{cy+8}" text-anchor="middle" font-family="'Segoe UI Symbol',sans-serif" '''\
           f'''font-size="24" fill="{color}" filter="url(#sealGlow)" opacity="0.65">{glyph}</text>
<text x="{cx}" y="{cy+8}" text-anchor="middle" font-family="'Segoe UI Symbol',sans-serif" '''\
           f'''font-size="24" fill="{color}">{glyph}</text>
</svg>'''


# ----------------------------------------------------------------- dividers

def build_divider_svg(color):
    W, H, cy = 1400, 24, 12
    ornament = gen_divider_ornament(W / 2, cy, color, (W - 120) / 2, 40)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
{ornament}
</svg>'''


# ------------------------------------------------------------- panel headers

def build_panel_header_svg(title, subtitle, cfg):
    """A Steam-profile-style showcase header on a pure-black canvas."""
    W, H = 1500, 56
    primary = cfg["primary"]
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="panelBg" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#671515"/><stop offset="90%" stop-color="#8c1616"/><stop offset="100%" stop-color="#2a0505"/>
</linearGradient>
<linearGradient id="panelEdge" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{primary}" stop-opacity="0.9"/><stop offset="72%" stop-color="{primary}" stop-opacity="0.24"/><stop offset="100%" stop-color="{primary}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="panelSweep" gradientUnits="userSpaceOnUse" x1="-260" y1="0" x2="0" y2="0">
<stop offset="0%" stop-color="#ffffff" stop-opacity="0"/><stop offset="50%" stop-color="#ffffff" stop-opacity="0.16"/><stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
<animate attributeName="x1" values="-260;1500" dur="8s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;1760" dur="8s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="#000000"/>
<rect x="14" y="7" width="1472" height="42" rx="5" fill="#000000" opacity="0.78"/>
<rect x="18" y="9" width="1464" height="38" rx="4" fill="url(#panelBg)" opacity="0.94"/>
<rect x="18" y="9" width="5" height="38" rx="2" fill="{primary}"/>
<rect x="18" y="9" width="1464" height="38" rx="4" fill="url(#panelSweep)"/>
<rect x="18" y="46" width="1464" height="1" fill="url(#panelEdge)"/>
<text x="44" y="34" fill="#ffffff" font-family="'Segoe UI',Arial,sans-serif" font-size="17" font-weight="300" letter-spacing="3">{esc(title)}</text>
<text x="1456" y="33" text-anchor="end" fill="#c4c4c4" font-family="'Segoe UI',Arial,sans-serif" font-size="12" font-weight="400" letter-spacing="2">{esc(subtitle)}</text>
</svg>'''


# ------------------------------------------------------------------ tagline

def build_tagline_svg(cfg):
    """A self-hosted typewriter effect matching readme-typing-svg's look:
    each line clip-reveals left-to-right, holds, deletes, then the next
    line begins. Widths are pre-measured in an actual browser against the
    real embedded font (scripts/measure_tagline.py) rather than guessed
    from monospace-advance math, so the clip edge lines up with the glyphs
    exactly instead of clipping mid-character."""
    W, H = cfg["tagline"]["width"], cfg["tagline"]["height"]
    cx = W / 2
    type_ms = cfg["tagline"]["type_ms_per_char"]
    delete_ms = cfg["tagline"]["delete_ms_per_char"]
    hold_ms = cfg["tagline"]["hold_ms"]
    gap_ms = cfg["tagline"]["gap_ms"]
    dmmono = b64_font("dm-mono-500.woff2")

    segments = []
    t = 0.0
    for text, w in cfg["tagline"]["lines"]:
        left = cx - w / 2
        type_dur = len(text) * type_ms
        delete_dur = len(text) * delete_ms
        seg = {
            "text": text, "w": w, "left": left, "t_start": t,
            "t_type_end": t + type_dur,
            "t_hold_end": t + type_dur + hold_ms,
            "t_delete_end": t + type_dur + hold_ms + delete_dur,
        }
        t = seg["t_delete_end"] + gap_ms
        segments.append(seg)
    total = t

    y_text = H / 2 + 5
    y_clip_top = H / 2 - 12
    clip_h = 24

    clip_defs, texts = [], []
    for i, seg in enumerate(segments):
        kt = [0, seg["t_start"] / total, seg["t_type_end"] / total,
              seg["t_hold_end"] / total, seg["t_delete_end"] / total, 1]
        vals = [0, 0, seg["w"], seg["w"], 0, 0]
        kt_str = ";".join(f"{k:.5f}" for k in kt)
        vals_str = ";".join(f"{v:.2f}" for v in vals)
        clip_defs.append(
            f'<clipPath id="tclip{i}"><rect x="{seg["left"]:.2f}" y="{y_clip_top:.1f}" '
            f'width="0" height="{clip_h}">'
            f'<animate attributeName="width" keyTimes="{kt_str}" values="{vals_str}" '
            f'dur="{total/1000:.3f}s" repeatCount="indefinite"/></rect></clipPath>'
        )
        texts.append(
            f'<text x="{seg["left"]:.2f}" y="{y_text:.1f}" clip-path="url(#tclip{i})" '
            f'font-family="DM Mono" font-weight="500" font-size="14" letter-spacing="0.5" '
            f'fill="{cfg["muted"]}">{esc(seg["text"])}</text>'
        )

    cur_kt, cur_vals = [], []
    for i, seg in enumerate(segments):
        cur_kt += [seg["t_start"] / total, seg["t_type_end"] / total,
                   seg["t_hold_end"] / total, seg["t_delete_end"] / total]
        cur_vals += [seg["left"], seg["left"] + seg["w"], seg["left"] + seg["w"], seg["left"]]
        next_start = segments[i + 1]["t_start"] if i + 1 < len(segments) else total
        cur_kt.append(next_start / total)
        cur_vals.append(seg["left"])
    cur_kt_str = ";".join(f"{k:.5f}" for k in cur_kt)
    cur_vals_str = ";".join(f"{v:.2f}" for v in cur_vals)

    cursor = (
        f'<g>'
        f'<rect y="{y_clip_top+1:.1f}" width="4" height="{clip_h-2}" fill="{cfg["primary"]}" '
        f'opacity="0.35" filter="url(#cursorGlow)">'
        f'<animate attributeName="x" keyTimes="{cur_kt_str}" values="{cur_vals_str}" '
        f'dur="{total/1000:.3f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" keyTimes="0;0.12;0.3;0.46;0.62;0.7;1" '
        f'values="0.35;0.28;0.35;0.08;0;0;0.35" dur="1.1s" repeatCount="indefinite"/>'
        f'</rect>'
        f'<rect y="{y_clip_top+2:.1f}" width="1.6" height="{clip_h-4}" fill="{cfg["primary"]}">'
        f'<animate attributeName="x" keyTimes="{cur_kt_str}" values="{cur_vals_str}" '
        f'dur="{total/1000:.3f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" keyTimes="0;0.12;0.3;0.46;0.62;0.7;1" '
        f'values="1;0.88;1;0.25;0;0;1" dur="1.1s" repeatCount="indefinite"/>'
        f'</rect>'
        f'</g>'
    )

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>
@font-face {{ font-family: 'DM Mono'; font-weight: 500; src: url(data:font/woff2;base64,{dmmono}) format('woff2'); }}
</style>
<filter id="cursorGlow" x="-300%" y="-100%" width="700%" height="300%">
<feGaussianBlur stdDeviation="2.4"/>
</filter>
{grain_filter("taglineGrain", cfg["seed"])}
{"".join(clip_defs)}
</defs>
{"".join(texts)}
{cursor}
<rect width="{W}" height="{H}" filter="url(#taglineGrain)" opacity="0.04"/>
</svg>'''


# ======================================================= cinematic experience

def experience_font_defs():
    cormorant = b64_font("cormorant-garamond-600.woff2")
    dmmono = b64_font("dm-mono-500.woff2")
    return (
        "<style>"
        f"@font-face {{ font-family:'Cormorant Garamond'; font-weight:600; "
        f"src:url(data:font/woff2;base64,{cormorant}) format('woff2'); }}"
        f"@font-face {{ font-family:'DM Mono'; font-weight:500; "
        f"src:url(data:font/woff2;base64,{dmmono}) format('woff2'); }}"
        ".serif{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600}"
        ".mono{font-family:'DM Mono','Courier New',monospace;font-weight:500}"
        "</style>"
    )


def build_cinematic_hero_svg(cfg):
    """A self-contained title sequence: original raster key art plus a
    GitHub-safe animated HUD, scan pass, signal traces, and identity lockup."""
    W, H = 1500, 620
    art = asset_data_uri("hero-keyart-v2.png", "image/png")
    fonts = experience_font_defs()
    rng = random.Random(cfg["seed"] + 900)

    embers = []
    for i in range(28):
        x = rng.uniform(20, W - 20)
        y = rng.uniform(H * 0.45, H + 30)
        rise = rng.uniform(70, 220)
        drift = rng.uniform(-28, 28)
        dur = rng.uniform(4.5, 10.5)
        delay = rng.uniform(0, dur)
        embers.append(
            f'<circle r="{rng.uniform(0.8, 2.1):.2f}" fill="{cfg["sparkle"]}">'
            f'<animate attributeName="opacity" values="0;0.8;0.25;0" '
            f'keyTimes="0;.12;.72;1" dur="{dur:.2f}s" begin="-{delay:.2f}s" '
            f'repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{x:.1f},{y:.1f};{x+drift:.1f},{y-rise:.1f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            "</circle>"
        )

    telemetry = []
    for i, width in enumerate((420, 350, 280)):
        y = 72 + i * 18
        telemetry.append(
            f'<path d="M70 {y} H{70+width}" stroke="#e84b4b" stroke-width="1" '
            f'opacity="{0.34-i*0.07:.2f}" stroke-dasharray="5 12">'
            f'<animate attributeName="stroke-dashoffset" values="0;-68" '
            f'dur="{4.0+i*1.4:.1f}s" repeatCount="indefinite"/></path>'
        )

    chips = [
        (74, "SYSTEMS", "RUST"),
        (250, "PRODUCT", "TYPESCRIPT"),
        (482, "APPLIED", "GENAI + AWS"),
    ]
    chip_svg = []
    for x, label, value in chips:
        width = 160 if x == 74 else 216 if x == 250 else 220
        chip_svg.append(
            f'<g transform="translate({x},520)">'
            f'<rect width="{width}" height="48" rx="3" fill="#050505" '
            f'stroke="#671515" stroke-width="1"/>'
            f'<rect width="4" height="48" rx="2" fill="#e84b4b"/>'
            f'<text x="18" y="18" class="mono" font-size="10" fill="#8d7777" '
            f'letter-spacing="2">{label}</text>'
            f'<text x="18" y="36" class="mono" font-size="14" fill="#f5eaea" '
            f'letter-spacing="1">{value}</text></g>'
        )

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{fonts}
<clipPath id="heroClip"><rect x="10" y="10" width="1480" height="600" rx="8"/></clipPath>
<linearGradient id="heroShade" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#000" stop-opacity=".98"/>
<stop offset="37%" stop-color="#000" stop-opacity=".88"/>
<stop offset="61%" stop-color="#000" stop-opacity=".18"/>
<stop offset="100%" stop-color="#000" stop-opacity=".05"/>
</linearGradient>
<linearGradient id="heroBottom" x1="0%" y1="0%" x2="0%" y2="100%">
<stop offset="46%" stop-color="#000" stop-opacity="0"/>
<stop offset="100%" stop-color="#000" stop-opacity=".9"/>
</linearGradient>
<linearGradient id="scan" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#e84b4b" stop-opacity="0"/>
<stop offset="50%" stop-color="#ff8a7f" stop-opacity=".34"/>
<stop offset="100%" stop-color="#e84b4b" stop-opacity="0"/>
</linearGradient>
<pattern id="scanlines" width="8" height="8" patternUnits="userSpaceOnUse">
<rect width="8" height="1" fill="#fff" opacity=".025"/>
</pattern>
<pattern id="microgrid" width="32" height="32" patternUnits="userSpaceOnUse">
<path d="M32 0H0V32" fill="none" stroke="#e84b4b" stroke-width=".45" opacity=".08"/>
</pattern>
<filter id="heroGlow" x="-40%" y="-80%" width="180%" height="260%">
<feGaussianBlur stdDeviation="7"/>
</filter>
<filter id="softHero" x="-30%" y="-30%" width="160%" height="160%">
<feGaussianBlur stdDeviation="18"/>
</filter>
{grain_filter("experienceGrain", cfg["seed"] + 900)}
</defs>
<rect width="{W}" height="{H}" rx="10" fill="#000"/>
<g clip-path="url(#heroClip)">
<image href="{art}" x="4" y="4" width="1492" height="612" preserveAspectRatio="xMidYMid slice">
<animate attributeName="x" values="4;-8;4" dur="26s" repeatCount="indefinite"/>
<animate attributeName="y" values="4;-3;4" dur="26s" repeatCount="indefinite"/>
<animate attributeName="width" values="1492;1516;1492" dur="26s" repeatCount="indefinite"/>
<animate attributeName="height" values="612;626;612" dur="26s" repeatCount="indefinite"/>
</image>
<rect x="10" y="10" width="1480" height="600" fill="url(#heroShade)"/>
<rect x="10" y="10" width="1480" height="600" fill="url(#heroBottom)"/>
<rect x="10" y="10" width="1480" height="600" fill="url(#microgrid)"/>
<rect x="10" y="10" width="1480" height="600" fill="url(#scanlines)"/>
<rect x="-220" y="10" width="180" height="600" fill="url(#scan)" opacity=".72">
<animate attributeName="x" values="-220;1540" dur="8s" repeatCount="indefinite"/>
</rect>
<ellipse cx="1120" cy="220" rx="250" ry="250" fill="none" stroke="#e84b4b"
 stroke-width="1" opacity=".16" stroke-dasharray="12 20">
<animateTransform attributeName="transform" type="rotate" from="0 1120 220"
 to="360 1120 220" dur="38s" repeatCount="indefinite"/>
</ellipse>
<ellipse cx="1120" cy="220" rx="276" ry="276" fill="none" stroke="#ff8a7f"
 stroke-width=".7" opacity=".1" stroke-dasharray="2 16">
<animateTransform attributeName="transform" type="rotate" from="360 1120 220"
 to="0 1120 220" dur="28s" repeatCount="indefinite"/>
</ellipse>
{"".join(embers)}
</g>
<rect x="10" y="10" width="1480" height="600" rx="8" fill="none" stroke="#3b0b0b"/>
<rect x="22" y="22" width="1456" height="576" rx="5" fill="none" stroke="#e84b4b"
 stroke-width=".7" opacity=".18" stroke-dasharray="44 14"/>
{"".join(telemetry)}
<circle cx="74" cy="38" r="4" fill="#e84b4b">
<animate attributeName="opacity" values=".3;1;.3" dur="1.6s" repeatCount="indefinite"/>
</circle>
<text x="90" y="43" class="mono" font-size="11" fill="#c4c4c4" letter-spacing="2.6">
AYR // OPERATOR ONLINE
</text>
<text x="1426" y="43" text-anchor="end" class="mono" font-size="10" fill="#8d7777"
 letter-spacing="2">INDIA · UTC+05:30 · BUILD 2026</text>
<text x="72" y="154" class="mono" font-size="12" fill="#e84b4b" letter-spacing="4">
SYSTEMS ENGINEER / PRODUCT BUILDER
</text>
<text x="68" y="270" class="serif" font-size="116" fill="#e84b4b" opacity=".55"
 filter="url(#heroGlow)">AYUSH</text>
<text x="68" y="270" class="serif" font-size="116" fill="#f8eeee" letter-spacing="4">AYUSH</text>
<text x="68" y="370" class="serif" font-size="116" fill="#f8eeee" letter-spacing="4">ROY</text>
<g opacity=".48" transform="translate(3,0)">
<text x="68" y="370" class="serif" font-size="116" fill="#e84b4b" letter-spacing="4">
ROY
<animate attributeName="opacity" values="0;0;.52;0;0" keyTimes="0;.71;.715;.73;1"
 dur="6.4s" repeatCount="indefinite"/>
</text>
</g>
<rect x="72" y="400" width="524" height="2" fill="#671515"/>
<rect x="72" y="400" width="120" height="2" fill="#ff8a7f">
<animate attributeName="x" values="72;476;72" dur="5s" repeatCount="indefinite"/>
</rect>
<text x="72" y="440" class="mono" font-size="18" fill="#d6c8c8" letter-spacing="1.4">
BUILDING THE SOFTWARE LAYER
</text>
<text x="72" y="470" class="mono" font-size="18" fill="#d6c8c8" letter-spacing="1.4">
FOR THE PHYSICAL WORLD.
</text>
{"".join(chip_svg)}
<g transform="translate(1392,545)">
<circle r="34" fill="#000" opacity=".65" stroke="#e84b4b" stroke-width="1"/>
<circle r="24" fill="none" stroke="#e84b4b" stroke-width="1" stroke-dasharray="4 8">
<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="7s"
 repeatCount="indefinite"/>
</circle>
<circle r="4" fill="#ff8a7f">
<animate attributeName="r" values="3;6;3" dur="2s" repeatCount="indefinite"/>
</circle>
</g>
<rect width="{W}" height="{H}" filter="url(#experienceGrain)" opacity=".035"/>
</svg>'''


def build_nav_button_svg(label, code, glyph, cfg, seed):
    W, H = 350, 72
    rng = random.Random(seed)
    ticks = "".join(
        f'<rect x="{18+i*17}" y="60" width="{rng.randint(5,13)}" height="1" '
        f'fill="#e84b4b" opacity="{rng.uniform(.18,.65):.2f}"/>'
        for i in range(18)
    )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="navBg" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#050505"/><stop offset="72%" stop-color="#130303"/>
<stop offset="100%" stop-color="#300707"/>
</linearGradient>
<linearGradient id="navSweep" gradientUnits="userSpaceOnUse" x1="-120" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"
 stop-opacity=".14"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-120;350" dur="6s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;470" dur="6s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<rect x="1" y="1" width="348" height="70" rx="4" fill="url(#navBg)" stroke="#671515"/>
<rect x="1" y="1" width="5" height="70" rx="2" fill="#e84b4b"/>
<rect x="1" y="1" width="348" height="70" rx="4" fill="url(#navSweep)"/>
<text x="24" y="44" class="mono" font-size="25" fill="#e84b4b">{esc(glyph)}</text>
<text x="68" y="31" class="mono" font-size="13" fill="#f5eaea" letter-spacing="2">{esc(label)}</text>
<text x="68" y="49" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">{esc(code)}</text>
<text x="326" y="40" text-anchor="end" class="mono" font-size="19" fill="#e84b4b">→</text>
{ticks}
</svg>'''


def build_signal_strip_svg(cfg):
    W, H = 1500, 52
    phrase = "GEOSPATIAL  ·  REALTIME  ·  COMPUTER VISION  ·  SYSTEMS  ·  3D  ·  APPLIED AI  ·  "
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="signalFade" x1="0%" x2="100%">
<stop offset="0%" stop-color="#000"/><stop offset="8%" stop-color="#000" stop-opacity="0"/>
<stop offset="92%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000"/>
</linearGradient>
<clipPath id="signalClip"><rect x="170" y="0" width="1330" height="52"/></clipPath>
</defs>
<rect width="{W}" height="{H}" fill="#030303"/>
<rect width="{W}" height="1" fill="#671515"/>
<rect y="51" width="{W}" height="1" fill="#2a0505"/>
<rect x="18" y="12" width="132" height="28" rx="3" fill="#671515"/>
<circle cx="34" cy="26" r="4" fill="#ff8a7f">
<animate attributeName="opacity" values=".2;1;.2" dur="1.3s" repeatCount="indefinite"/>
</circle>
<text x="48" y="30" class="mono" font-size="10" fill="#fff" letter-spacing="2">LIVE SIGNAL</text>
<g clip-path="url(#signalClip)">
<text y="32" class="mono" font-size="13" fill="#bcaeae" letter-spacing="3">
<tspan x="170">{phrase}{phrase}</tspan>
<animateTransform attributeName="transform" type="translate" values="0 0;-1120 0"
 dur="18s" repeatCount="indefinite"/>
</text>
</g>
<rect x="150" width="1350" height="52" fill="url(#signalFade)" pointer-events="none"/>
</svg>'''


def build_section_header_svg(index, title, subtitle, cfg):
    W, H = 1500, 96
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="sectionRail" x1="0%" x2="100%">
<stop offset="0%" stop-color="#e84b4b"/><stop offset="58%" stop-color="#671515"/>
<stop offset="100%" stop-color="#000" stop-opacity="0"/>
</linearGradient>
<linearGradient id="sectionSweep" gradientUnits="userSpaceOnUse" x1="-180" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"
 stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-180;1500" dur="8s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;1680" dur="8s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="#000"/>
<text x="20" y="78" class="serif" font-size="86" fill="#671515" opacity=".34">{esc(index)}</text>
<rect x="112" y="16" width="1370" height="64" rx="4" fill="#080202" stroke="#310808"/>
<rect x="112" y="16" width="8" height="64" rx="2" fill="#e84b4b"/>
<rect x="120" y="16" width="1362" height="64" fill="url(#sectionSweep)"/>
<text x="148" y="49" class="mono" font-size="18" fill="#f5eaea" letter-spacing="4">{esc(title)}</text>
<text x="148" y="67" class="mono" font-size="9" fill="#9b8585" letter-spacing="2.2">{esc(subtitle)}</text>
<rect x="112" y="79" width="1370" height="1" fill="url(#sectionRail)"/>
<circle cx="1442" cy="48" r="15" fill="none" stroke="#e84b4b" opacity=".42"
 stroke-dasharray="3 6">
<animateTransform attributeName="transform" type="rotate" from="0 1442 48"
 to="360 1442 48" dur="6s" repeatCount="indefinite"/>
</circle>
<circle cx="1442" cy="48" r="3" fill="#ff8a7f">
<animate attributeName="opacity" values=".2;1;.2" dur="1.4s" repeatCount="indefinite"/>
</circle>
</svg>'''


def build_identity_console_svg(cfg):
    W, H = 1500, 360
    nodes = [
        (760, 92, "GEOSPATIAL"), (985, 132, "REALTIME"),
        (930, 274, "VISION"), (680, 252, "SYSTEMS"),
    ]
    links = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)]
    link_svg = []
    for i, (a, b) in enumerate(links):
        x1, y1, _ = nodes[a]
        x2, y2, _ = nodes[b]
        link_svg.append(
            f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#671515" stroke-width="1.2" '
            f'opacity=".55" stroke-dasharray="5 10">'
            f'<animate attributeName="stroke-dashoffset" values="0;-60" dur="{4+i*.7:.1f}s" '
            f'repeatCount="indefinite"/></path>'
        )
    node_svg = []
    for i, (x, y, label) in enumerate(nodes):
        node_svg.append(
            f'<g><circle cx="{x}" cy="{y}" r="28" fill="#080202" stroke="#e84b4b" '
            f'stroke-width="1"/><circle cx="{x}" cy="{y}" r="20" fill="none" '
            f'stroke="#e84b4b" opacity=".45" stroke-dasharray="3 5">'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {x} {y}" '
            f'to="360 {x} {y}" dur="{8+i*2}s" repeatCount="indefinite"/></circle>'
            f'<circle cx="{x}" cy="{y}" r="4" fill="#ff8a7f">'
            f'<animate attributeName="r" values="3;6;3" dur="{1.8+i*.3}s" '
            f'repeatCount="indefinite"/></circle>'
            f'<text x="{x}" y="{y+48}" text-anchor="middle" class="mono" font-size="9" '
            f'fill="#c4c4c4" letter-spacing="1.5">{label}</text></g>'
        )

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<pattern id="consoleGrid" width="28" height="28" patternUnits="userSpaceOnUse">
<path d="M28 0H0V28" fill="none" stroke="#671515" stroke-width=".5" opacity=".12"/>
</pattern>
<radialGradient id="coreGlow">
<stop offset="0" stop-color="#e84b4b" stop-opacity=".25"/>
<stop offset="1" stop-color="#e84b4b" stop-opacity="0"/>
</radialGradient>
</defs>
<rect x="1" y="1" width="1498" height="358" rx="7" fill="#030303" stroke="#2d0808"/>
<rect x="1" y="1" width="1498" height="358" rx="7" fill="url(#consoleGrid)"/>
<path d="M560 20V340M1080 20V340" stroke="#310808"/>
<text x="34" y="48" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">
OPERATOR MANIFEST
</text>
<text x="34" y="93" class="serif" font-size="35" fill="#f5eaea">I build systems where</text>
<text x="34" y="132" class="serif" font-size="35" fill="#f5eaea">software meets reality.</text>
<rect x="34" y="154" width="440" height="1" fill="#671515"/>
<text x="34" y="188" class="mono" font-size="13" fill="#a99494">
<tspan x="34" dy="0">Geospatial solar simulation.</tspan>
<tspan x="34" dy="25">Realtime energy telemetry.</tspan>
<tspan x="34" dy="25">Computer vision pipelines.</tspan>
<tspan x="34" dy="25">Browser-native 3D products.</tspan>
</text>
<text x="34" y="319" class="mono" font-size="10" fill="#e84b4b" letter-spacing="2">
THE DOMAIN CHANGES. THE STANDARD DOESN'T.
</text>
<circle cx="835" cy="180" r="165" fill="url(#coreGlow)"/>
{"".join(link_svg)}
{"".join(node_svg)}
<g>
<circle cx="835" cy="180" r="50" fill="#050101" stroke="#e84b4b" stroke-width="1.4"/>
<circle cx="835" cy="180" r="38" fill="none" stroke="#ff8a7f" opacity=".35"
 stroke-dasharray="6 9">
<animateTransform attributeName="transform" type="rotate" from="0 835 180"
 to="-360 835 180" dur="10s" repeatCount="indefinite"/>
</circle>
<text x="835" y="176" text-anchor="middle" class="mono" font-size="11" fill="#f5eaea"
 letter-spacing="2">AYR</text>
<text x="835" y="194" text-anchor="middle" class="mono" font-size="8" fill="#e84b4b"
 letter-spacing="1">CORE</text>
</g>
<text x="1118" y="48" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">
CURRENT STATE
</text>
<text x="1118" y="93" class="mono" font-size="13" fill="#8d7777">ROLE</text>
<text x="1118" y="116" class="mono" font-size="17" fill="#f5eaea">FULL-STACK / SYSTEMS</text>
<text x="1118" y="158" class="mono" font-size="13" fill="#8d7777">LOCATION</text>
<text x="1118" y="181" class="mono" font-size="17" fill="#f5eaea">INDIA · IST</text>
<text x="1118" y="223" class="mono" font-size="13" fill="#8d7777">SIGNAL</text>
<text x="1118" y="246" class="mono" font-size="17" fill="#f5eaea">OPEN TO BUILD</text>
<rect x="1118" y="274" width="310" height="42" rx="3" fill="#130303" stroke="#671515"/>
<circle cx="1140" cy="295" r="5" fill="#e84b4b">
<animate attributeName="opacity" values=".2;1;.2" dur="1.2s" repeatCount="indefinite"/>
</circle>
<text x="1156" y="300" class="mono" font-size="11" fill="#d7caca" letter-spacing="1.5">
BUILDING / LEARNING / SHIPPING
</text>
</svg>'''


def build_operator_gateway_svg(cfg):
    """A full-width `<summary>` surface for the profile's optional deep layer.

    GitHub strips JavaScript but preserves native details/summary controls and
    SMIL inside SVG images, so the entire gateway remains interactive there.
    """
    W, H = 1500, 196
    chevrons = "".join(
        f'<path d="M{x} 82l18 16-18 16" fill="none" stroke="#e84b4b" '
        f'stroke-width="2" opacity="{.22 + i * .08:.2f}">'
        f'<animate attributeName="opacity" values=".12;.9;.12" dur="2.4s" '
        f'begin="-{i * .22:.2f}s" repeatCount="indefinite"/></path>'
        for i, x in enumerate(range(1000, 1136, 34))
    )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="gatewayBg" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0" stop-color="#020202"/><stop offset=".5" stop-color="#100202"/>
<stop offset="1" stop-color="#020202"/>
</linearGradient>
<linearGradient id="gatewayRail" x1="0%" x2="100%">
<stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset=".18" stop-color="#671515"/>
<stop offset=".5" stop-color="#ff8a7f"/><stop offset=".82" stop-color="#671515"/>
<stop offset="1" stop-color="#000" stop-opacity="0"/>
</linearGradient>
<linearGradient id="gatewaySweep" gradientUnits="userSpaceOnUse" x1="-260" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#ff8a7f"
 stop-opacity=".2"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-260;1500" dur="7s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;1760" dur="7s" repeatCount="indefinite"/>
</linearGradient>
<pattern id="gatewayGrid" width="26" height="26" patternUnits="userSpaceOnUse">
<path d="M26 0H0V26" fill="none" stroke="#e84b4b" stroke-width=".45" opacity=".1"/>
</pattern>
<filter id="gatewayGlow" x="-40%" y="-80%" width="180%" height="260%">
<feGaussianBlur stdDeviation="8"/>
</filter>
</defs>
<rect x="1" y="1" width="1498" height="194" rx="7" fill="url(#gatewayBg)" stroke="#4b0e0e"/>
<rect x="1" y="1" width="1498" height="194" rx="7" fill="url(#gatewayGrid)"/>
<rect x="1" y="1" width="1498" height="194" rx="7" fill="url(#gatewaySweep)"/>
<path d="M20 22H214L238 46H1262L1286 22H1480" fill="none" stroke="#671515"/>
<path d="M20 174H214L238 150H1262L1286 174H1480" fill="none" stroke="#671515"/>
<rect x="258" y="30" width="984" height="136" rx="4" fill="#030303" opacity=".72" stroke="#310808"/>
<rect x="258" y="30" width="6" height="136" rx="3" fill="#e84b4b"/>
<rect x="258" y="30" width="984" height="1.5" fill="url(#gatewayRail)"/>
<rect x="258" y="164" width="984" height="1.5" fill="url(#gatewayRail)"/>
<text x="42" y="55" class="mono" font-size="9" fill="#8d7777" letter-spacing="2.5">LAYER // 00</text>
<text x="42" y="86" class="mono" font-size="13" fill="#e84b4b" letter-spacing="2">RESTRICTED</text>
<text x="42" y="110" class="mono" font-size="13" fill="#e84b4b" letter-spacing="2">SIGNAL</text>
<circle cx="44" cy="143" r="5" fill="#e84b4b">
<animate attributeName="opacity" values=".2;1;.2" dur="1.1s" repeatCount="indefinite"/>
</circle>
<text x="60" y="147" class="mono" font-size="9" fill="#a99494" letter-spacing="1.4">READY TO BREACH</text>
<text x="750" y="83" text-anchor="middle" class="serif" font-size="45" fill="#e84b4b"
 opacity=".38" filter="url(#gatewayGlow)">INITIATE OPERATOR MODE</text>
<text x="750" y="83" text-anchor="middle" class="serif" font-size="45" fill="#f5eaea"
 letter-spacing="2">INITIATE OPERATOR MODE</text>
<text x="750" y="116" text-anchor="middle" class="mono" font-size="11" fill="#c4b4b4"
 letter-spacing="2.4">CLICK THE FRAME · CHOOSE A PROTOCOL · DECODE THE BUILD</text>
<rect x="570" y="134" width="360" height="2" fill="#310808"/>
<rect x="570" y="134" width="86" height="2" fill="#ff8a7f">
<animate attributeName="x" values="570;844;570" dur="3.8s" repeatCount="indefinite"/>
</rect>
{chevrons}
<g transform="translate(1378,98)">
<circle r="58" fill="#050101" stroke="#671515"/>
<circle r="46" fill="none" stroke="#e84b4b" opacity=".58" stroke-dasharray="8 12">
<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="9s" repeatCount="indefinite"/>
</circle>
<circle r="32" fill="none" stroke="#ff8a7f" opacity=".38" stroke-dasharray="3 7">
<animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="5s" repeatCount="indefinite"/>
</circle>
<path d="M-9 -5L0 5 14-12" fill="none" stroke="#f5eaea" stroke-width="3" stroke-linecap="round"/>
<text y="78" text-anchor="middle" class="mono" font-size="8" fill="#e84b4b" letter-spacing="2">ENTER</text>
</g>
</svg>'''


def build_achievement_rack_svg(cfg):
    W, H = 1500, 286
    achievements = [
        ("GPU", "4,000", "PARTICLES", "ONE DRAW CALL", .92),
        ("QA", "24", "TESTS", "FIVE SUITES", .84),
        ("CV", "78%", "ACCURACY", "CALIBRATED", .78),
        ("XP", "125", "STEAM LEVEL", "LONG GAME", .88),
        ("OSS", "25+", "PUBLIC REPOS", "BUILD LOG", .74),
    ]
    cards = []
    circumference = 251.3
    for i, (code, value, label, note, progress) in enumerate(achievements):
        x = 24 + i * 291
        end_offset = circumference * (1 - progress)
        cards.append(f'''
<g transform="translate({x},72)">
<rect width="276" height="188" rx="6" fill="#050101" stroke="#3d0b0b"/>
<rect width="5" height="188" rx="2" fill="#671515"/>
<circle cx="63" cy="78" r="48" fill="#0b0202" stroke="#310808"/>
<circle cx="63" cy="78" r="40" fill="none" stroke="#260606" stroke-width="5"/>
<circle cx="63" cy="78" r="40" fill="none" stroke="#e84b4b" stroke-width="5"
 stroke-linecap="round" stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{circumference:.1f}"
 transform="rotate(-90 63 78)">
<animate attributeName="stroke-dashoffset" values="{circumference:.1f};{end_offset:.1f}"
 dur="{1.5 + i * .18:.2f}s" begin="{i * .12:.2f}s" fill="freeze"/>
</circle>
<circle cx="63" cy="78" r="4" fill="#ff8a7f">
<animate attributeName="opacity" values=".25;1;.25" dur="{1.3 + i * .17:.2f}s" repeatCount="indefinite"/>
</circle>
<text x="63" y="83" text-anchor="middle" class="mono" font-size="12" fill="#f5eaea" letter-spacing="1">{code}</text>
<text x="132" y="72" class="serif" font-size="37" fill="#f5eaea">{value}</text>
<text x="132" y="96" class="mono" font-size="9" fill="#e84b4b" letter-spacing="1.8">{label}</text>
<path d="M22 142H254" stroke="#310808"/>
<text x="22" y="166" class="mono" font-size="9" fill="#8d7777" letter-spacing="1.8">{note}</text>
<rect x="226" y="154" width="28" height="3" fill="#671515"/>
<rect x="226" y="154" width="9" height="3" fill="#ff8a7f">
<animate attributeName="x" values="226;245;226" dur="2.6s" begin="-{i * .31:.2f}s" repeatCount="indefinite"/>
</rect>
</g>''')
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="rackBg" x1="0%" x2="100%">
<stop offset="0" stop-color="#020202"/><stop offset=".5" stop-color="#0d0202"/><stop offset="1" stop-color="#020202"/>
</linearGradient>
<pattern id="rackGrid" width="32" height="32" patternUnits="userSpaceOnUse">
<path d="M32 0H0V32" fill="none" stroke="#671515" stroke-width=".4" opacity=".08"/>
</pattern>
</defs>
<rect x="1" y="1" width="1498" height="284" rx="7" fill="url(#rackBg)" stroke="#310808"/>
<rect x="1" y="1" width="1498" height="284" rx="7" fill="url(#rackGrid)"/>
<text x="24" y="38" class="mono" font-size="11" fill="#e84b4b" letter-spacing="3">PROOF OF WORK // ACHIEVEMENTS UNLOCKED</text>
<text x="1476" y="38" text-anchor="end" class="mono" font-size="9" fill="#806d6d" letter-spacing="2">SIGNAL VERIFIED · 05 RECORDS</text>
<path d="M24 52H1476" stroke="#310808"/>
{"".join(cards)}
</svg>'''


def build_protocol_engineer_svg(cfg):
    W, H = 1500, 338
    stages = [
        ("01", "REALITY", "OBSERVE CONSTRAINTS"),
        ("02", "MODEL", "REMOVE AMBIGUITY"),
        ("03", "SYSTEM", "ENCODE BEHAVIOR"),
        ("04", "INTERFACE", "MAKE IT LEGIBLE"),
        ("05", "FEEDBACK", "CLOSE THE LOOP"),
    ]
    stage_svg = []
    for i, (code, title, subtitle) in enumerate(stages):
        x = 38 + i * 291
        stage_svg.append(f'''
<g transform="translate({x},104)">
<rect width="252" height="128" rx="5" fill="#050101" stroke="#3d0b0b"/>
<rect width="252" height="5" rx="2" fill="{"#e84b4b" if i in (0, 4) else "#671515"}"/>
<text x="18" y="35" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">NODE // {code}</text>
<text x="18" y="75" class="serif" font-size="29" fill="#f5eaea">{title}</text>
<text x="18" y="102" class="mono" font-size="8" fill="#e84b4b" letter-spacing="1.3">{subtitle}</text>
<circle cx="232" cy="22" r="5" fill="#e84b4b">
<animate attributeName="opacity" values=".2;1;.2" dur="{1.2 + i * .18:.2f}s" begin="-{i * .21:.2f}s" repeatCount="indefinite"/>
</circle>
</g>''')
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="traceBg" x1="0%" x2="100%"><stop offset="0" stop-color="#020202"/><stop offset="1" stop-color="#100202"/></linearGradient>
<pattern id="traceGrid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#671515" stroke-width=".45" opacity=".09"/></pattern>
<filter id="traceGlow"><feGaussianBlur stdDeviation="5"/></filter>
</defs>
<rect x="1" y="1" width="1498" height="336" rx="7" fill="url(#traceBg)" stroke="#310808"/>
<rect x="1" y="1" width="1498" height="336" rx="7" fill="url(#traceGrid)"/>
<text x="38" y="44" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">PROTOCOL 01 // TRACE</text>
<text x="38" y="78" class="serif" font-size="31" fill="#f5eaea">Architecture starts at the constraint.</text>
<text x="1462" y="48" text-anchor="end" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">INPUT: REALITY // OUTPUT: LEVERAGE</text>
<path d="M164 168H1336" stroke="#671515" stroke-width="2" stroke-dasharray="8 12">
<animate attributeName="stroke-dashoffset" values="0;-80" dur="5s" repeatCount="indefinite"/>
</path>
<circle r="8" fill="#ff8a7f" filter="url(#traceGlow)" opacity=".8">
<animateMotion path="M164 168H1336" dur="5s" repeatCount="indefinite"/>
</circle>
<circle r="4" fill="#fff"><animateMotion path="M164 168H1336" dur="5s" repeatCount="indefinite"/></circle>
{"".join(stage_svg)}
<text x="38" y="307" class="mono" font-size="10" fill="#9b8585" letter-spacing="2">THE DOMAIN CHANGES · THE STANDARD DOESN'T · OBSERVABILITY IS PART OF THE PRODUCT</text>
</svg>'''


def build_protocol_product_svg(cfg):
    W, H = 1500, 360
    nodes = [
        (1035, 58, "OBSERVE"), (1222, 126, "MODEL"), (1212, 274, "BUILD"),
        (1035, 320, "MEASURE"), (846, 226, "REPEAT"),
    ]
    spokes = []
    node_svg = []
    for i, (x, y, label) in enumerate(nodes):
        spokes.append(f'<path d="M1035 190L{x} {y}" stroke="#671515" stroke-dasharray="4 9"/>')
        node_svg.append(f'''
<g>
<circle cx="{x}" cy="{y}" r="35" fill="#060101" stroke="#671515"/>
<circle cx="{x}" cy="{y}" r="27" fill="none" stroke="#e84b4b" opacity=".35" stroke-dasharray="3 6">
<animateTransform attributeName="transform" type="rotate" from="0 {x} {y}" to="360 {x} {y}" dur="{7 + i}s" repeatCount="indefinite"/>
</circle>
<text x="{x}" y="{y + 4}" text-anchor="middle" class="mono" font-size="8" fill="#f5eaea" letter-spacing="1">{label}</text>
</g>''')
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="forgeBg" x1="0%" x2="100%"><stop offset="0" stop-color="#020202"/><stop offset=".6" stop-color="#080101"/><stop offset="1" stop-color="#1b0303"/></linearGradient>
<radialGradient id="forgeGlow"><stop offset="0" stop-color="#e84b4b" stop-opacity=".25"/><stop offset="1" stop-color="#e84b4b" stop-opacity="0"/></radialGradient>
<pattern id="forgeGrid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#671515" stroke-width=".45" opacity=".09"/></pattern>
</defs>
<rect x="1" y="1" width="1498" height="358" rx="7" fill="url(#forgeBg)" stroke="#310808"/>
<rect x="1" y="1" width="1498" height="358" rx="7" fill="url(#forgeGrid)"/>
<text x="42" y="48" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">PROTOCOL 02 // FORGE</text>
<text x="42" y="112" class="serif" font-size="52" fill="#f5eaea">Make the difficult</text>
<text x="42" y="164" class="serif" font-size="52" fill="#f5eaea">feel inevitable.</text>
<rect x="42" y="190" width="480" height="1" fill="#671515"/>
<text x="42" y="226" class="mono" font-size="11" fill="#a99494" letter-spacing="1.2">
<tspan x="42" dy="0">SCOPE HARD · SHIP SMALL · MEASURE HONESTLY</tspan>
<tspan x="42" dy="25">KEEP THE INTERFACE SIMPLE AND THE SYSTEM EXPLICIT</tspan>
<tspan x="42" dy="25">EARN COMPLEXITY ONLY WHEN REALITY DEMANDS IT</tspan>
</text>
<text x="42" y="328" class="mono" font-size="9" fill="#e84b4b" letter-spacing="2">PRODUCT DOCTRINE // BUILD → LEARN → COMPOUND</text>
<circle cx="1035" cy="190" r="178" fill="url(#forgeGlow)"/>
<circle cx="1035" cy="190" r="132" fill="none" stroke="#671515" stroke-dasharray="9 14">
<animateTransform attributeName="transform" type="rotate" from="0 1035 190" to="360 1035 190" dur="24s" repeatCount="indefinite"/>
</circle>
<circle cx="1035" cy="190" r="92" fill="none" stroke="#e84b4b" opacity=".3" stroke-dasharray="3 10">
<animateTransform attributeName="transform" type="rotate" from="360 1035 190" to="0 1035 190" dur="14s" repeatCount="indefinite"/>
</circle>
{"".join(spokes)}
{"".join(node_svg)}
<circle cx="1035" cy="190" r="66" fill="#050101" stroke="#e84b4b"/>
<circle cx="1035" cy="190" r="50" fill="none" stroke="#ff8a7f" opacity=".42" stroke-dasharray="5 8">
<animateTransform attributeName="transform" type="rotate" from="0 1035 190" to="-360 1035 190" dur="8s" repeatCount="indefinite"/>
</circle>
<text x="1035" y="185" text-anchor="middle" class="mono" font-size="11" fill="#f5eaea" letter-spacing="2">SHIP</text>
<text x="1035" y="205" text-anchor="middle" class="mono" font-size="9" fill="#e84b4b" letter-spacing="1">LEARN</text>
<text x="1452" y="334" text-anchor="end" class="mono" font-size="8" fill="#806d6d" letter-spacing="2">SYSTEM LOOP // CONTINUOUS</text>
</svg>'''


def build_protocol_human_svg(cfg):
    W, H = 1500, 350
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="archiveBg" x1="0%" x2="100%"><stop offset="0" stop-color="#030303"/><stop offset=".55" stop-color="#100202"/><stop offset="1" stop-color="#030303"/></linearGradient>
<radialGradient id="levelGlow"><stop offset="0" stop-color="#e84b4b" stop-opacity=".32"/><stop offset="1" stop-color="#e84b4b" stop-opacity="0"/></radialGradient>
<pattern id="archiveGrid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#671515" stroke-width=".45" opacity=".09"/></pattern>
<linearGradient id="archiveScan" gradientUnits="userSpaceOnUse" x1="-180" x2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#ff8a7f" stop-opacity=".12"/><stop offset="1" stop-color="#fff" stop-opacity="0"/><animate attributeName="x1" values="-180;1500" dur="10s" repeatCount="indefinite"/><animate attributeName="x2" values="0;1680" dur="10s" repeatCount="indefinite"/></linearGradient>
</defs>
<rect x="1" y="1" width="1498" height="348" rx="7" fill="url(#archiveBg)" stroke="#310808"/>
<rect x="1" y="1" width="1498" height="348" rx="7" fill="url(#archiveGrid)"/>
<rect x="1" y="1" width="1498" height="348" rx="7" fill="url(#archiveScan)"/>
<text x="36" y="42" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">PROTOCOL 03 // ARCHIVE</text>
<text x="1464" y="42" text-anchor="end" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">STEAM DNA · HUMAN SIGNAL</text>
<circle cx="190" cy="185" r="148" fill="url(#levelGlow)"/>
<circle cx="190" cy="185" r="108" fill="#050101" stroke="#671515" stroke-width="2"/>
<circle cx="190" cy="185" r="90" fill="none" stroke="#e84b4b" stroke-width="2" stroke-dasharray="11 15">
<animateTransform attributeName="transform" type="rotate" from="0 190 185" to="360 190 185" dur="18s" repeatCount="indefinite"/>
</circle>
<circle cx="190" cy="185" r="74" fill="none" stroke="#ff8a7f" opacity=".45" stroke-dasharray="3 8">
<animateTransform attributeName="transform" type="rotate" from="360 190 185" to="0 190 185" dur="10s" repeatCount="indefinite"/>
</circle>
<text x="190" y="151" text-anchor="middle" class="mono" font-size="10" fill="#8d7777" letter-spacing="2">STEAM LEVEL</text>
<text x="190" y="211" text-anchor="middle" class="serif" font-size="70" fill="#f5eaea">125</text>
<text x="190" y="236" text-anchor="middle" class="mono" font-size="8" fill="#e84b4b" letter-spacing="2">THE LONG GAME</text>
<path d="M382 70V304" stroke="#310808"/>
<text x="426" y="126" class="serif" font-size="54" fill="#f5eaea" letter-spacing="2">GRIND. BUILD. REPEAT.</text>
<text x="426" y="163" class="mono" font-size="12" fill="#e84b4b" letter-spacing="3">NO NOISE · NO SHORTCUTS · STAY CURIOUS</text>
<rect x="426" y="188" width="620" height="1" fill="#671515"/>
<g class="mono" font-size="10" letter-spacing="1.4">
<rect x="426" y="218" width="190" height="54" rx="4" fill="#080202" stroke="#3d0b0b"/>
<text x="448" y="240" fill="#8d7777">SIGNAL // 01</text><text x="448" y="259" fill="#f5eaea">DIGITAL WORLDS</text>
<rect x="630" y="218" width="190" height="54" rx="4" fill="#080202" stroke="#3d0b0b"/>
<text x="652" y="240" fill="#8d7777">SIGNAL // 02</text><text x="652" y="259" fill="#f5eaea">HARD PROBLEMS</text>
<rect x="834" y="218" width="190" height="54" rx="4" fill="#080202" stroke="#3d0b0b"/>
<text x="856" y="240" fill="#8d7777">SIGNAL // 03</text><text x="856" y="259" fill="#f5eaea">OBSESSIVE CRAFT</text>
</g>
<g transform="translate(1120,82)">
<rect width="326" height="220" rx="6" fill="#050101" stroke="#671515"/>
<rect width="326" height="48" rx="6" fill="#671515"/>
<rect y="42" width="326" height="6" fill="#671515"/>
<circle cx="24" cy="24" r="5" fill="#ff8a7f"><animate attributeName="opacity" values=".2;1;.2" dur="1.3s" repeatCount="indefinite"/></circle>
<text x="42" y="29" class="mono" font-size="10" fill="#fff" letter-spacing="2">OPERATOR PROFILE</text>
<text x="24" y="84" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">STATUS</text>
<text x="24" y="111" class="mono" font-size="17" fill="#f5eaea">ONLINE / BUILDING</text>
<text x="24" y="145" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">PHILOSOPHY</text>
<text x="24" y="172" class="mono" font-size="13" fill="#f5eaea">PLAY THE LONG GAME.</text>
<rect x="24" y="190" width="278" height="1" fill="#310808"/>
<text x="24" y="211" class="mono" font-size="9" fill="#e84b4b" letter-spacing="1.8">OPEN STEAM PROFILE ↗</text>
</g>
</svg>'''


def build_featured_project_svg(cfg):
    W, H = 1500, 520
    rng = random.Random(cfg["seed"] + 1200)
    particles = []
    for i in range(92):
        angle = rng.uniform(0, math.pi * 2)
        radius = rng.uniform(34, 190)
        x = 1110 + math.cos(angle) * radius * 1.5
        y = 258 + math.sin(angle) * radius
        r = rng.uniform(.9, 2.7)
        dur = rng.uniform(3, 8)
        particles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" '
            f'fill="{"#ff8a7f" if i % 5 == 0 else "#e84b4b"}">'
            f'<animate attributeName="opacity" values=".12;.95;.12" dur="{dur:.2f}s" '
            f'begin="-{rng.uniform(0,dur):.2f}s" repeatCount="indefinite"/></circle>'
        )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="featureBg" x1="0%" x2="100%">
<stop offset="0%" stop-color="#020202"/><stop offset="58%" stop-color="#080101"/>
<stop offset="100%" stop-color="#1f0404"/>
</linearGradient>
<radialGradient id="particleGlow">
<stop offset="0" stop-color="#e84b4b" stop-opacity=".28"/>
<stop offset="1" stop-color="#e84b4b" stop-opacity="0"/>
</radialGradient>
<pattern id="featureGrid" width="36" height="36" patternUnits="userSpaceOnUse">
<path d="M36 0H0V36" fill="none" stroke="#e84b4b" stroke-width=".45" opacity=".09"/>
</pattern>
<filter id="featureGlow"><feGaussianBlur stdDeviation="10"/></filter>
</defs>
<rect x="1" y="1" width="1498" height="518" rx="8" fill="url(#featureBg)" stroke="#671515"/>
<rect x="1" y="1" width="1498" height="518" rx="8" fill="url(#featureGrid)"/>
<rect x="18" y="18" width="1464" height="484" rx="5" fill="none" stroke="#e84b4b"
 opacity=".16" stroke-dasharray="38 12"/>
<text x="52" y="62" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">
FLAGSHIP // 01
</text>
<text x="52" y="128" class="serif" font-size="62" fill="#f5eaea">Personal Portfolio</text>
<text x="52" y="164" class="mono" font-size="15" fill="#bdaaaa" letter-spacing="1.5">
AN INTERACTIVE 3D PRODUCT UNIVERSE
</text>
<rect x="52" y="190" width="520" height="1" fill="#671515"/>
<text x="52" y="232" class="mono" font-size="13" fill="#a99494">
<tspan x="52" dy="0">4,000 GPU-driven particles.</tspan>
<tspan x="52" dy="27">Lazy-loaded case-study systems.</tspan>
<tspan x="52" dy="27">Automated GitHub data synchronization.</tspan>
<tspan x="52" dy="27">24 tests across five Vitest suites.</tspan>
</text>
<g transform="translate(52,354)">
<rect width="172" height="50" rx="3" fill="#671515"/>
<text x="86" y="31" text-anchor="middle" class="mono" font-size="12" fill="#fff"
 letter-spacing="2">ENTER SYSTEM</text>
</g>
<g transform="translate(238,354)">
<rect width="146" height="50" rx="3" fill="#050505" stroke="#671515"/>
<text x="73" y="31" text-anchor="middle" class="mono" font-size="12" fill="#e84b4b"
 letter-spacing="2">SOURCE</text>
</g>
<text x="52" y="470" class="mono" font-size="10" fill="#806d6d" letter-spacing="2">
TYPESCRIPT · REACT · THREE.JS · VITE · VITEST
</text>
<circle cx="1110" cy="258" r="245" fill="url(#particleGlow)"/>
<ellipse cx="1110" cy="258" rx="300" ry="202" fill="none" stroke="#671515" opacity=".55"/>
<ellipse cx="1110" cy="258" rx="240" ry="150" fill="none" stroke="#e84b4b"
 opacity=".32" stroke-dasharray="12 18">
<animateTransform attributeName="transform" type="rotate" from="0 1110 258"
 to="360 1110 258" dur="28s" repeatCount="indefinite"/>
</ellipse>
<ellipse cx="1110" cy="258" rx="170" ry="240" fill="none" stroke="#ff8a7f"
 opacity=".18" stroke-dasharray="4 14">
<animateTransform attributeName="transform" type="rotate" from="360 1110 258"
 to="0 1110 258" dur="22s" repeatCount="indefinite"/>
</ellipse>
{"".join(particles)}
<circle cx="1110" cy="258" r="54" fill="#050101" stroke="#e84b4b"/>
<circle cx="1110" cy="258" r="43" fill="none" stroke="#e84b4b" opacity=".5"
 stroke-dasharray="3 7">
<animateTransform attributeName="transform" type="rotate" from="0 1110 258"
 to="-360 1110 258" dur="8s" repeatCount="indefinite"/>
</circle>
<text x="1110" y="253" text-anchor="middle" class="mono" font-size="12" fill="#f5eaea"
 letter-spacing="2">YOR</text>
<text x="1110" y="272" text-anchor="middle" class="mono" font-size="9" fill="#e84b4b">
PORTFOLIO
</text>
</svg>'''


def project_visual_svg(kind, cfg):
    if kind == "helios":
        return '''
<path d="M50 252 L130 205 L210 225 L292 152 L374 177 L458 98 L540 130 L640 62"
 fill="none" stroke="#e84b4b" stroke-width="4" stroke-linecap="round"
 stroke-dasharray="900" stroke-dashoffset="900">
<animate attributeName="stroke-dashoffset" values="900;0;0" keyTimes="0;.55;1"
 dur="5s" repeatCount="indefinite"/></path>
<path d="M50 282H640M50 220H640M50 158H640M50 96H640" stroke="#671515" opacity=".25"/>
<g transform="translate(440,182)">
<rect width="190" height="80" rx="5" fill="#180303" stroke="#e84b4b"/>
<circle cx="22" cy="22" r="5" fill="#ff8a7f"><animate attributeName="opacity"
 values=".2;1;.2" dur="1s" repeatCount="indefinite"/></circle>
<text x="38" y="27" class="mono" font-size="10" fill="#f5eaea">SPIKE DETECTED</text>
<text x="20" y="56" class="mono" font-size="20" fill="#e84b4b">+18.4%</text>
</g>'''
    if kind == "zenith":
        art = asset_data_uri("zenith-solar-reference.png", "image/png")
        return f'''
<clipPath id="zenithClip"><rect x="28" y="82" width="664" height="224" rx="5"/></clipPath>
<g clip-path="url(#zenithClip)">
<image href="{art}" x="28" y="82" width="664" height="224" preserveAspectRatio="xMidYMid slice"/>
<rect x="28" y="82" width="664" height="224" fill="#170000" opacity=".48"/>
<path d="M34 265 Q210 60 440 120 T686 88" fill="none" stroke="#ff8a7f"
 stroke-width="2" stroke-dasharray="8 10">
<animate attributeName="stroke-dashoffset" values="0;-72" dur="5s"
 repeatCount="indefinite"/></path>
</g>
<g transform="translate(520,224)">
<circle r="48" fill="#050505" stroke="#e84b4b"/>
<circle r="36" fill="none" stroke="#ff8a7f" opacity=".5" stroke-dasharray="4 7">
<animateTransform attributeName="transform" type="rotate" from="0" to="360"
 dur="7s" repeatCount="indefinite"/></circle>
<text y="5" text-anchor="middle" class="mono" font-size="14" fill="#f5eaea">ROI</text>
</g>'''
    if kind == "vision":
        pixels = []
        for row in range(7):
            for col in range(11):
                op = .12 + ((row * 11 + col) % 9) * .07
                pixels.append(
                    f'<rect x="{48+col*24}" y="{102+row*24}" width="18" height="18" rx="2" '
                    f'fill="#e84b4b" opacity="{op:.2f}"/>'
                )
        return f'''
<rect x="32" y="86" width="306" height="210" rx="5" fill="#080202" stroke="#310808"/>
{"".join(pixels)}
<path d="M382 115H656M382 168H620M382 221H580" stroke="#671515" stroke-width="18"
 stroke-linecap="round"/>
<path d="M382 115H614M382 168H548M382 221H494" stroke="#e84b4b" stroke-width="18"
 stroke-linecap="round">
<animate attributeName="opacity" values=".55;1;.55" dur="2.2s" repeatCount="indefinite"/>
</path>
<text x="382" y="277" class="mono" font-size="27" fill="#f5eaea">78% / REAL</text>'''
    if kind == "talks":
        return '''
<path d="M118 142 C220 80 298 248 406 156 S570 102 628 180" fill="none"
 stroke="#671515" stroke-width="2" stroke-dasharray="6 9">
<animate attributeName="stroke-dashoffset" values="0;-60" dur="4s"
 repeatCount="indefinite"/></path>
<g fill="#090202" stroke="#e84b4b">
<rect x="52" y="102" width="190" height="76" rx="12"/>
<rect x="292" y="192" width="210" height="76" rx="12"/>
<rect x="466" y="82" width="190" height="76" rx="12"/>
</g>
<g class="mono" font-size="11" fill="#c4c4c4">
<text x="74" y="132">CHANNEL ONLINE</text><text x="74" y="153">latency 42ms</text>
<text x="314" y="222">EVENT DELIVERED</text><text x="314" y="243">socket / room-07</text>
<text x="488" y="112">AUTH VERIFIED</text><text x="488" y="133">token refreshed</text>
</g>
<g fill="#ff8a7f">
<circle cx="118" cy="142" r="5"><animate attributeName="r" values="3;8;3"
 dur="2s" repeatCount="indefinite"/></circle>
<circle cx="406" cy="156" r="5"><animate attributeName="r" values="3;8;3"
 dur="2s" begin="-.7s" repeatCount="indefinite"/></circle>
<circle cx="628" cy="180" r="5"><animate attributeName="r" values="3;8;3"
 dur="2s" begin="-1.3s" repeatCount="indefinite"/></circle>
</g>'''
    if kind == "next":
        return '''
<circle cx="360" cy="190" r="114" fill="#080202" stroke="#310808"/>
<circle cx="360" cy="190" r="84" fill="none" stroke="#671515" stroke-dasharray="7 12">
<animateTransform attributeName="transform" type="rotate" from="0 360 190"
 to="360 360 190" dur="12s" repeatCount="indefinite"/></circle>
<circle cx="360" cy="190" r="54" fill="none" stroke="#e84b4b" opacity=".5"
 stroke-dasharray="3 8"><animateTransform attributeName="transform" type="rotate"
 from="360 360 190" to="0 360 190" dur="7s" repeatCount="indefinite"/></circle>
<path d="M360 106V274M276 190H444" stroke="#671515" opacity=".65"/>
<circle cx="360" cy="190" r="12" fill="#e84b4b">
<animate attributeName="r" values="8;18;8" dur="2.2s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="1;.25;1" dur="2.2s" repeatCount="indefinite"/>
</circle>
<text x="360" y="194" text-anchor="middle" class="mono" font-size="20"
 fill="#fff">+</text>
<text x="360" y="298" text-anchor="middle" class="mono" font-size="10"
 fill="#c4c4c4" letter-spacing="2">AWAITING THE NEXT HARD PROBLEM</text>'''
    # feelings
    waves = []
    for i in range(5):
        y = 116 + i * 38
        waves.append(
            f'<path d="M52 {y} C130 {y-34} 176 {y+34} 254 {y} S378 {y-28} 448 {y} '
            f'S560 {y+30} 650 {y}" fill="none" stroke="{"#e84b4b" if i % 2 == 0 else "#671515"}" '
            f'stroke-width="{3 if i % 2 == 0 else 2}" opacity="{.9-i*.11:.2f}" '
            f'stroke-dasharray="8 10"><animate attributeName="stroke-dashoffset" '
            f'values="0;-72" dur="{3.5+i*.6:.1f}s" repeatCount="indefinite"/></path>'
        )
    return f'''
{"".join(waves)}
<circle cx="572" cy="190" r="74" fill="#080202" stroke="#671515"/>
<circle cx="572" cy="190" r="57" fill="none" stroke="#e84b4b" stroke-width="10"
 stroke-dasharray="232 126" transform="rotate(-90 572 190)"/>
<text x="572" y="187" text-anchor="middle" class="mono" font-size="10"
 fill="#9b8585">SENTIMENT</text>
<text x="572" y="211" text-anchor="middle" class="mono" font-size="22"
 fill="#f5eaea">+0.82</text>'''


def build_project_card_svg(project, cfg):
    W, H = 720, 430
    visual = project_visual_svg(project["kind"], cfg)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="cardBg" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#020202"/><stop offset="68%" stop-color="#080101"/>
<stop offset="100%" stop-color="#1d0404"/>
</linearGradient>
<pattern id="cardGrid" width="24" height="24" patternUnits="userSpaceOnUse">
<path d="M24 0H0V24" fill="none" stroke="#671515" stroke-width=".45" opacity=".1"/>
</pattern>
<linearGradient id="cardSweep" gradientUnits="userSpaceOnUse" x1="-160" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"
 stop-opacity=".1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-160;720" dur="9s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;880" dur="9s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<rect x="1" y="1" width="718" height="428" rx="7" fill="url(#cardBg)" stroke="#4b0e0e"/>
<rect x="1" y="1" width="718" height="428" rx="7" fill="url(#cardGrid)"/>
<rect x="1" y="1" width="718" height="428" rx="7" fill="url(#cardSweep)"/>
<rect x="18" y="18" width="5" height="45" rx="2" fill="#e84b4b"/>
<text x="38" y="37" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">
{esc(project["code"])} // {esc(project["domain"])}
</text>
<text x="38" y="60" class="mono" font-size="18" fill="#f5eaea" letter-spacing="1.4">
{esc(project["title"])}
</text>
<g>{visual}</g>
<rect x="28" y="326" width="664" height="1" fill="#310808"/>
<text x="28" y="359" class="mono" font-size="10" fill="#e84b4b" letter-spacing="1.8">
{esc(project["stack"])}
</text>
<text x="28" y="392" class="mono" font-size="11" fill="#a99494">
{esc(project["summary"])}
</text>
<text x="684" y="404" text-anchor="end" class="mono" font-size="12" fill="#e84b4b">OPEN ↗</text>
</svg>'''


def build_arsenal_svg(cfg):
    W, H = 1500, 540
    tech = [
        (750, 76, "RUST"), (1000, 116, "TYPESCRIPT"), (1182, 264, "REACT / NEXT"),
        (1030, 424, "THREE.JS"), (750, 474, "PYTHON"), (470, 424, "FASTAPI"),
        (318, 264, "POSTGRES / REDIS"), (500, 116, "DOCKER / AWS"),
    ]
    spokes = []
    labels = []
    for i, (x, y, label) in enumerate(tech):
        spokes.append(
            f'<path d="M750 270 L{x} {y}" stroke="#671515" stroke-width="1.2" '
            f'stroke-dasharray="5 11"><animate attributeName="stroke-dashoffset" '
            f'values="0;-64" dur="{4+i*.45:.1f}s" repeatCount="indefinite"/></path>'
        )
        labels.append(
            f'<g><rect x="{x-76}" y="{y-22}" width="152" height="44" rx="4" '
            f'fill="#070101" stroke="#4c0d0d"/>'
            f'<circle cx="{x-58}" cy="{y}" r="4" fill="#e84b4b">'
            f'<animate attributeName="opacity" values=".25;1;.25" dur="{1.4+i*.17:.2f}s" '
            f'repeatCount="indefinite"/></circle>'
            f'<text x="{x+8}" y="{y+5}" text-anchor="middle" class="mono" font-size="11" '
            f'fill="#d9cccc" letter-spacing="1">{esc(label)}</text></g>'
        )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<radialGradient id="arsenalGlow">
<stop offset="0" stop-color="#e84b4b" stop-opacity=".2"/>
<stop offset="1" stop-color="#e84b4b" stop-opacity="0"/>
</radialGradient>
<pattern id="arsenalGrid" width="30" height="30" patternUnits="userSpaceOnUse">
<path d="M30 0H0V30" fill="none" stroke="#671515" stroke-width=".45" opacity=".09"/>
</pattern>
</defs>
<rect x="1" y="1" width="1498" height="538" rx="7" fill="#020202" stroke="#350909"/>
<rect x="1" y="1" width="1498" height="538" rx="7" fill="url(#arsenalGrid)"/>
<circle cx="750" cy="270" r="246" fill="url(#arsenalGlow)"/>
<ellipse cx="750" cy="270" rx="390" ry="210" fill="none" stroke="#310808"/>
<ellipse cx="750" cy="270" rx="295" ry="158" fill="none" stroke="#671515"
 stroke-dasharray="8 14" opacity=".65">
<animateTransform attributeName="transform" type="rotate" from="0 750 270"
 to="360 750 270" dur="34s" repeatCount="indefinite"/>
</ellipse>
<circle cx="750" cy="270" r="126" fill="none" stroke="#e84b4b" opacity=".18"
 stroke-dasharray="3 12">
<animateTransform attributeName="transform" type="rotate" from="360 750 270"
 to="0 750 270" dur="18s" repeatCount="indefinite"/>
</circle>
{"".join(spokes)}
{"".join(labels)}
<circle cx="750" cy="270" r="82" fill="#050101" stroke="#e84b4b" stroke-width="1.5"/>
<circle cx="750" cy="270" r="64" fill="none" stroke="#ff8a7f" opacity=".55"
 stroke-dasharray="5 8">
<animateTransform attributeName="transform" type="rotate" from="0 750 270"
 to="-360 750 270" dur="9s" repeatCount="indefinite"/>
</circle>
<text x="750" y="262" text-anchor="middle" class="serif" font-size="31" fill="#f5eaea">AYR</text>
<text x="750" y="289" text-anchor="middle" class="mono" font-size="9" fill="#e84b4b"
 letter-spacing="2">TECHNICAL CORE</text>
<text x="38" y="44" class="mono" font-size="10" fill="#8d7777" letter-spacing="2">
PRODUCT · SYSTEMS · INFRASTRUCTURE
</text>
<text x="1462" y="514" text-anchor="end" class="mono" font-size="9" fill="#6f5b5b"
 letter-spacing="2">TOOLS ARE LOADOUT. SYSTEMS ARE THE WORK.</text>
</svg>'''


def build_finale_svg(cfg):
    W, H = 1500, 300
    rng = random.Random(cfg["seed"] + 1400)
    stars = "".join(
        f'<circle cx="{rng.uniform(20,W-20):.1f}" cy="{rng.uniform(10,150):.1f}" '
        f'r="{rng.uniform(.5,1.6):.2f}" fill="#ff8a7f" opacity="{rng.uniform(.15,.75):.2f}">'
        f'<animate attributeName="opacity" values=".1;.9;.1" dur="{rng.uniform(2,5):.2f}s" '
        f'begin="-{rng.uniform(0,4):.2f}s" repeatCount="indefinite"/></circle>'
        for _ in range(42)
    )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<radialGradient id="finalSun">
<stop offset="0" stop-color="#ff8a7f"/><stop offset=".38" stop-color="#e84b4b"/>
<stop offset="1" stop-color="#671515" stop-opacity="0"/>
</radialGradient>
<linearGradient id="finalHorizon" x1="0%" y1="0%" x2="0%" y2="100%">
<stop offset="0%" stop-color="#000"/><stop offset="100%" stop-color="#220404"/>
</linearGradient>
<pattern id="floorGrid" width="62" height="28" patternUnits="userSpaceOnUse"
 patternTransform="skewX(-26)">
<path d="M62 0H0V28" fill="none" stroke="#e84b4b" stroke-width=".7" opacity=".18"/>
</pattern>
</defs>
<rect width="{W}" height="{H}" fill="url(#finalHorizon)"/>
{stars}
<circle cx="750" cy="230" r="176" fill="url(#finalSun)" opacity=".68">
<animate attributeName="opacity" values=".52;.78;.52" dur="5s" repeatCount="indefinite"/>
</circle>
<rect y="204" width="{W}" height="96" fill="url(#floorGrid)"/>
<rect y="203" width="{W}" height="1" fill="#ff8a7f" opacity=".7"/>
<rect x="280" y="40" width="940" height="136" rx="5" fill="#000" opacity=".74"
 stroke="#671515"/>
<text x="750" y="100" text-anchor="middle" class="serif" font-size="48" fill="#f5eaea"
 letter-spacing="3">GRIND. BUILD. REPEAT.</text>
<text x="750" y="137" text-anchor="middle" class="mono" font-size="11" fill="#c4b4b4"
 letter-spacing="3">NO NOISE · NO SHORTCUTS · JUST FOCUS AND THE WORK</text>
<circle cx="610" cy="160" r="4" fill="#e84b4b">
<animate attributeName="opacity" values=".2;1;.2" dur="1.4s" repeatCount="indefinite"/>
</circle>
<text x="750" y="165" text-anchor="middle" class="mono" font-size="9" fill="#e84b4b"
 letter-spacing="2">CHANNEL OPEN // COLLABORATION SIGNAL ACTIVE</text>
</svg>'''


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    hero = build_cinematic_hero_svg(CONFIG)
    hero_path = os.path.join(OUT_DIR, "hero.svg")
    with open(hero_path, "w", encoding="utf-8") as f:
        f.write(hero)
    print(f"wrote {hero_path} ({len(hero)/1024:.1f} KB)")

    for label, color in [("primary", CONFIG["primary"]), ("secondary", CONFIG["secondary"])]:
        div = build_divider_svg(color)
        div_path = os.path.join(OUT_DIR, f"divider-{label}.svg")
        with open(div_path, "w", encoding="utf-8") as f:
            f.write(div)
        print(f"wrote {div_path} ({len(div)/1024:.1f} KB)")

    wave_specs = [
        ("wave-header", CONFIG["wave_header_stops"], True, 12, CONFIG["seed"] + 1),
        ("wave-footer", CONFIG["wave_footer_stops"], False, 12, CONFIG["seed"] + 2),
    ]
    for name, stops, crest_up, star_count, seed in wave_specs:
        svg = build_wave_banner_svg(1500, 40, stops, crest_up, star_count, CONFIG["primary"], seed)
        path = os.path.join(OUT_DIR, f"{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

    wave_final = build_wave_final_svg(CONFIG)
    wave_final_path = os.path.join(OUT_DIR, "wave-final.svg")
    with open(wave_final_path, "w", encoding="utf-8") as f:
        f.write(wave_final)
    print(f"wrote {wave_final_path} ({len(wave_final)/1024:.1f} KB)")

    tagline = build_tagline_svg(CONFIG)
    tagline_path = os.path.join(OUT_DIR, "tagline.svg")
    with open(tagline_path, "w", encoding="utf-8") as f:
        f.write(tagline)
    print(f"wrote {tagline_path} ({len(tagline)/1024:.1f} KB)")

    for i, (name, glyph, color_key) in enumerate(CONFIG["seals"]):
        seal = build_seal_svg(glyph, CONFIG[color_key], CONFIG["seed"] + 100 + i)
        seal_path = os.path.join(OUT_DIR, f"{name}.svg")
        with open(seal_path, "w", encoding="utf-8") as f:
            f.write(seal)
        print(f"wrote {seal_path} ({len(seal)/1024:.1f} KB)")

    panel_headers = [
        ("panel-profile", "SYSTEM PROFILE", "STATUS // BUILDING"),
        ("panel-showcase", "PROJECT SHOWCASE", "05 SYSTEMS // 01 ACTIVE BUILD"),
        ("panel-loadout", "TECHNICAL LOADOUT", "PRODUCT // SYSTEMS // INFRA"),
        ("panel-record", "SYSTEM RECORD", "PUBLIC BUILD LOG"),
    ]
    for filename, title, subtitle in panel_headers:
        panel = build_panel_header_svg(title, subtitle, CONFIG)
        panel_path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(panel_path, "w", encoding="utf-8") as f:
            f.write(panel)
        print(f"wrote {panel_path} ({len(panel)/1024:.1f} KB)")

    experience_assets = {
        "signal-strip": build_signal_strip_svg(CONFIG),
        "identity-console": build_identity_console_svg(CONFIG),
        "operator-gateway": build_operator_gateway_svg(CONFIG),
        "achievement-rack": build_achievement_rack_svg(CONFIG),
        "protocol-engineer": build_protocol_engineer_svg(CONFIG),
        "protocol-product": build_protocol_product_svg(CONFIG),
        "protocol-human": build_protocol_human_svg(CONFIG),
        "project-portfolio": build_featured_project_svg(CONFIG),
        "arsenal": build_arsenal_svg(CONFIG),
        "finale": build_finale_svg(CONFIG),
    }
    for filename, svg in experience_assets.items():
        path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

    nav_specs = [
        ("nav-portfolio", "PORTFOLIO", "ENTER THE SYSTEM", "◢"),
        ("nav-projects", "PROJECTS", "EXPLORE THE BUILDS", "⌁"),
        ("nav-steam", "STEAM", "OPERATOR PROFILE", "◉"),
        ("nav-contact", "CONNECT", "OPEN A CHANNEL", "◇"),
    ]
    for i, (filename, label, code, glyph) in enumerate(nav_specs):
        svg = build_nav_button_svg(label, code, glyph, CONFIG, CONFIG["seed"] + 1500 + i)
        path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

    section_specs = [
        ("section-identity", "01", "OPERATOR / IDENTITY", "THE PERSON BEHIND THE SYSTEMS"),
        ("section-projects", "02", "SELECTED / SYSTEMS", "CLICK ANY VISUAL TO OPEN THE BUILD"),
        ("section-arsenal", "03", "TECHNICAL / ARSENAL", "PRODUCT · SYSTEMS · INFRASTRUCTURE"),
        ("section-record", "04", "PUBLIC / RECORD", "REPOSITORIES · LANGUAGES · SIGNAL"),
    ]
    for filename, index, title, subtitle in section_specs:
        svg = build_section_header_svg(index, title, subtitle, CONFIG)
        path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

    projects = [
        {
            "filename": "project-helios", "kind": "helios", "code": "SYS-02",
            "domain": "REALTIME TELEMETRY", "title": "YOR HELIOS",
            "stack": "PYTHON · FASTAPI · WEBSOCKETS · DOCKER",
            "summary": "Threshold intelligence and anomaly alerts, streamed live.",
        },
        {
            "filename": "project-zenith", "kind": "zenith", "code": "SYS-03",
            "domain": "GEOSPATIAL SOLAR", "title": "YOR ZENITH",
            "stack": "TYPESCRIPT · NEXT.JS · POSTGIS · THREE.JS",
            "summary": "Roof geometry, irradiance, placement, ROI, and payback.",
        },
        {
            "filename": "project-vision", "kind": "vision", "code": "SYS-04",
            "domain": "COMPUTER VISION", "title": "AI VS REAL",
            "stack": "PYTHON · OPENCV · SCIKIT-LEARN · STREAMLIT",
            "summary": "Texture intelligence with calibrated confidence.",
        },
        {
            "filename": "project-talks", "kind": "talks", "code": "SYS-05",
            "domain": "REALTIME COMMS", "title": "YOR TALKS",
            "stack": "TYPESCRIPT · REACT · SOCKET.IO · REDIS",
            "summary": "Bidirectional rooms, delivery, auth, and presence.",
        },
        {
            "filename": "project-feelings", "kind": "feelings", "code": "SYS-06",
            "domain": "SENTIMENT", "title": "YOR FEELINGS",
            "stack": "TYPESCRIPT · NEXT.JS · PRISMA · NLP",
            "summary": "Mood intelligence translated into responsive interface state.",
        },
        {
            "filename": "project-next", "kind": "next", "code": "SYS-07",
            "domain": "OPEN CHANNEL", "title": "NEXT TRANSMISSION",
            "stack": "COLLABORATION · RESEARCH · OPEN SOURCE",
            "summary": "Bring the difficult problem. We'll build the system.",
        },
    ]
    for project in projects:
        svg = build_project_card_svg(project, CONFIG)
        path = os.path.join(OUT_DIR, f'{project["filename"]}.svg')
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

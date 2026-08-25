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


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    hero = build_hero_svg(CONFIG)
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

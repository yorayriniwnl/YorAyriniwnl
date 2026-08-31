#!/usr/bin/env python3
"""Render a short rotating signal study and reduced-motion posters.

The imagery is an illustrative motion study, not simulated live telemetry.
Both layouts use the same scenes and palette, with no external assets or fonts.
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_data import load_profile

ROOT = SCRIPT_DIR.parent
OUT_DIR = ROOT / "generated"
WIDTH, HEIGHT = 900, 320
MOBILE_SIZE = (600, 650)
FRAME_COUNT = 48
FRAME_DURATION = 120
PALETTE = load_profile()["visual_contract"]["palette"]
TAU = math.tau


def rgb(value):
    return tuple(int(value.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


VOID = rgb(PALETTE["void"])
CRIMSON = rgb(PALETTE["crimson"])
DEEP = rgb(PALETTE["deep_crimson"])
SIGNAL = rgb(PALETTE["signal"])
PAPER = rgb(PALETTE["paper"])


@lru_cache(maxsize=12)
def font(size):
    return ImageFont.load_default(size=size)


def mix(left, right, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(left, right))


def project(x, y, z, angle, tilt=.55):
    """Orthographic camera; periodic rotation makes the GIF loop seamless."""
    xx = x * math.cos(angle) + z * math.sin(angle)
    zz = -x * math.sin(angle) + z * math.cos(angle)
    return xx, y * math.cos(tilt) - zz * math.sin(tilt), y * math.sin(tilt) + zz * math.cos(tilt)


def point(draw, x, y, radius, color):
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def draw_particles(draw, cx, cy, phase):
    particles = []
    for ring in range(30):
        u = ring / 30 * TAU
        for spoke in range(8):
            v = spoke / 8 * TAU
            radius = 58 + 19 * math.cos(v)
            x, y, z = project(radius * math.cos(u), 19 * math.sin(v), radius * math.sin(u), phase * TAU, .72)
            particles.append((z, cx + x * 1.22, cy + y, 1.2 + (z + 78) / 100))
    for z, x, y, r in sorted(particles):
        light = max(.12, min(1, (z + 85) / 155))
        point(draw, x, y, r, mix((42, 10, 13), SIGNAL, light))
    draw.arc((cx - 105, cy - 51, cx + 105, cy + 51), 8, 133, fill=DEEP, width=1)
    draw.arc((cx - 105, cy - 51, cx + 105, cy + 51), 188, 313, fill=DEEP, width=1)


def draw_streams(draw, cx, cy, phase):
    for lane in range(7):
        points = []
        for sample in range(100):
            t = sample / 99
            envelope = math.sin(t * math.pi)
            wave = math.sin(t * TAU * 1.4 - phase * TAU + lane * .32)
            points.append((cx - 114 + t * 228, cy + (lane - 3) * 12 + wave * 22 * envelope))
        color = mix((49, 12, 17), SIGNAL, .85 if lane == 3 else .12 + lane * .065)
        draw.line(points, fill=color, width=2 if lane == 3 else 1)
        position = (phase + lane / 7) % 1
        px = cx - 114 + position * 228
        py = cy + (lane - 3) * 12 + math.sin(position * TAU * 1.4 - phase * TAU + lane * .32) * 22 * math.sin(position * math.pi)
        # Fade packets at the edges instead of visibly teleporting on loop.
        opacity = math.sin(position * math.pi) ** .5
        point(draw, px, py, 3, mix((30, 6, 10), SIGNAL, opacity))
        point(draw, px, py, 1, mix((30, 6, 10), PAPER, opacity))


def draw_vision(draw, cx, cy, phase):
    scan_y = cy + math.sin(phase * TAU) * 45
    for row in range(11):
        for col in range(24):
            x, y = cx - 92 + col * 8, cy - 40 + row * 8
            texture = (math.sin(col * .8 + row * .4) + math.cos(col * .25 - row * .8) + 2) / 4
            proximity = max(0, 1 - abs(y - scan_y) / 20)
            color = mix((21, 7, 10), SIGNAL, texture * (.25 + proximity * .65))
            draw.rectangle((x, y, x + 3, y + 3), fill=color)
    for sign_x in (-1, 1):
        for sign_y in (-1, 1):
            x, y = cx + sign_x * 108, cy + sign_y * 54
            draw.line([(x - sign_x * 15, y), (x, y), (x, y - sign_y * 15)], fill=CRIMSON, width=2)
    draw.line((cx - 99, scan_y, cx + 99, scan_y), fill=SIGNAL, width=1)
    draw.line((cx - 5, cy, cx + 5, cy), fill=PAPER, width=1)
    draw.line((cx, cy - 5, cx, cy + 5), fill=PAPER, width=1)


def draw_network(draw, cx, cy, phase):
    nodes = [(cx - 106, cy), (cx - 57, cy - 41), (cx + 55, cy - 40),
             (cx + 107, cy + 8), (cx + 56, cy + 46), (cx - 55, cy + 44)]
    center = (cx, cy)
    for i, end in enumerate(nodes):
        draw.line([center, end], fill=DEEP, width=1)
        draw.line([end, nodes[(i + 1) % len(nodes)]], fill=(47, 11, 15), width=1)
        progress = (phase + i / len(nodes)) % 1
        x = cx + (end[0] - cx) * progress
        y = cy + (end[1] - cy) * progress
        point(draw, x, y, 2.5, mix(DEEP, SIGNAL, math.sin(progress * math.pi)))
        point(draw, *end, 5, DEEP)
        point(draw, *end, 2, SIGNAL)
    top, left, right, bottom = (cx, cy - 24), (cx - 26, cy - 10), (cx + 26, cy - 10), (cx, cy + 28)
    draw.polygon([top, right, (cx, cy + 4), left], fill=(50, 10, 16), outline=SIGNAL)
    draw.polygon([left, (cx, cy + 4), bottom, (cx - 26, cy + 14)], fill=(19, 5, 9), outline=CRIMSON)
    draw.polygon([(cx, cy + 4), right, (cx + 26, cy + 14), bottom], fill=(33, 7, 12), outline=CRIMSON)


SCENES = (
    ("01", "GPU WORLDS", "PARTICLES / INTERFACES", draw_particles),
    ("02", "REALTIME", "EVENTS / SIGNALS", draw_streams),
    ("03", "VISION", "TEXTURES / FEATURES", draw_vision),
    ("04", "PLATFORMS", "APIs / CONNECTIONS", draw_network),
)


def build_frame(frame_index, mobile=False):
    index = frame_index % FRAME_COUNT
    phase = index / FRAME_COUNT
    scene_index = min(len(SCENES) - 1, index * len(SCENES) // FRAME_COUNT)
    _, label, _, renderer = SCENES[scene_index]
    label = "INTERFACES" if scene_index == 0 else label
    size = MOBILE_SIZE if mobile else (WIDTH, HEIGHT)
    frame = Image.new("RGB", size, (5, 5, 7))
    draw = ImageDraw.Draw(frame)
    body_size = 42 if mobile else 26
    draw.rounded_rectangle((1, 1, size[0]-2, size[1]-2), radius=14,
                           outline=(72, 32, 41), width=2)
    draw.text((30, 24), "AYR / SIGNAL STUDY", font=font(body_size), fill=SIGNAL)
    draw.line((30, 78, size[0]-30, 78), fill=DEEP, width=2)
    diagram = Image.new("RGB", (300, 190), (5, 5, 7))
    renderer(ImageDraw.Draw(diagram), 150, 95, phase)
    if mobile:
        draw.text((30, 105), label, font=font(58), fill=PAPER)
        frame.paste(diagram.resize((540, 342), Image.Resampling.LANCZOS), (30, 170))
        draw = ImageDraw.Draw(frame)
        draw.text((30, 524), "ILLUSTRATIVE ART", font=font(body_size), fill=SIGNAL)
        draw.text((30, 577), "NOT LIVE DATA", font=font(body_size), fill=(196, 181, 183))
    else:
        frame.paste(diagram.resize((340, 215), Image.Resampling.LANCZOS), (22, 85))
        draw = ImageDraw.Draw(frame)
        draw.text((407, 116), label, font=font(49), fill=PAPER)
        draw.text((410, 189), "ILLUSTRATIVE ART", font=font(body_size), fill=SIGNAL)
        draw.text((410, 235), "NOT LIVE DATA", font=font(body_size), fill=(196, 181, 183))
    return frame


def build_poster(mobile=False):
    return build_frame(0, mobile).quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def build_systems_reel_gif(mobile=False):
    frames = [build_frame(index, mobile) for index in range(FRAME_COUNT)]
    # A shared palette prevents frame-to-frame shimmer and keeps transfers small.
    palette = build_poster(mobile)
    indexed = [palette.copy(), *[frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames[1:]]]
    buffer = BytesIO()
    indexed[0].save(buffer, format="GIF", save_all=True, append_images=indexed[1:],
                    duration=FRAME_DURATION, loop=0, optimize=True, disposal=1,
                    comment=b"Illustrative systems motion study - Ayush Roy")
    return buffer.getvalue()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for mobile, stem in ((False, "systems-reel-v2"), (True, "systems-reel-mobile-v2")):
        path = OUT_DIR / f"{stem}.gif"
        payload = build_systems_reel_gif(mobile)
        path.write_bytes(payload)
        build_poster(mobile).save(OUT_DIR / f"{stem}-still.png", optimize=True)
        print(f"wrote {path.name} ({len(payload) / 1024:.1f} KB, {FRAME_COUNT} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

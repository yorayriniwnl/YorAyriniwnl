#!/usr/bin/env python3
"""Render seamless systems reels and reduced-motion posters.

The imagery is an illustrative motion study, not simulated live telemetry.
Both layouts use the same scenes and palette, with no external assets or fonts.
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_data import load_profile

ROOT = SCRIPT_DIR.parent
OUT_DIR = ROOT / "generated"
WIDTH, HEIGHT = 1200, 280
MOBILE_SIZE = (600, 530)
# A near-four-second loop at 70 ms/frame keeps the motion fluid while
# respecting GitHub profile transfer budgets on both desktop and mobile.
FRAME_COUNT = 54
FRAME_DURATION = 70
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


def rgba(color, alpha):
    return (*color, max(0, min(255, int(alpha))))


def glow_point(glow, x, y, radius, color, alpha=150):
    for multiplier, opacity in ((4.2, .08), (2.4, .16), (1.35, .28)):
        r = radius * multiplier
        glow.ellipse((x - r, y - r, x + r, y + r), fill=rgba(color, alpha * opacity))


def draw_particles(draw, glow, cx, cy, phase):
    for radius, opacity in ((104, .18), (78, .28), (51, .42)):
        draw.ellipse((cx - radius, cy - radius * .42, cx + radius, cy + radius * .42),
                     outline=mix((35, 8, 14), SIGNAL, opacity), width=1)
        draw.arc((cx - radius, cy - radius * .42, cx + radius, cy + radius * .42),
                 int(phase * 360 + radius), int(phase * 360 + radius + 125),
                 fill=mix(DEEP, SIGNAL, opacity + .12), width=1)
    particles = []
    for ring in range(20):
        u = ring / 20 * TAU
        for spoke in range(10):
            v = spoke / 10 * TAU
            shell = 56 + 20 * math.cos(v) + 8 * math.sin(u * 2 + v)
            x, y, z = project(shell * math.cos(u), 22 * math.sin(v), shell * math.sin(u), phase * TAU, .72)
            particles.append((z, cx + x * 1.18, cy + y, 1.05 + (z + 82) / 105, ring))
    for z, x, y, r, ring in sorted(particles):
        light = max(.12, min(1, (z + 85) / 155))
        color = mix((42, 10, 13), SIGNAL, light)
        point(draw, x, y, r, color)
        if light > .76 and ring % 4 == 0:
            glow_point(glow, x, y, r, SIGNAL, 130)
    for index in range(3):
        orbit = phase + index / 3
        x = cx + math.cos(orbit * TAU) * (86 - index * 15)
        y = cy + math.sin(orbit * TAU) * (34 - index * 6)
        point(draw, x, y, 2.4 - index * .35, PAPER)
        glow_point(glow, x, y, 2.6, SIGNAL, 155)
    draw.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), fill=(13, 4, 9), outline=SIGNAL, width=1)
    point(draw, cx, cy, 4.5, SIGNAL)
    glow_point(glow, cx, cy, 5, SIGNAL, 180)
    draw.line((cx - 128, cy, cx + 128, cy), fill=(79, 18, 29), width=1)
    draw.line((cx, cy - 55, cx, cy + 55), fill=(79, 18, 29), width=1)


def draw_streams(draw, glow, cx, cy, phase):
    for lane in range(9):
        points = []
        for sample in range(84):
            t = sample / 83
            envelope = math.sin(t * math.pi)
            wave = math.sin(t * TAU * 1.4 - phase * TAU + lane * .31)
            wave += .35 * math.sin(t * TAU * 3.2 + phase * TAU * .4 - lane)
            points.append((cx - 116 + t * 232, cy + (lane - 4) * 9 + wave * 19 * envelope))
        intensity = .82 if lane in (3, 4) else .12 + (lane % 3) * .08
        color = mix((49, 12, 17), SIGNAL, intensity)
        draw.line(points, fill=color, width=2 if lane in (3, 4) else 1)
        if lane in (3, 4):
            draw.line([(x, y + 3) for x, y in points], fill=(104, 25, 37), width=1)
        position = (phase * 1.15 + lane / 9) % 1
        for trail in range(5, -1, -1):
            trail_pos = (position - trail * .018) % 1
            px = cx - 116 + trail_pos * 232
            envelope = math.sin(trail_pos * math.pi)
            py = cy + (lane - 4) * 9 + (
                math.sin(trail_pos * TAU * 1.4 - phase * TAU + lane * .31)
                + .35 * math.sin(trail_pos * TAU * 3.2 + phase * TAU * .4 - lane)
            ) * 19 * envelope
            alpha = (1 - trail / 7) * envelope
            point(draw, px, py, 2.8 if trail == 0 else 1.3, mix((30, 6, 10), SIGNAL, alpha))
            if trail == 0:
                glow_point(glow, px, py, 3.2, SIGNAL, int(160 * alpha))
    gate = cx - 116 + ((phase * 1.15) % 1) * 232
    draw.line((gate, cy - 73, gate, cy + 73), fill=SIGNAL, width=1)
    draw.line((gate + 3, cy - 73, gate + 3, cy + 73), fill=(82, 20, 31), width=1)
    glow_point(glow, gate, cy, 4, SIGNAL, 110)


def draw_vision(draw, glow, cx, cy, phase):
    scan_y = cy + math.sin(phase * TAU) * 45
    left, top, right, bottom = cx - 105, cy - 53, cx + 105, cy + 53
    draw.rounded_rectangle((left, top, right, bottom), radius=8, fill=(10, 4, 9), outline=(75, 18, 28), width=1)
    for row in range(13):
        for col in range(27):
            x, y = cx - 98 + col * 7.5, cy - 45 + row * 7.5
            texture = (math.sin(col * .77 + row * .43) + math.cos(col * .21 - row * .82) + 2) / 4
            proximity = max(0, 1 - abs(y - scan_y) / 24)
            focus = max(0, 1 - math.hypot(x - (cx + 18), y - (cy - 3)) / 86)
            color = mix((24, 7, 12), SIGNAL, texture * (.2 + proximity * .58 + focus * .25))
            size = 1.8 + texture * 1.8 + proximity * 1.2
            draw.rectangle((x - size / 2, y - size / 2, x + size / 2, y + size / 2), fill=color)
    draw.rounded_rectangle((cx - 38, cy - 31, cx + 54, cy + 34), radius=4,
                           outline=(176, 46, 57), width=1)
    draw.line((cx - 38, cy - 31, cx - 25, cy - 31), fill=PAPER, width=2)
    draw.line((cx + 54, cy + 34, cx + 41, cy + 34), fill=PAPER, width=2)
    for sign_x in (-1, 1):
        for sign_y in (-1, 1):
            x, y = cx + sign_x * 112, cy + sign_y * 58
            draw.line([(x - sign_x * 15, y), (x, y), (x, y - sign_y * 15)], fill=CRIMSON, width=2)
    draw.line((cx - 99, scan_y, cx + 99, scan_y), fill=SIGNAL, width=1)
    draw.line((cx - 99, scan_y + 2, cx + 99, scan_y + 2), fill=(97, 23, 34), width=1)
    glow_point(glow, cx, scan_y, 4, SIGNAL, 135)
    sample_x = cx + 18 + math.sin(phase * TAU) * 31
    sample_y = cy - 3 + math.cos(phase * TAU) * 24
    point(draw, sample_x, sample_y, 3.2, PAPER)
    glow_point(glow, sample_x, sample_y, 4, PAPER, 125)
    draw.line((cx - 5, cy, cx + 5, cy), fill=PAPER, width=1)
    draw.line((cx, cy - 5, cx, cy + 5), fill=PAPER, width=1)


def draw_network(draw, glow, cx, cy, phase):
    nodes = [(cx - 108, cy + 2), (cx - 62, cy - 49), (cx + 13, cy - 55),
             (cx + 101, cy - 17), (cx + 88, cy + 45), (cx + 10, cy + 57),
             (cx - 75, cy + 47), (cx - 35, cy - 4)]
    center = (cx, cy)
    draw.ellipse((cx - 128, cy - 73, cx + 128, cy + 73), outline=(46, 12, 21), width=1)
    draw.arc((cx - 128, cy - 73, cx + 128, cy + 73), int(phase * 360), int(phase * 360 + 145), fill=CRIMSON, width=1)
    for i, end in enumerate(nodes):
        draw.line([center, end], fill=DEEP, width=1)
        draw.line([end, nodes[(i + 1) % len(nodes)]], fill=(47, 11, 15), width=1)
        if i % 2 == 0:
            draw.line([end, nodes[(i + 2) % len(nodes)]], fill=(37, 10, 17), width=1)
        progress = (phase * 1.2 + i / len(nodes)) % 1
        for trail in range(3, -1, -1):
            p = (progress - trail * .035) % 1
            x = cx + (end[0] - cx) * p
            y = cy + (end[1] - cy) * p
            point(draw, x, y, 2.8 if trail == 0 else 1.0, mix(DEEP, SIGNAL, math.sin(p * math.pi)))
        point(draw, *end, 6, (31, 8, 15))
        point(draw, *end, 3, SIGNAL)
        glow_point(glow, *end, 4, SIGNAL, 115)
    top, left, right, bottom = (cx, cy - 27), (cx - 30, cy - 11), (cx + 30, cy - 11), (cx, cy + 32)
    draw.polygon([top, right, (cx, cy + 4), left], fill=(50, 10, 16), outline=SIGNAL)
    draw.polygon([left, (cx, cy + 4), bottom, (cx - 30, cy + 15)], fill=(19, 5, 9), outline=CRIMSON)
    draw.polygon([(cx, cy + 4), right, (cx + 30, cy + 15), bottom], fill=(33, 7, 12), outline=CRIMSON)
    draw.line((cx - 18, cy - 3, cx + 18, cy - 3), fill=(255, 138, 127), width=1)
    point(draw, cx, cy + 4, 4, SIGNAL)
    glow_point(glow, cx, cy + 4, 5, SIGNAL, 165)


SCENES = (
    ("01", "GPU WORLDS", "PARTICLES / INTERFACES", draw_particles),
    ("02", "REALTIME", "EVENTS / SIGNALS", draw_streams),
    ("03", "VISION", "TEXTURES / FEATURES", draw_vision),
    ("04", "PLATFORMS", "APIs / CONNECTIONS", draw_network),
)


def build_backdrop(size, phase):
    width, height = size
    frame = Image.new("RGB", size)
    draw = ImageDraw.Draw(frame)
    top = (2, 2, 4)
    bottom = (17, 3, 10)
    for y in range(height):
        t = y / max(1, height - 1)
        draw.line((0, y, width, y), fill=mix(top, bottom, t))
    atmosphere = Image.new("RGBA", size, (0, 0, 0, 0))
    atmosphere_draw = ImageDraw.Draw(atmosphere)
    atmosphere_draw.ellipse((width * .02, height * .15, width * .42, height * 1.1), fill=rgba(CRIMSON, 45))
    atmosphere_draw.ellipse((width * .54, -height * .5, width * 1.08, height * .75), fill=rgba(SIGNAL, 30))
    atmosphere = atmosphere.filter(ImageFilter.GaussianBlur(max(12, height // 7)))
    frame = Image.alpha_composite(frame.convert("RGBA"), atmosphere).convert("RGB")
    draw = ImageDraw.Draw(frame)
    for y in range(8, height, 8):
        draw.line((0, y, width, y), fill=(29, 7, 14), width=1)
    scan_y = int(52 + ((phase * .72) % 1) * max(1, height - 62))
    draw.line((0, scan_y, width, scan_y), fill=(45, 10, 20), width=1)
    return frame


def _clip_layer(layer, clip_box):
    mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(clip_box, radius=7, fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    return layer


def render_scene(frame, renderer, cx, cy, phase, clip_box):
    scene = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    glow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    renderer(ImageDraw.Draw(scene), ImageDraw.Draw(glow), cx, cy, phase)
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    frame = Image.alpha_composite(frame.convert("RGBA"), _clip_layer(glow, clip_box))
    frame = Image.alpha_composite(frame, _clip_layer(scene, clip_box))
    return frame.convert("RGB")


def draw_panel_hud(draw, left, top, right, bottom, index, phase):
    color = mix((42, 10, 17), SIGNAL, .18 + index * .04)
    draw.line((left + 13, top + 70, left + 13, bottom - 42), fill=color, width=1)
    draw.line((left + 13, top + 70, left + 23, top + 70), fill=SIGNAL, width=1)
    for tick in range(4):
        x = right - 45 + tick * 8
        tick_h = 3 + ((index + tick) % 3) * 2
        draw.line((x, bottom - 16, x, bottom - 16 - tick_h), fill=(112, 29, 39), width=1)
    radius = 8 + index * 2
    draw.arc((right - 22 - radius, top + 14 - radius, right - 22 + radius, top + 14 + radius),
             int(phase * 360 + index * 40), int(phase * 360 + index * 40 + 94), fill=SIGNAL, width=1)
    point(draw, right - 22, top + 14, 2, SIGNAL)


def build_frame(frame_index, mobile=False, compact=True):
    phase = (frame_index % FRAME_COUNT) / FRAME_COUNT
    size = MOBILE_SIZE if mobile else (WIDTH, HEIGHT)
    frame = build_backdrop(size, phase)
    draw = ImageDraw.Draw(frame)
    columns = 2 if mobile else 4
    margin, gap, top = 16, 12, 64
    panel_w = (size[0] - 2 * margin - (columns - 1) * gap) // columns
    panel_h = 217 if mobile else 200
    draw.text((20, 16), "THE SYSTEMS I BUILD", font=font(23), fill=PAPER)
    if not mobile:
        draw.text((937, 22), "ILLUSTRATIVE MOTION STUDY", font=font(13), fill=(166, 131, 140))
    draw.line((20, 49, size[0] - 20, 49), fill=(52, 15, 21), width=1)
    draw.line((20, 49, 80, 49), fill=SIGNAL, width=1)

    for index, (code, label, note, renderer) in enumerate(SCENES):
        left = margin + (index % columns) * (panel_w + gap)
        y = top + (index // columns) * (panel_h + gap)
        right, bottom = left + panel_w, y + panel_h
        draw.rounded_rectangle((left, y, right, bottom), radius=7, fill=(8, 5, 8), outline=(67, 21, 28), width=1)
        draw.rounded_rectangle((left + 5, y + 5, right - 5, bottom - 5), radius=5, outline=(27, 9, 16), width=1)
        draw.line((left + 13, y + 5, right - 13, y + 5), fill=(116, 29, 39), width=1)
        draw.text((left + 14, y + 13), label, font=font(25), fill=PAPER)
        draw.text((right - 32, y + 18), code, font=font(13), fill=CRIMSON)
        draw.line((left + 14, bottom - 32, right - 14, bottom - 32), fill=(52, 15, 21), width=1)
        draw_panel_hud(draw, left, y, right, bottom, index, phase)
        frame = render_scene(
            frame,
            renderer,
            (left + right) / 2,
            y + (113 if mobile else 104),
            phase,
            (left + 2, y + 2, right - 2, bottom - 2),
        )
        draw = ImageDraw.Draw(frame)
        draw.text((left + 14, bottom - 23), note, font=font(13), fill=(177, 145, 154))
        draw.line((right - 27, bottom - 18, right - 14, bottom - 18), fill=CRIMSON, width=1)
    # The reel encoder applies a smaller shared palette later. Returning a
    # compact poster here keeps the reduced-motion PNG fallback lightweight
    # as well, without changing its dimensions or its visual hierarchy.
    if compact:
        return frame.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return frame


def build_systems_reel_gif(mobile=False):
    # Keep GIF quantization based on the full RGB render; the compact palette
    # returned by build_frame is reserved for still-image fallbacks.
    frames = [build_frame(index, mobile, compact=False) for index in range(FRAME_COUNT)]
    # A shared palette prevents frame-to-frame shimmer and keeps transfers small.
    # Keep the reels visually deep without making a profile README pay for a
    # photographic palette. The small, shared palette also prevents shimmer
    # between frames and materially improves GitHub's transfer time.
    palette = frames[0].quantize(colors=20, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    buffer = BytesIO()
    indexed[0].save(buffer, format="GIF", save_all=True, append_images=indexed[1:],
                    duration=FRAME_DURATION, loop=0, optimize=True, disposal=1,
                    comment=b"Illustrative systems motion study - Ayush Roy")
    return buffer.getvalue()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for mobile, stem in ((False, "systems-reel"), (True, "systems-reel-mobile")):
        path = OUT_DIR / f"{stem}.gif"
        payload = build_systems_reel_gif(mobile)
        path.write_bytes(payload)
        build_frame(0, mobile).save(OUT_DIR / f"{stem}-still.png", optimize=True)
        print(f"wrote {path.name} ({len(payload) / 1024:.1f} KB, {FRAME_COUNT} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

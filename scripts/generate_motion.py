#!/usr/bin/env python3
"""Generate the compact animated visual decoder used by the profile README."""

from __future__ import annotations

import math
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_data import load_profile


ROOT = SCRIPT_DIR.parent
OUT_DIR = ROOT / "generated"
OUTPUT = OUT_DIR / "kinetic-primer.gif"
WIDTH, HEIGHT = 1200, 240
FRAME_COUNT = 24

PROFILE = load_profile()
PALETTE = PROFILE["visual_contract"]["palette"]


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


VOID = rgb(PALETTE["void"])
PANEL = rgb(PALETTE["panel"])
CRIMSON = rgb(PALETTE["crimson"])
DEEP = rgb(PALETTE["deep_crimson"])
SIGNAL = rgb(PALETTE["signal"])
PAPER = rgb(PALETTE["paper"])
MUTED = rgb(PALETTE["muted"])


def font(size: int) -> ImageFont.ImageFont:
    """Use Pillow's bundled font for identical rendering on every runner."""
    return ImageFont.load_default(size=size)


def mix(left: tuple[int, int, int], right: tuple[int, int, int], amount: float):
    return tuple(round(a + (b - a) * amount) for a, b in zip(left, right))


def draw_background(draw: ImageDraw.ImageDraw, phase: float) -> None:
    for y in range(HEIGHT):
        depth = y / max(HEIGHT - 1, 1)
        draw.line((0, y, WIDTH, y), fill=mix(VOID, (22, 3, 3), depth * .75))

    for x in range(0, WIDTH, 24):
        draw.line((x, 44, x, HEIGHT), fill=(30, 7, 7), width=1)
    for y in range(52, HEIGHT, 24):
        draw.line((0, y, WIDTH, y), fill=(30, 7, 7), width=1)

    scan_x = int((phase % 1.0) * (WIDTH + 220)) - 110
    for offset in range(-42, 43):
        strength = max(0.0, 1 - abs(offset) / 43) * .24
        color = mix(VOID, SIGNAL, strength)
        draw.line((scan_x + offset, 44, scan_x + offset, HEIGHT), fill=color)

    draw.line((0, 43, WIDTH, 43), fill=DEEP, width=1)
    draw.line((0, HEIGHT - 2, WIDTH, HEIGHT - 2), fill=DEEP, width=1)


def draw_corner_brackets(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    length = 13
    for points in (
        ((left + 8, top + length + 8), (left + 8, top + 8), (left + length + 8, top + 8)),
        ((right - length - 8, top + 8), (right - 8, top + 8), (right - 8, top + length + 8)),
        ((left + 8, bottom - length - 8), (left + 8, bottom - 8), (left + length + 8, bottom - 8)),
        ((right - length - 8, bottom - 8), (right - 8, bottom - 8), (right - 8, bottom - length - 8)),
    ):
        draw.line(points, fill=CRIMSON, width=2)


def draw_gpu(draw: ImageDraw.ImageDraw, box, phase: float) -> None:
    left, top, right, bottom = box
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2 + 2
    spacing = 19
    coords = []
    for row in range(4):
        for col in range(6):
            x = center_x + (col - 2.5) * spacing
            y = center_y + (row - 1.5) * spacing
            coords.append((x, y, row, col))

    for x, y, row, col in coords:
        if col < 5:
            draw.line((x, y, x + spacing, y), fill=(50, 10, 10), width=1)
        if row < 3:
            draw.line((x, y, x, y + spacing), fill=(50, 10, 10), width=1)

    for index, (x, y, _row, _col) in enumerate(coords):
        pulse = (math.sin(phase * math.tau + index * .72) + 1) / 2
        radius = 2 + round(pulse * 3)
        color = mix(DEEP, SIGNAL, .35 + pulse * .65)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def draw_realtime(draw: ImageDraw.ImageDraw, box, phase: float) -> None:
    left, top, right, bottom = box
    center = (top + bottom) / 2 + 3
    points = []
    for index in range(88):
        progress = index / 87
        x = left + 20 + progress * (right - left - 40)
        envelope = .55 + .45 * math.sin(progress * math.pi)
        y = center + math.sin(progress * math.tau * 2.4 - phase * math.tau) * 28 * envelope
        points.append((x, y))
    draw.line(points, fill=CRIMSON, width=3)
    draw.line((left + 20, center, right - 20, center), fill=(52, 10, 10), width=1)
    marker = points[int((phase % 1.0) * (len(points) - 1))]
    draw.ellipse((marker[0] - 7, marker[1] - 7, marker[0] + 7, marker[1] + 7), outline=SIGNAL, width=2)
    draw.ellipse((marker[0] - 3, marker[1] - 3, marker[0] + 3, marker[1] + 3), fill=PAPER)


def draw_vision(draw: ImageDraw.ImageDraw, box, phase: float) -> None:
    left, top, right, bottom = box
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2 + 2
    radius = 47
    draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), outline=CRIMSON, width=2)
    draw.ellipse((center_x - 25, center_y - 25, center_x + 25, center_y + 25), outline=PAPER, width=2)
    draw.ellipse((center_x - 7, center_y - 7, center_x + 7, center_y + 7), fill=SIGNAL)
    draw.line((center_x - radius - 18, center_y, center_x + radius + 18, center_y), fill=(80, 15, 15), width=1)
    draw.line((center_x, center_y - radius - 12, center_x, center_y + radius + 12), fill=(80, 15, 15), width=1)
    scan_y = center_y - radius + round((phase % 1.0) * radius * 2)
    draw.line((center_x - radius, scan_y, center_x + radius, scan_y), fill=SIGNAL, width=2)
    corner = 22
    draw.line((center_x - 64, center_y - 55, center_x - 64 + corner, center_y - 55), fill=CRIMSON, width=3)
    draw.line((center_x - 64, center_y - 55, center_x - 64, center_y - 55 + corner), fill=CRIMSON, width=3)
    draw.line((center_x + 64, center_y + 55, center_x + 64 - corner, center_y + 55), fill=CRIMSON, width=3)
    draw.line((center_x + 64, center_y + 55, center_x + 64, center_y + 55 - corner), fill=CRIMSON, width=3)


def draw_systems(draw: ImageDraw.ImageDraw, box, phase: float) -> None:
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    nodes = (
        (left + width * .20, top + height * .30),
        (left + width * .50, top + height * .18),
        (left + width * .80, top + height * .34),
        (left + width * .72, top + height * .74),
        (left + width * .35, top + height * .78),
    )
    edges = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (1, 3))
    for start, end in edges:
        draw.line((*nodes[start], *nodes[end]), fill=(83, 18, 18), width=2)
    for index, (x, y) in enumerate(nodes):
        pulse = (math.sin(phase * math.tau + index * .9) + 1) / 2
        radius = 7 + round(pulse * 4)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=PANEL, outline=CRIMSON, width=2)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=SIGNAL)

    path = edges[int((phase % 1.0) * len(edges)) % len(edges)]
    local = (phase * len(edges)) % 1.0
    start, end = nodes[path[0]], nodes[path[1]]
    marker_x = start[0] + (end[0] - start[0]) * local
    marker_y = start[1] + (end[1] - start[1]) * local
    draw.ellipse((marker_x - 5, marker_y - 5, marker_x + 5, marker_y + 5), fill=PAPER)


def build_frame(frame_index: int) -> Image.Image:
    phase = frame_index / FRAME_COUNT
    image = Image.new("RGB", (WIDTH, HEIGHT), VOID)
    draw = ImageDraw.Draw(image)
    draw_background(draw, phase)

    draw.text((20, 13), "VISUAL DECODER // KINETIC PRIMER", font=font(16), fill=SIGNAL)
    right_label = "04 SIGNALS / CONTINUOUS LOOP"
    right_bbox = draw.textbbox((0, 0), right_label, font=font(13))
    draw.text((WIDTH - 20 - (right_bbox[2] - right_bbox[0]), 15), right_label, font=font(13), fill=MUTED)

    margin = 18
    gap = 12
    panel_width = (WIDTH - margin * 2 - gap * 3) // 4
    labels = (
        ("01", "GPU FIELD", "4K PARTICLES", draw_gpu),
        ("02", "REALTIME", "LIVE SIGNAL", draw_realtime),
        ("03", "VISION", "TEXTURE SCAN", draw_vision),
        ("04", "SYSTEMS", "CONNECTED CORE", draw_systems),
    )

    for index, (code, title, note, renderer) in enumerate(labels):
        left = margin + index * (panel_width + gap)
        box = (left, 54, left + panel_width, HEIGHT - 14)
        draw.rounded_rectangle(box, radius=7, fill=(5, 1, 1), outline=DEEP, width=2)
        draw.rectangle((left, 54, left + 5, HEIGHT - 14), fill=CRIMSON if index in (0, 3) else DEEP)
        draw_corner_brackets(draw, box)
        draw.text((left + 18, 67), f"SIGNAL // {code}", font=font(12), fill=MUTED)
        draw.text((left + 18, 88), title, font=font(19), fill=PAPER)
        renderer(draw, (left + 20, 104, left + panel_width - 20, HEIGHT - 42), phase)
        draw.text((left + 18, HEIGHT - 34), note, font=font(11), fill=CRIMSON)
        status_x = left + panel_width - 27
        pulse = int(2 + ((math.sin(phase * math.tau + index) + 1) / 2) * 3)
        draw.ellipse((status_x - pulse, 73 - pulse, status_x + pulse, 73 + pulse), fill=SIGNAL)

    return image


def build_kinetic_primer_gif() -> bytes:
    frames = [build_frame(index) for index in range(FRAME_COUNT)]
    palette = frames[0].quantize(
        colors=64,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    indexed = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in frames
    ]
    buffer = BytesIO()
    indexed[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=indexed[1:],
        duration=80,
        loop=0,
        optimize=False,
        disposal=2,
        comment=b"YorAyriniwnl kinetic visual decoder",
    )
    return buffer.getvalue()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_kinetic_primer_gif()
    OUTPUT.write_bytes(payload)
    print(f"wrote {OUTPUT} ({len(payload) / 1024:.1f} KB, {FRAME_COUNT} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create deterministic, web-sized derivatives of approved profile artwork."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"


class AssetRecipe(NamedTuple):
    source: str
    output: str
    max_size: tuple[int, int]
    quality: int = 84


RECIPES = (
    AssetRecipe("hero-keyart-v2.png", "hero-keyart-v2-optimized.jpg", (1600, 900), 86),
    AssetRecipe("project-helios-keyart-v3.png", "project-helios-keyart-v3-optimized.jpg", (900, 506), 70),
    AssetRecipe("project-zenith-keyart-v3.png", "project-zenith-keyart-v3-optimized.jpg", (900, 506), 70),
    AssetRecipe("project-vision-keyart-v3.png", "project-vision-keyart-v3-optimized.jpg", (900, 506), 70),
    AssetRecipe("project-talks-keyart-v3.png", "project-talks-keyart-v3-optimized.jpg", (900, 506), 70),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approved_hero_contract() -> tuple[Path, str]:
    # Read only the hero contract here. Full profile validation intentionally
    # runs after optimization, because a new derivative cannot exist until
    # this script has created it.
    with (ROOT / "data" / "profile.json").open(encoding="utf-8") as stream:
        contract = json.load(stream)["visual_contract"]
    return ROOT / contract["approved_hero"], contract["approved_hero_sha256"]


def optimize_asset(recipe: AssetRecipe) -> tuple[int, int]:
    source = ASSET_DIR / recipe.source
    output = ASSET_DIR / recipe.output
    temporary = output.with_name(f"{output.stem}.tmp{output.suffix}")

    before = source.stat().st_size
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        image.thumbnail(recipe.max_size, Image.Resampling.LANCZOS)
        image.save(
            temporary,
            "JPEG",
            quality=recipe.quality,
            optimize=True,
            progressive=True,
            subsampling=2,
        )
    temporary.replace(output)
    return before, output.stat().st_size


def validate_optimized_assets() -> None:
    hero_path, expected_hero_sha = approved_hero_contract()
    if sha256(hero_path) != expected_hero_sha:
        raise ValueError("approved hero source changed during optimization")

    for recipe in RECIPES:
        source = ASSET_DIR / recipe.source
        output = ASSET_DIR / recipe.output
        if not output.is_file():
            raise ValueError(f"optimized asset is missing: {output}")
        if output.stat().st_size >= source.stat().st_size:
            raise ValueError(f"optimized asset is not smaller than its source: {output}")
        with Image.open(output) as image:
            if image.format != "JPEG" or image.mode != "RGB":
                raise ValueError(f"optimized asset must be an RGB JPEG: {output}")
            if image.width > recipe.max_size[0] or image.height > recipe.max_size[1]:
                raise ValueError(f"optimized asset exceeds its size budget: {output}")
            if image.getexif():
                raise ValueError(f"optimized asset contains EXIF metadata: {output}")


def main() -> int:
    hero_path, expected_hero_sha = approved_hero_contract()
    before_hero_sha = sha256(hero_path)
    if before_hero_sha != expected_hero_sha:
        raise ValueError("approved hero source does not match the visual contract")

    total_before = 0
    total_after = 0
    for recipe in RECIPES:
        before, after = optimize_asset(recipe)
        total_before += before
        total_after += after
        reduction = (1 - after / before) * 100
        print(f"optimized {recipe.source} -> {recipe.output}: {before:,} -> {after:,} bytes ({reduction:.1f}% smaller)")

    validate_optimized_assets()
    if sha256(hero_path) != before_hero_sha:
        raise ValueError("approved hero source changed during optimization")

    reduction = (1 - total_after / total_before) * 100
    print(f"optimized artwork total: {total_before:,} -> {total_after:,} bytes ({reduction:.1f}% smaller)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

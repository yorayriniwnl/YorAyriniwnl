#!/usr/bin/env python3
"""Create deterministic delivery derivatives of approved source artwork.

The original PNGs remain canonical. This pipeline only creates versioned JPEG
delivery files from those sources. The approved profile portrait can therefore
never be silently re-generated or replaced by an image model. Historical
upscaled files are retained as an archive, but are intentionally not rebuilt or
described as native 4K artwork.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "assets"


class AssetRecipe(NamedTuple):
    source: str
    output: str
    target_size: tuple[int, int]
    quality: int = 84
    sharpen_percent: int = 110


RECIPES = (
    # These are the derivatives embedded in the self-contained GitHub SVGs.
    # Their 1.5-2x display density keeps the README sharp without making each
    # generated card carry a multi-megabyte photographic payload.
    AssetRecipe("hero-keyart-v2.png", "hero-keyart-v2-optimized.jpg", (2400, 1110), 84),
    AssetRecipe("project-helios-atmosphere-crimson-v2.png", "project-helios-atmosphere-crimson-v2-optimized.jpg", (1800, 1013), 82),
    AssetRecipe("project-zenith-atmosphere-crimson-v2.png", "project-zenith-atmosphere-crimson-v2-optimized.jpg", (1800, 1013), 82),
    AssetRecipe("project-vision-atmosphere-crimson-v2.png", "project-vision-atmosphere-crimson-v2-optimized.jpg", (1800, 1013), 82),
    AssetRecipe("project-talks-atmosphere-crimson-v2.png", "project-talks-atmosphere-crimson-v2-optimized.jpg", (1800, 1013), 82),
)

LEGACY_UPSCALED_RECIPES = (
    # Retained files from the earlier release. They are not native 4K sources
    # and are deliberately excluded from the active generation path.
    AssetRecipe("hero-keyart-v2.png", "hero-keyart-v2-4k.jpg", (3840, 1777), 88, 118),
    AssetRecipe("project-helios-keyart-v5.png", "project-helios-keyart-v5-4k.jpg", (3840, 2160), 88, 118),
    AssetRecipe("project-zenith-keyart-v5.png", "project-zenith-keyart-v5-4k.jpg", (3840, 2160), 88, 118),
    AssetRecipe("project-vision-keyart-v5.png", "project-vision-keyart-v5-4k.jpg", (3840, 2160), 88, 118),
    AssetRecipe("project-talks-keyart-v5.png", "project-talks-keyart-v5-4k.jpg", (3840, 2160), 88, 118),
)
# Backwards-compatible name for older local checks. New code should use the
# honest archive terminology above.
FOUR_K_RECIPES = LEGACY_UPSCALED_RECIPES


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
        image = ImageOps.fit(
            image,
            recipe.target_size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        image = image.filter(
            ImageFilter.UnsharpMask(radius=1.1, percent=recipe.sharpen_percent, threshold=3)
        )
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
            if image.size != recipe.target_size:
                raise ValueError(
                    f"optimized asset has the wrong dimensions: {output} "
                    f"({image.size}, expected {recipe.target_size})"
                )
            if image.getexif():
                raise ValueError(f"optimized asset contains EXIF metadata: {output}")


def validate_four_k_assets() -> None:
    """Validate retained legacy files without endorsing their old label."""
    for recipe in LEGACY_UPSCALED_RECIPES:
        source = ASSET_DIR / recipe.source
        output = ASSET_DIR / recipe.output
        if not output.is_file():
            raise ValueError(f"legacy upscaled asset is missing: {output}")
        if output.stat().st_size >= source.stat().st_size:
            raise ValueError(f"legacy upscaled asset is unexpectedly larger than its PNG source: {output}")
        with Image.open(output) as image:
            if image.format != "JPEG" or image.mode != "RGB":
                raise ValueError(f"legacy upscaled asset must be an RGB JPEG: {output}")
            if image.size != recipe.target_size:
                raise ValueError(
                    f"legacy upscaled asset has the wrong dimensions: {output} "
                    f"({image.size}, expected {recipe.target_size})"
                )
            if image.getexif():
                raise ValueError(f"legacy upscaled asset contains EXIF metadata: {output}")


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
    validate_four_k_assets()
    if sha256(hero_path) != before_hero_sha:
        raise ValueError("approved hero source changed during optimization")

    reduction = (1 - total_after / total_before) * 100
    print(f"optimized artwork total: {total_before:,} -> {total_after:,} bytes ({reduction:.1f}% smaller)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

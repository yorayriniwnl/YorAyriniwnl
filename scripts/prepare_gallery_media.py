"""Optimize reviewed browser captures, using only resizing and JPEG encoding."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "assets/gallery"


def main():
    gallery = json.loads((ROOT / "data/gallery.json").read_text(encoding="utf-8"))
    records = []
    for project_id in gallery["featured"]:
        spec = gallery["projects"][project_id]
        source = MEDIA / (Path(spec["media"]).stem + ".png")
        target = MEDIA / spec["media"]
        with Image.open(source) as image:
            original_size = image.size
            image = image.convert("RGB")
            image.thumbnail((1100, 720), Image.Resampling.LANCZOS)
            image.save(target, "JPEG", quality=82, optimize=True, progressive=True, subsampling=0)
        records.append({
            "project": project_id, "source_url": spec["media_url"],
            "captured_on": gallery["checked_at"], "scope": spec["media_note"],
            "source": source.name, "source_size": original_size,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "optimized": target.name, "optimized_bytes": target.stat().st_size,
            "optimized_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "processing": "Resize and JPEG encoding only; no synthetic UI",
        })
        print(f"optimized {target.name}: {target.stat().st_size:,} bytes")
    (MEDIA / "manifest.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# AYR / The Proof Gallery

The GitHub profile is an image-led gallery, not a JavaScript website. Its native
links, responsive pictures, and closed-by-default details panels work within
GitHub's Markdown renderer. `PROFILE.md` is the selectable, animation-free edition.

## Content and artwork contracts

- `data/profile.json` owns public biographical facts, project links, and stacks.
- `data/gallery.json` owns gallery order, presentation copy, source-review scope,
  and the dated provenance of the three published-interface captures.
- `assets/gallery/manifest.json` records original capture and optimized-image hashes.
  Screenshot resizing and JPEG encoding do not fabricate UI or product behavior.
- `scripts/gallery.py` owns the responsive visual system and snapshot cards.
- The approved hero SVG and original portrait are hash-locked. The reverted live
  graph and rotating-earth experiment must not be reintroduced.
- CGPA, private phone numbers, and retired public contact information stay out of
  canonical data, both profile editions, and the public resume. The private DOCX
  is not a generated output and must not be edited by this pipeline.

## Local build and verification

Use Python with `requirements-profile.txt` installed. Run each command successfully
before continuing to the next one:

```text
python scripts/profile_data.py
python scripts/optimize_assets.py
python scripts/prepare_gallery_media.py
python scripts/generate_assets.py
python scripts/generate_motion.py
python scripts/generate_readme.py
python scripts/generate_stats.py --overview-only
python scripts/generate_contributions.py
python scripts/generate_readme.py --check
python -m unittest discover -s tests -v
python scripts/preview_profile.py --refresh-markup
```

The preview binds only to `127.0.0.1:8765`. Its optional Markdown request uses
GitHub's sanitizer; the surrounding layout is an approximation. Inspect the real
GitHub profile after publishing. `/inspect?layout=mobile` and
`/inspect?layout=desktop` expose inline SVGs for text-geometry checks.

The static SVG budget is 2,500,000 bytes, including both responsive variants and
the unchanged hero. Each optional GIF must remain below 500,000 bytes, with a
matching first-frame PNG below 50,000 bytes. New body typography targets at least
14 CSS pixels at tested narrow content widths; the protected legacy hero is an
explicit exception. The signal GIF is illustrative art, not a product recording.

## Public data and publishing

`main` owns source, README, text edition, reviewed captures, and public PDF.
`output` owns generated SVGs, GIFs, posters, `public-record.json`, and
`contribution-record.json`. The latter files expose selectable numbers and dates
matching the visual cards. Never publish `--sample` output as real statistics.

For a coordinated release, first verify remote refs and a clean source worktree,
then use a separate output worktree. Copy the exact generated release files,
preserving unrelated output assets. Commit source and artwork separately and
push both branches atomically. Verify the remote refs, raw asset contents, and
actual rendered profile; a local commit alone does not establish publication.
The legacy `update-profile.ps1` does not publish every gallery artifact and is
not the gallery release path.

The three output-writing workflows share one concurrency group. The static
workflow preserves independently refreshed record and contribution cards.
Versioned filenames avoid old image-cache entries on structural redesigns.
Keep prior output assets in Git history for rollback; never restore a reverted
hero variant merely because an old generator or file still exists.

As checked on 2026-08-31, GitHub Actions jobs were blocked before execution by an
account billing lock. Direct Git publication remains separate from scheduled
refresh availability. Dated snapshots must remain visibly dated if refreshes stop.

## Evidence limits

The three featured captures demonstrate observed public screens, not complete
backend flows. Classifier inference, authenticated solar analysis, and social
authentication/message delivery were not retested for this profile release.
Solar financial outputs are model estimates, not guarantees. The historical
24-test claim belongs to an earlier portfolio iteration. Lab entries distinguish
source inspection, in-development systems, and mismatched deployment branding.

#!/usr/bin/env python3
"""Generate the visual profile and its selectable, motion-free text edition."""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gallery import asset_name, load_gallery
from profile_data import load_profile

ROOT = SCRIPT_DIR.parent
README_PATH = ROOT / "README.md"
TEXT_PATH = ROOT / "PROFILE.md"
PROFILE_REPOSITORY = "Yorayriniwnl"
SELECTED_PROJECT_IDS = ("portfolio", "vision", "zenith", "helios", "talks", "feelings")
PROJECT_VISUALS = {key: asset_name(key) for key in SELECTED_PROJECT_IDS}
DYNAMIC_ASSETS = {"gallery-record-v1.svg", "gallery-record-mobile-v1.svg",
                  "gallery-contributions-v1.svg", "gallery-contributions-mobile-v1.svg"}
MOTION_ASSETS = {"systems-reel-v2.gif", "systems-reel-mobile-v2.gif",
                 "systems-reel-v2-still.png", "systems-reel-mobile-v2-still.png"}


def raw_asset_url(handle, filename):
    return f"https://raw.githubusercontent.com/{handle}/{PROFILE_REPOSITORY}/output/{filename}"


def record_url(handle, filename):
    return f"https://github.com/{handle}/{PROFILE_REPOSITORY}/blob/output/{filename}"


def profile_views_url(handle):
    return ("https://komarev.com/ghpvc/?"
            f"username={handle}&amp;label=PROFILE+VIEWS&amp;color=b84050&amp;"
            "style=for-the-badge&amp;abbreviated=false")


def image(filename, alt, handle, width="100%"):
    return (f'<img src="{raw_asset_url(handle, filename)}" width="{width}" '
            f'alt="{html.escape(alt, quote=True)}"/>')


def picture(stem, alt, handle):
    return ["<picture>",
            f'<source media="(max-width: 600px)" srcset="{raw_asset_url(handle, asset_name(stem, True))}"/>',
            image(asset_name(stem), alt, handle), "</picture>"]


def link(href, content):
    return [f'<a href="{html.escape(href, quote=True)}">', *content, "</a>"]


def button(href, name, label, handle):
    return f'<a href="{html.escape(href, quote=True)}">{image(asset_name("button-" + name), label, handle, "140")}</a>'


def controls(items):
    return ['<p align="center">', *items, "</p>", ""]


def summary(filename, alt, handle):
    return f'<summary><picture>{image(filename, alt, handle, "180")}</picture></summary>'


def systems_reel(handle):
    variants = (
        ("(max-width: 600px) and (prefers-reduced-motion: reduce)", "systems-reel-mobile-v2-still.png"),
        ("(prefers-reduced-motion: reduce)", "systems-reel-v2-still.png"),
        ("(max-width: 600px)", "systems-reel-mobile-v2.gif"),
    )
    return ["<picture>",
            *[f'<source media="{media}" srcset="{raw_asset_url(handle, name)}"/>' for media, name in variants],
            image("systems-reel-v2.gif", "The crimson thread: illustrative studies of interfaces, signals, and texture features. Not live data or a product recording.", handle),
            "</picture>"]


def project_block(project, handle, gallery=None):
    gallery = gallery or load_gallery()
    project_id = project["id"]
    spec = gallery["projects"][project_id]
    target = project["live"] if spec["show_site"] else project["repo"]
    description = (f'{project["name"]}. {spec["caption"]} {spec["verified_scope"]}. '
                   f'Reviewed {gallery["checked_at"]}.')
    dossier_alt = (f'{project["name"]}: {project["summary"]} '
                   f'Engineering: {spec["build"]} Evidence: {"; ".join(project["proof"])}. '
                   f'Review scope: {spec["evidence_note"]} Stack: {"; ".join(project["stack"])}.')
    actions = []
    if spec["show_site"]:
        actions.append(button(project["live"], "site", f'Open {project["name"]} website; verification scope is in its technical notes', handle))
    actions.append(button(project["repo"], "source", f'Inspect {project["name"]} source repository', handle))
    return [*link(target, picture(project_id, description, handle)), "", *controls(actions),
            "<details>", summary(asset_name("toggle"), f'Under the hood: {project["name"]}', handle), "",
            *picture("dossier-" + project_id, dossier_alt, handle), "",
            *controls([button(spec["source_url"], "evidence", f'Read the source evidence for {project["name"]}', handle)]),
            "</details>", ""]


def render_readme(profile=None):
    profile = profile or load_profile()
    gallery = load_gallery()
    handle, contact = profile["identity"]["handle"], profile["contact"]
    projects = {item["id"]: item for item in profile["projects"]}
    resume = f'https://github.com/{handle}/{PROFILE_REPOSITORY}/blob/main/output/pdf/Ayush_Roy_Resume_Public.pdf'
    text_url = f'https://github.com/{handle}/{PROFILE_REPOSITORY}/blob/main/PROFILE.md'
    lines = ["<!-- Generated from data/profile.json and data/gallery.json. Do not hand-edit. -->", "",
             '<div align="center">', "",
             *link(contact["portfolio"], [image("hero.svg", "Ayush Roy, full-stack developer and applied ML builder. Original approved hero.", handle)]), "",
             *picture("intro", profile["identity"]["positioning"] + " " + profile["availability"]["status"] + ". Remote collaboration welcome.", handle), "",
             *controls([button("#selected-systems", "projects", "Explore selected projects", handle),
                        button(resume, "resume", "Read Ayush Roy public resume", handle),
                        button(text_url, "text", "Read the selectable, motion-free text edition", handle)]),
             "</div>", "", '<a id="selected-systems"></a>', "",
             *picture("section-projects", "Selected work: product engineering, applied ML, and solar decision support", handle), ""]
    for project_id in gallery["featured"]:
        lines.extend(project_block(projects[project_id], handle, gallery))
    lines.extend(["<details>", summary(asset_name("motion-toggle"), "Explore the illustrative crimson signal motion study", handle), "",
                  *systems_reel(handle), "", "</details>", "",
                  *picture("section-lab", "Inside the lab: developing systems and experiments", handle), ""])
    for project_id in gallery["lab"]:
        lines.extend(project_block(projects[project_id], handle, gallery))
    lines.extend([
        *picture("section-builder", "Behind the systems: the builder and the learning direction", handle), "",
        *picture("builder", f'{profile["experience"][0]["role"]} at BSNL. {profile["experience"][0]["summary"]} '
                 f'{profile["education"][0]["degree"]}, KIIT, {profile["education"][0]["period"]}. '
                 'Currently learning LLMs, RAG, agents, and AWS; separate from demonstrated project work.', handle), "",
        *controls([button(resume, "resume", "Read the public resume", handle), button(text_url, "text", "Read complete skills and experience in the text edition", handle)]),
        *picture("section-record", "The public record: dated GitHub snapshots and a third-party profile view counter", handle), "",
        *link(record_url(handle, "public-record.json"), picture("record", "GitHub public repositories, stars, and followers. Open the selectable snapshot data; these are not live audience metrics.", handle)), "",
        *link(record_url(handle, "contribution-record.json"), picture("contributions", "Dated public contribution counts with a chart of the most recent thirteen weeks. Open the selectable daily data.", handle)), "",
        '<p align="center">', f'<img src="{profile_views_url(handle)}" width="280" alt="Third-party profile view counter from Komarev; not a unique-visitor or live-online measurement"/>', "</p>", "",
        *picture("section-contact", "Open a conversation about internships, products, and collaboration", handle), "",
        *link("mailto:" + contact["email"], picture("contact", "Grind. Build. Repeat. " + profile["availability"]["status"] + ". Remote collaboration welcome.", handle)), "",
        *controls([button("mailto:" + contact["email"], "email", "Email Ayush Roy", handle), button(contact["linkedin"], "linkedin", "Connect on LinkedIn", handle), button(resume, "resume", "Open the public resume", handle)]),
        *controls([button(contact["github"], "github", "Open GitHub", handle), button(contact["devpost"], "devpost", "Explore Devpost prototypes", handle), button(contact["steam"], "steam", "Open the original Steam inspiration", handle), button(contact["hub"], "hub", "Explore the separate personal hub", handle)]),
    ])
    return "\n".join(lines)


def render_text_profile(profile=None):
    profile = profile or load_profile()
    gallery = load_gallery()
    contact = profile["contact"]
    lines = ["<!-- Generated alongside README.md; selectable text and no animated images. -->", "",
             f'# {profile["identity"]["name"]}', "",
             f'{profile["identity"]["role"]} / {profile["identity"]["specialty"]}', "",
             profile["identity"]["positioning"], "", profile["availability"]["status"] + ". Open to remote collaboration.", "",
             f'[Portfolio]({contact["portfolio"]}) · [Public résumé](output/pdf/Ayush_Roy_Resume_Public.pdf) · [Email](mailto:{contact["email"]}) · [LinkedIn]({contact["linkedin"]})', "",
             f'Project-source review: {gallery["checked_at"]}. These are bounded checks, not an end-to-end certification of every deployment.', "",
             "## Selected work and experiments", ""]
    projects = {item["id"]: item for item in profile["projects"]}
    for project_id in gallery["featured"] + gallery["lab"]:
        project, spec = projects[project_id], gallery["projects"][project_id]
        lines.extend([f'### {project["name"]}', "", f'{project["status"]} · {project["period"]}', "",
                      project["summary"], "", spec["build"], "", "Evidence and reported results:", "",
                      *["- " + value for value in project["proof"]], "",
                      "Verification scope: " + spec["evidence_note"], "", "Stack: " + ", ".join(project["stack"]) + ".", "",
                      f'[Source]({project["repo"]}) · [Evidence]({spec["source_url"]})' +
                      (f' · [Published interface]({project["live"]})' if spec["show_site"] else ""), ""])
    lines.extend(["## Experience", ""])
    for item in profile["experience"]:
        lines.extend([f'### {item["role"]} — {item["organization"]}', "", item["period"] + " · " + item["location"], "", item["summary"], ""])
    lines.extend(["## Education", ""])
    for item in profile["education"]:
        lines.extend([item["degree"] + " — " + item["institution"], "", item["period"] + " · " + item["location"], "", "Coursework: " + ", ".join(item["coursework"]) + ".", ""])
    lines.extend(["## Technical range", ""])
    for key, values in profile["skills"].items():
        label = "Currently learning — not a claim of production expertise" if key == "expanding" else key.title()
        lines.extend([f'- **{label}:** ' + ", ".join(values)])
    lines.extend(["", "## Resume-reported record", ""])
    for item in profile["proof"]:
        lines.append(f'- {item["value"]} {item["label"].lower()}: {item["detail"]}.')
    lines.extend(["", "The 24-test record belongs to an earlier portfolio iteration. No current portfolio benchmark or test run is implied.", "",
                  "## Certifications and achievements", ""])
    lines.extend([f'- {item["name"]} — {item["issuer"]}, {item["date"]}' for item in profile["certifications"]])
    lines.extend(["- " + item for item in profile["achievements"]])
    lines.extend(["", "## Public record and visual provenance", "",
                  "GitHub figures are dated snapshots. When a refresh is unavailable, the date remains visible; a snapshot is not described as live. The Komarev profile-view counter is separate and must not be interpreted as unique visitors or people currently online.", "",
                  f'[Repository snapshot and timestamp (JSON)]({record_url(profile["identity"]["handle"], "public-record.json")}) · [Daily contribution counts and timestamp (JSON)]({record_url(profile["identity"]["handle"], "contribution-record.json")})', "",
                  "The gallery uses captures of the published portfolio, classifier upload screen, and Zenith interface. A capture demonstrates the observed screen, not every backend capability. Crimson filaments and the signal GIF are labeled illustrative studies, not telemetry or recorded product behavior.", "",
                  "This edition has selectable text and no animation. The visual profile keeps the approved original hero unchanged. Both editions are generated from the same profile and review data.", "",
                  f'[GitHub]({contact["github"]}) · [Devpost]({contact["devpost"]}) · [Steam]({contact["steam"]}) · [Personal hub]({contact["hub"]})', ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {README_PATH: render_readme(), TEXT_PATH: render_text_profile()}
    for path, rendered in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
                print(f"{path.name} is out of date; run scripts/generate_readme.py", file=sys.stderr)
                return 1
        else:
            path.write_text(rendered, encoding="utf-8")
            print(f"wrote {path.name} ({len(rendered):,} characters)")
    if args.check:
        print("Visual and text profiles match canonical data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

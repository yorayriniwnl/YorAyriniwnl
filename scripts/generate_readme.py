#!/usr/bin/env python3
"""Render the public GitHub profile README from the canonical profile data."""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_data import load_profile


ROOT = SCRIPT_DIR.parent
README_PATH = ROOT / "README.md"
PROFILE_REPOSITORY = "Yorayriniwnl"
SELECTED_PROJECT_IDS = ("portfolio", "vision", "zenith", "helios", "token-usage", "talks")
PROJECT_VISUALS = {
    "portfolio": "project-portfolio-v2.svg",
    "helios": "project-helios.svg",
    "zenith": "project-zenith.svg",
    "vision": "project-vision.svg",
    "token-usage": "project-token-usage.svg",
    "talks": "project-talks.svg",
}
ATLAS_ASSETS = (
    "identity-console.svg",
    "signal-strip.svg",
    "field-notes.svg",
    "skills-matrix.svg",
    "operator-gateway.svg",
    "achievement-rack.svg",
    "protocol-engineer.svg",
    "protocol-product.svg",
    "protocol-human.svg",
    "dossier-toggle.svg",
    "arsenal.svg",
    "finale.svg",
    "jump-projects.svg",
    "jump-experience.svg",
    "jump-activity.svg",
    "jump-contact.svg",
    "proof-apps.svg",
    "proof-tests.svg",
    "proof-accuracy.svg",
    "proof-prototypes.svg",
    "nav-portfolio.svg",
    "nav-projects.svg",
    "nav-resume.svg",
    "nav-linkedin.svg",
    "nav-live.svg",
    "nav-source.svg",
    "nav-email.svg",
    "nav-github.svg",
    "nav-devpost.svg",
    "nav-steam.svg",
    "section-projects.svg",
    "section-field.svg",
    "section-arsenal.svg",
    "section-record.svg",
    "section-operator.svg",
    "section-channel.svg",
    "project-dossier-portfolio.svg",
    "project-dossier-helios.svg",
    "project-dossier-zenith.svg",
    "project-dossier-vision.svg",
    "project-dossier-talks.svg",
    "project-dossier-token-usage.svg",
)
MOTION_ASSETS = (
    "systems-reel.gif",
    "systems-reel-mobile.gif",
    "systems-reel-still.png",
    "systems-reel-mobile-still.png",
)

ASSET_REVISIONS = {
    # GitHub's raw CDN can retain a recently replaced visual at the same URL.
    # Supporting assets share the saturated red atlas pass; motion gets its own
    # revision so responsive GIF and still fallbacks cannot be mixed by a stale
    # CDN edge.
    **{
        filename: "atlas-v5"
        for filename in ATLAS_ASSETS
    },
    "systems-reel.gif": "motion-v6",
    "systems-reel-mobile.gif": "motion-v6",
    "systems-reel-still.png": "motion-v6",
    "systems-reel-mobile-still.png": "motion-v6",
    "hero.svg": "raster-v2",
    "project-portfolio-v2.svg": "raster-v4",
    "project-portfolio-mobile-v2.svg": "raster-v4",
    "project-helios.svg": "raster-v9",
    "project-zenith.svg": "raster-v9",
    "project-vision.svg": "raster-v9",
    "project-talks.svg": "raster-v9",
    "project-token-usage.svg": "raster-v9",
}


def raw_asset_url(handle: str, filename: str) -> str:
    url = f"https://raw.githubusercontent.com/{handle}/{PROFILE_REPOSITORY}/output/{filename}"
    revision = ASSET_REVISIONS.get(filename)
    return f"{url}?rev={revision}" if revision else url


def profile_views_url(handle: str) -> str:
    return (
        "https://komarev.com/ghpvc/?"
        f"username={handle}&amp;label=TOTAL+PROFILE+VIEWS&amp;color=ff1f2d&amp;"
        "style=for-the-badge&amp;abbreviated=false"
    )


def image(filename: str, alt: str, handle: str, width: str = "100%") -> str:
    return (
        f'<img src="{raw_asset_url(handle, filename)}" width="{width}" '
        f'alt="{html.escape(alt, quote=True)}"/>'
    )


def linked_image(href: str, filename: str, alt: str, handle: str, width: str = "100%") -> list[str]:
    return [f'<a href="{href}">', image(filename, alt, handle, width), "</a>"]


def linked_button(href: str, filename: str, alt: str, handle: str) -> str:
    """Render a compact animated SVG control instead of a plain text link."""
    return f'<a href="{href}">{image(filename, alt, handle, "350")}</a>'


def project_details_panel(project: dict) -> list[str]:
    """Keep cover art clean while placing the authored project context below it."""
    code = f'SYS-{project["order"]:02d}'
    name = html.escape(project["name"].upper())
    status = html.escape(project["status"].upper())
    period = html.escape(project["period"].upper())
    summary = html.escape(project["summary"])
    stack = html.escape(" · ".join(project["stack"]).upper())
    proof = html.escape(" · ".join(project["proof"]))
    return [
        '<table align="center">',
        '<tr><td align="center">',
        f'<strong>{code} // {name}</strong><br/>',
        f'<sub>{status} · {period}</sub><br/><br/>',
        f'{summary}<br/><br/>',
        f'<sub>STACK · {stack}</sub><br/>',
        f'<sub>PROOF · {proof}</sub>',
        '</td></tr>',
        '</table>',
    ]


def systems_reel(handle: str) -> list[str]:
    """Use native picture selection for mobile and reduced-motion visitors."""
    variants = (
        ("(max-width: 600px) and (prefers-reduced-motion: reduce)", "systems-reel-mobile-still.png"),
        ("(prefers-reduced-motion: reduce)", "systems-reel-still.png"),
        ("(max-width: 600px)", "systems-reel-mobile.gif"),
    )
    return [
        "<picture>",
        *[
            f'<source media="{media}" srcset="{raw_asset_url(handle, filename)}"/>'
            for media, filename in variants
        ],
        image(
            "systems-reel.gif",
            "The worlds I build: a cinematic product archive, industrial telemetry, daylight solar intelligence, forensic texture vision, and realtime communication. Illustrative motion study.",
            handle,
        ),
        "</picture>",
    ]


def project_block(project: dict, handle: str) -> list[str]:
    code = f'SYS-{project["order"]:02d}'
    target = project.get("live") or project["repo"]
    dossier_alt = (
        f'{code}: {project["name"]}. {project["status"]}, {project["period"]}. '
        f'{project["summary"]} Proof: {"; ".join(project["proof"])}. '
        f'Stack: {"; ".join(project["stack"])}.'
    )
    links = []
    if project.get("live"):
        links.append(
            linked_button(
                project["live"],
                "nav-live.svg",
                f'Launch {project["name"]} live system',
                handle,
            )
        )
    links.append(
        linked_button(
            project["repo"],
            "nav-source.svg",
            f'Inspect {project["name"]} source repository',
            handle,
        )
    )

    if project["id"] == "portfolio":
        cover = [
            f'<a href="{target}">',
            "<picture>",
            f'<source media="(max-width: 600px)" srcset="{raw_asset_url(handle, "project-portfolio-mobile-v2.svg")}"/>',
            image(PROJECT_VISUALS["portfolio"], f'{project["name"]}: {project["codename"].lower()}', handle),
            "</picture>",
            "</a>",
        ]
    else:
        cover = linked_image(
            target,
            PROJECT_VISUALS[project["id"]],
            f'{project["name"]}: {project["codename"].lower()}',
            handle,
        )

    dossier_label = f'Expand {project["name"]} mission, proof, and stack'
    lines = [
        *cover,
        "",
        *project_details_panel(project),
        "",
        "<details>",
        (
            '<summary><picture>'
            f'{image("dossier-toggle.svg", dossier_label, handle, "240")}'
            '</picture></summary>'
        ),
        "",
        *linked_image(
            target,
            f'project-dossier-{project["id"]}.svg',
            dossier_alt,
            handle,
        ),
        "",
        "</details>",
        "",
        '<p align="center">',
        *links,
        "</p>",
        "",
    ]
    return lines


def render_readme(profile: dict | None = None) -> str:
    profile = profile or load_profile()
    identity = profile["identity"]
    contact = profile["contact"]
    availability = profile["availability"]
    handle = identity["handle"]
    projects = {project["id"]: project for project in profile["projects"]}
    experience = profile["experience"][0]
    education = profile["education"][0]
    skills = profile["skills"]
    resume_url = (
        f'https://github.com/{handle}/{PROFILE_REPOSITORY}/blob/main/'
        "output/pdf/Ayush_Roy_Resume_Public.pdf"
    )

    lines = [
        "<!-- Generated by scripts/generate_readme.py from data/profile.json. -->",
        "",
        '<div align="center">',
        "",
        *linked_image(
            contact["portfolio"],
            "hero.svg",
            f'{identity["name"]}, {identity["role"].lower()} and {identity["specialty"].lower()}',
            handle,
        ),
        "",
        '<p>',
        f'<a href="#selected-systems">{image("jump-projects.svg", "Jump to selected projects", handle, "160")}</a>',
        f'<a href="#field-notes">{image("jump-experience.svg", "Jump to experience and education", handle, "160")}</a>',
        f'<a href="#public-record">{image("jump-activity.svg", "Jump to GitHub activity and profile views", handle, "160")}</a>',
        f'<a href="#open-channel">{image("jump-contact.svg", "Jump to contact and collaboration", handle, "160")}</a>',
        '</p>',
        "",
        *systems_reel(handle),
        "",
        image(
            "identity-console.svg",
            (
                f'{identity["name"]}. {identity["role"]} and {identity["specialty"]}. '
                f'{identity["positioning"]} {availability["status"]}. '
                f'B.Tech {availability["graduating"]}. {identity["location"]}.'
            ),
            handle,
        ),
        "",
        '<p>',
        f'<a href="{contact["portfolio"]}">{image("nav-portfolio.svg", "Open Ayush Roy portfolio", handle, "350")}</a>',
        f'<a href="#selected-systems">{image("nav-projects.svg", "Explore Ayush Roy projects", handle, "350")}</a>',
        '<br/>',
        f'<a href="{resume_url}">{image("nav-resume.svg", "View Ayush Roy public resume", handle, "350")}</a>',
        f'<a href="{contact["linkedin"]}">{image("nav-linkedin.svg", "Open Ayush Roy LinkedIn profile", handle, "350")}</a>',
        "</p>",
        "",
        image(
            "signal-strip.svg",
            "Product engineering, realtime systems, computer vision, 3D interfaces, and applied AI",
            handle,
        ),
        "",
        '<p>',
        image(
            f'proof-{profile["proof"][0]["id"]}.svg',
            f'{profile["proof"][0]["value"]} {profile["proof"][0]["label"]}. {profile["proof"][0]["detail"]}',
            handle,
            "350",
        ),
        image(
            f'proof-{profile["proof"][1]["id"]}.svg',
            f'{profile["proof"][1]["value"]} {profile["proof"][1]["label"]}. {profile["proof"][1]["detail"]}',
            handle,
            "350",
        ),
        '<br/>',
        image(
            f'proof-{profile["proof"][2]["id"]}.svg',
            f'{profile["proof"][2]["value"]} {profile["proof"][2]["label"]}. {profile["proof"][2]["detail"]}',
            handle,
            "350",
        ),
        image(
            f'proof-{profile["proof"][3]["id"]}.svg',
            f'{profile["proof"][3]["value"]} {profile["proof"][3]["label"]}. {profile["proof"][3]["detail"]}',
            handle,
            "350",
        ),
        "</p>",
        "",
        "</div>",
        "",
        '<a id="selected-systems"></a>',
        "",
        image(
            "section-projects.svg",
            "Section 01: selected systems. Six public builds with visual proof and verified data.",
            handle,
        ),
        "",
    ]

    for project_id in SELECTED_PROJECT_IDS:
        lines.extend(project_block(projects[project_id], handle))

    lines.extend(
        [
            '<a id="field-notes"></a>',
            "",
            image(
                "section-field.svg",
                "Section 02: field notes covering verified experience, education, and trajectory.",
                handle,
            ),
            "",
            image(
                "field-notes.svg",
                (
                    f'{experience["role"]} at {experience["organization"]}, {experience["period"]}. '
                    f'{experience["summary"]} {education["degree"]} at {education["institution"]}, '
                    f'{education["period"]}. Coursework: {"; ".join(education["coursework"])}.'
                ),
                handle,
            ),
            "",
            '<p align="center">',
            linked_button(
                resume_url,
                "nav-resume.svg",
                "View Ayush Roy privacy-safe public resume",
                handle,
            ),
            "</p>",
            "",
            image("section-arsenal.svg", "Section 03: complete technical range", handle),
            "",
            image("arsenal.svg", "Ayush Roy technical range across product, backend, machine learning, and platform engineering", handle),
            "",
            image(
                "skills-matrix.svg",
                (
                    f'Product: {"; ".join(skills["product"])}. '
                    f'Backend: {"; ".join(skills["backend"])}. '
                    f'Applied ML: {"; ".join(skills["ml"])}. '
                    f'Platform: {"; ".join(skills["platform"])}. '
                    f'Currently expanding: {"; ".join(skills["expanding"])}.'
                ),
                handle,
            ),
            "",
            '<a id="public-record"></a>',
            "",
            image("section-record.svg", "Section 04: live public GitHub record with verified fallback data", handle),
            "",
            '<p align="center">',
            (
                f'<img src="{profile_views_url(handle)}" width="350" '
                'alt="Live total profile views counter"/>'
            ),
            "</p>",
            "",
            *linked_image(
                contact["github"],
                "stats.svg",
                "Ayush Roy GitHub repositories, stars, followers, languages, and system status",
                handle,
            ),
            "",
            *linked_image(
                contact["github"],
                "contribution-stream.svg",
                "Animated 365-day GitHub contribution signal for Ayush Roy",
                handle,
            ),
            "",
            image("section-operator.svg", "Section 05: interactive operator mode and protocol archive", handle),
            "",
            "<details>",
            (
                '<summary><picture>'
                f'{image("operator-gateway.svg", "Initiate the Steam-inspired operator mode", handle)}'
                '</picture></summary>'
            ),
            "",
            image("achievement-rack.svg", "Proof-of-work achievement rack", handle),
            "",
            image("protocol-engineer.svg", "Engineering protocol from constraints through feedback", handle),
            "",
            image("protocol-product.svg", "Product doctrine and learning loop", handle),
            "",
            *linked_image(
                contact["steam"],
                "protocol-human.svg",
                "Steam-inspired human signal and long-game philosophy",
                handle,
            ),
            "",
            "</details>",
            "",
            '<a id="open-channel"></a>',
            "",
            image(
                "section-channel.svg",
                "Section 06: open channel for software engineering internships, ambitious products, and collaboration",
                handle,
            ),
            "",
            '<p align="center">',
            linked_button(
                f'mailto:{contact["email"]}?subject=Next%20Transmission',
                "nav-email.svg",
                "Email Ayush Roy",
                handle,
            ),
            linked_button(
                contact["linkedin"],
                "nav-linkedin.svg",
                "Open Ayush Roy LinkedIn profile",
                handle,
            ),
            "<br/>",
            linked_button(
                contact["portfolio"],
                "nav-portfolio.svg",
                "Open Ayush Roy portfolio",
                handle,
            ),
            linked_button(
                contact["github"],
                "nav-github.svg",
                "Open Ayush Roy GitHub profile",
                handle,
            ),
            "<br/>",
            linked_button(
                contact["devpost"],
                "nav-devpost.svg",
                "Open Ayush Roy Devpost profile",
                handle,
            ),
            linked_button(
                contact["steam"],
                "nav-steam.svg",
                "Open Ayush Roy Steam profile",
                handle,
            ),
            "</p>",
            "",
            '<div align="center">',
            "",
            *linked_image(
                f'mailto:{contact["email"]}?subject=Next%20Transmission',
                "finale.svg",
                "Grind. Build. Repeat. Open a collaboration channel with Ayush Roy",
                handle,
            ),
            "",
            "</div>",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if README.md is out of date")
    args = parser.parse_args()
    rendered = render_readme()

    if args.check:
        current = README_PATH.read_text(encoding="utf-8") if README_PATH.is_file() else ""
        if current != rendered:
            print("README.md is out of date; run scripts/generate_readme.py", file=sys.stderr)
            return 1
        print("README.md matches canonical profile data")
        return 0

    README_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {README_PATH} ({len(rendered):,} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

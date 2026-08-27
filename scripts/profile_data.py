#!/usr/bin/env python3
"""Load and validate the public profile's canonical factual data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = ROOT / "data" / "profile.json"
PHONE_PATTERN = re.compile(r"(?:\+?91[\s.-]?)?[6-9]\d{4}[\s.-]?\d{5}")
REQUIRED_PROJECT_IDS = {"portfolio", "helios", "zenith", "vision", "talks", "feelings"}
STALE_PUBLIC_CLAIMS = {
    "yorayriniwnl@gmail.com",
    "deep learning",
    "convolutional neural network",
}


class ProfileDataError(ValueError):
    """Raised when canonical profile data violates a publishing contract."""


def load_profile(path: Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        profile = json.load(stream)
    validate_profile(profile)
    return profile


def _require(mapping: dict[str, Any], keys: set[str], context: str) -> None:
    missing = sorted(keys - mapping.keys())
    if missing:
        raise ProfileDataError(f"{context} is missing: {', '.join(missing)}")


def _validate_public_content(profile: dict[str, Any]) -> None:
    serialized = json.dumps(profile, ensure_ascii=False).lower()
    if PHONE_PATTERN.search(serialized):
        raise ProfileDataError("public profile data must not contain a phone number")
    for stale_claim in STALE_PUBLIC_CLAIMS:
        if stale_claim in serialized:
            raise ProfileDataError(f"stale public claim found: {stale_claim}")


def _validate_projects(projects: list[dict[str, Any]]) -> None:
    ids = [project.get("id") for project in projects]
    if set(ids) != REQUIRED_PROJECT_IDS or len(ids) != len(set(ids)):
        raise ProfileDataError("project ids must be unique and match the canonical project set")

    repos: set[str] = set()
    orders: set[int] = set()
    required = {"id", "order", "name", "codename", "status", "repo", "summary", "proof", "stack"}
    for project in projects:
        _require(project, required, f"project {project.get('id', '<unknown>')}")
        repo = project["repo"]
        if not repo.startswith("https://github.com/yorayriniwnl/"):
            raise ProfileDataError(f"project repo must use the canonical GitHub account: {repo}")
        if repo.lower() in repos:
            raise ProfileDataError(f"duplicate project repo: {repo}")
        if project["order"] in orders:
            raise ProfileDataError(f"duplicate project order: {project['order']}")
        if not project["proof"] or not project["stack"]:
            raise ProfileDataError(f"project {project['id']} needs proof and stack entries")
        repos.add(repo.lower())
        orders.add(project["order"])


def _validate_hero(profile: dict[str, Any]) -> None:
    contract = profile["visual_contract"]
    hero_path = ROOT / contract["approved_hero"]
    if not hero_path.is_file():
        raise ProfileDataError(f"approved hero is missing: {hero_path}")
    actual = hashlib.sha256(hero_path.read_bytes()).hexdigest()
    if actual != contract["approved_hero_sha256"]:
        raise ProfileDataError("approved hero changed; restore the previous profile portrait")


def validate_profile(profile: dict[str, Any]) -> None:
    _require(
        profile,
        {
            "schema_version",
            "identity",
            "contact",
            "availability",
            "proof",
            "experience",
            "education",
            "skills",
            "projects",
            "visual_contract",
        },
        "profile",
    )
    if profile["schema_version"] != 1:
        raise ProfileDataError("unsupported profile schema version")

    _require(profile["identity"], {"name", "handle", "role", "specialty", "positioning", "location"}, "identity")
    _require(profile["contact"], {"email", "portfolio", "github", "linkedin", "devpost", "steam"}, "contact")
    if profile["identity"]["name"] != "Ayush Roy":
        raise ProfileDataError("canonical public name must remain Ayush Roy")
    if profile["contact"]["email"] != "ayushroy.dev@gmail.com":
        raise ProfileDataError("canonical public email must be ayushroy.dev@gmail.com")

    proof_ids = {item.get("id") for item in profile["proof"]}
    if proof_ids != {"apps", "tests", "accuracy", "prototypes"}:
        raise ProfileDataError("proof metrics must include apps, tests, accuracy, and prototypes")

    _validate_projects(profile["projects"])
    _validate_public_content(profile)
    _validate_hero(profile)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    args = parser.parse_args()
    profile = load_profile(args.data)
    print(
        f"profile data valid: {profile['identity']['name']} | "
        f"{len(profile['projects'])} projects | {len(profile['proof'])} proof metrics"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# scripts/generate_sample_data.py
"""Generate data/raw/profiles.json: exactly 10 SYNTHETIC LinkedIn-style profiles
belonging to ONE fictional organization. Fake profile_urls act only as IDs.
No scraping, no real people, no network access.

Run: python scripts/generate_sample_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

from src.config import RAW_DATA_PATH

ORG_NAME: str = "Nimbus Analytics"
PROFILE_COUNT: int = 10


def build_profile(person: tuple) -> dict:
    """Map one person tuple to a raw profile dict with all required sections."""
    raise NotImplementedError


def write_profiles(profiles: list[dict], path: Path = RAW_DATA_PATH) -> None:
    """Write the profiles list as indented UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(profiles, file, indent=2, ensure_ascii=False)


def main() -> None:
    """Build PROFILE_COUNT synthetic profiles and write them to disk."""
    raise NotImplementedError


if __name__ == "__main__":
    main()

# src/loader.py
"""Load and validate the fixed synthetic input file (data/raw/profiles.json).

No HTTP, no crawling: the input is exactly one local JSON file with 10
synthetic profiles of ONE fictional organization.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.config import RAW_DATA_PATH, REQUIRED_PROFILE_KEYS
from src.exceptions import ProfileLoadError, ProfileValidationError

logger = logging.getLogger(__name__)

RawProfile = dict[str, Any]

_LIST_SECTIONS: tuple[str, ...] = (
    "experience",
    "education",
    "skills",
    "interests",
    "activity",
    "connections",
)


def validate_profile(profile: RawProfile, index: int) -> None:
    """Raise ProfileValidationError if profile #index misses a required section."""
    if not isinstance(profile, dict):
        raise ProfileValidationError(f"Profile #{index} must be a JSON object.")
    missing = [key for key in REQUIRED_PROFILE_KEYS if key not in profile]
    if missing:
        raise ProfileValidationError(f"Profile #{index} is missing keys: {missing}")
    info = profile["basic_info"]
    if not isinstance(info, dict) or not info.get("full_name"):
        raise ProfileValidationError(f"Profile #{index} has no basic_info.full_name.")
    for section in _LIST_SECTIONS:
        if not isinstance(profile[section], list):
            raise ProfileValidationError(f"Profile #{index}: '{section}' must be a list.")


def validate_profiles(profiles: list[RawProfile]) -> None:
    """Validate every profile and make sure ids are unique."""
    for index, profile in enumerate(profiles):
        validate_profile(profile, index)
    ids = [profile["id"] for profile in profiles]
    duplicates = sorted({pid for pid in ids if ids.count(pid) > 1})
    if duplicates:
        raise ProfileValidationError(f"Duplicate profile ids: {duplicates}")


def load_raw_profiles(path: Path = RAW_DATA_PATH) -> list[RawProfile]:
    """Read, decode and validate the raw profiles file."""
    if not path.exists():
        raise ProfileLoadError(f"Raw profiles file not found: {path}")
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ProfileLoadError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ProfileLoadError("Raw profiles file must contain a non-empty JSON list.")
    validate_profiles(data)
    logger.info("Loaded %d profiles from %s", len(data), path.name)
    return data
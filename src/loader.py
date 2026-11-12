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


def validate_profile(profile: RawProfile, index: int) -> None:
    """Raise ProfileValidationError if profile #index misses a required section."""
    raise NotImplementedError


def validate_profiles(profiles: list[RawProfile]) -> None:
    """Validate every profile and make sure ids are unique."""
    raise NotImplementedError


def load_raw_profiles(path: Path = RAW_DATA_PATH) -> list[RawProfile]:
    """Read, decode and validate the raw profiles file."""
    raise NotImplementedError

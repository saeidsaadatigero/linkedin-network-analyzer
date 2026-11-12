# src/normalizer.py
"""Turn nested raw profiles into clean, flat pandas DataFrames.

The 10 profiles belong to ONE synthetic org; profile_urls are fake IDs only.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import REFERENCE_DATE, SKILL_ALIASES
from src.exceptions import ProfileValidationError
from src.loader import RawProfile

logger = logging.getLogger(__name__)

_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class ProfileTables:
    """All normalized tables built from the raw profiles."""

    profiles: pd.DataFrame
    experience: pd.DataFrame
    education: pd.DataFrame
    skills: pd.DataFrame
    activity: pd.DataFrame
    connections: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        """Return all tables as a name -> DataFrame mapping (used for export)."""
        return {
            "profiles": self.profiles,
            "experience": self.experience,
            "education": self.education,
            "skills": self.skills,
            "activity": self.activity,
            "connections": self.connections,
        }


def clean_text(value: str | None) -> str:
    """Strip and collapse whitespace; None becomes an empty string."""
    raise NotImplementedError


def normalize_skill(raw_skill: str) -> str:
    """Lower-case a skill and map known aliases (e.g. 'ML' -> 'machine learning')."""
    raise NotImplementedError


def parse_year_month(value: str) -> date:
    """Parse 'YYYY-MM' into the first day of that month."""
    raise NotImplementedError


def months_between(start: str, end: str | None) -> int:
    """Months between two 'YYYY-MM' values; open end means REFERENCE_DATE."""
    raise NotImplementedError


def _experience_rows(profile: RawProfile) -> list[dict]:
    """One row per job, with computed duration_months and is_current flag."""
    raise NotImplementedError


def _education_rows(profile: RawProfile) -> list[dict]:
    """One row per education entry."""
    raise NotImplementedError


def _skill_rows(profile: RawProfile) -> list[dict]:
    """One row per unique normalized skill."""
    raise NotImplementedError


def _activity_rows(profile: RawProfile) -> list[dict]:
    """One row per post/comment/reaction/repost."""
    raise NotImplementedError


def _connection_rows(profile: RawProfile) -> list[dict]:
    """One row per declared connection between two of the 10 people."""
    raise NotImplementedError


def _profile_row(profile: RawProfile, experience: list[dict], skills: list[dict]) -> dict:
    """One summary row per person (current role, totals)."""
    raise NotImplementedError


def build_tables(raw_profiles: list[RawProfile]) -> ProfileTables:
    """Build all normalized DataFrames from validated raw profiles."""
    raise NotImplementedError

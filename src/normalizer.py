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
    if value is None:
        return ""
    return _WHITESPACE.sub(" ", str(value)).strip()


def normalize_skill(raw_skill: str) -> str:
    """Lower-case a skill and map known aliases (e.g. 'ML' -> 'machine learning')."""
    skill = clean_text(raw_skill).lower()
    return SKILL_ALIASES.get(skill, skill)


def parse_year_month(value: str) -> date:
    """Parse 'YYYY-MM' into the first day of that month."""
    year, month = value.split("-")
    return date(int(year), int(month), 1)


def months_between(start: str, end: str | None) -> int:
    """Months between two 'YYYY-MM' values; open end means REFERENCE_DATE."""
    start_date = parse_year_month(start)
    end_date = parse_year_month(end) if end else REFERENCE_DATE
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if months < 0:
        raise ValueError(f"End date {end} is before start date {start}")
    return months


def _experience_rows(profile: RawProfile) -> list[dict]:
    """One row per job, with computed duration_months and is_current flag."""
    rows: list[dict] = []
    for job in profile["experience"]:
        try:
            duration = months_between(job["start"], job.get("end"))
        except (ValueError, KeyError) as exc:
            raise ProfileValidationError(
                f"Profile {profile['id']}: invalid experience dates ({exc})"
            ) from exc
        rows.append(
            {
                "profile_id": profile["id"],
                "title": clean_text(job.get("title")),
                "company": clean_text(job.get("company")),
                "start": job["start"],
                "end": job.get("end") or "",
                "duration_months": duration,
                "is_current": not job.get("end"),
                "description": clean_text(job.get("description")),
            }
        )
    return rows


def _education_rows(profile: RawProfile) -> list[dict]:
    """One row per education entry."""
    return [
        {
            "profile_id": profile["id"],
            "school": clean_text(item.get("school")),
            "degree": clean_text(item.get("degree")),
            "field": clean_text(item.get("field")),
            "start_year": item.get("start_year"),
            "end_year": item.get("end_year"),
        }
        for item in profile["education"]
    ]


def _skill_rows(profile: RawProfile) -> list[dict]:
    """One row per unique normalized skill."""
    skills = {normalize_skill(skill) for skill in profile["skills"]}
    return [{"profile_id": profile["id"], "skill": skill} for skill in sorted(skills) if skill]


def _activity_rows(profile: RawProfile) -> list[dict]:
    """One row per post/comment/reaction/repost."""
    return [
        {
            "profile_id": profile["id"],
            "type": clean_text(item.get("type")).lower(),
            "date": item.get("date", ""),
            "text": clean_text(item.get("text")),
            "target_profile_id": item.get("target_profile_id"),
        }
        for item in profile["activity"]
    ]


def _connection_rows(profile: RawProfile) -> list[dict]:
    """One row per declared connection between two of the 10 people."""
    return [
        {
            "profile_id": profile["id"],
            "target_profile_id": item["profile_id"],
            "relation": clean_text(item.get("relation")).lower(),
        }
        for item in profile["connections"]
    ]


def _profile_row(profile: RawProfile, experience: list[dict], skills: list[dict]) -> dict:
    """One summary row per person (current role, totals)."""
    info = profile["basic_info"]
    current = next((job for job in experience if job["is_current"]), None)
    return {
        "profile_id": profile["id"],
        "profile_url": profile["profile_url"],
        "full_name": clean_text(info.get("full_name")),
        "headline": clean_text(info.get("headline")),
        "location": clean_text(info.get("location")),
        "summary": clean_text(info.get("summary")),
        "current_title": current["title"] if current else "",
        "current_company": current["company"] if current else "",
        "total_experience_months": sum(job["duration_months"] for job in experience),
        "num_skills": len(skills),
        "interests": "; ".join(clean_text(i) for i in profile["interests"]),
        "num_activities": len(profile["activity"]),
    }


def build_tables(raw_profiles: list[RawProfile]) -> ProfileTables:
    """Build all normalized DataFrames from validated raw profiles."""
    profile_rows: list[dict] = []
    experience_rows: list[dict] = []
    education_rows: list[dict] = []
    skill_rows: list[dict] = []
    activity_rows: list[dict] = []
    connection_rows: list[dict] = []

    for profile in raw_profiles:
        experience = _experience_rows(profile)
        skills = _skill_rows(profile)
        profile_rows.append(_profile_row(profile, experience, skills))
        experience_rows.extend(experience)
        education_rows.extend(_education_rows(profile))
        skill_rows.extend(skills)
        activity_rows.extend(_activity_rows(profile))
        connection_rows.extend(_connection_rows(profile))

    tables = ProfileTables(
        profiles=pd.DataFrame(profile_rows),
        experience=pd.DataFrame(experience_rows),
        education=pd.DataFrame(education_rows),
        skills=pd.DataFrame(skill_rows),
        activity=pd.DataFrame(activity_rows),
        connections=pd.DataFrame(connection_rows),
    )
    logger.info(
        "Built tables: %s",
        ", ".join(f"{name}={len(df)}" for name, df in tables.as_dict().items()),
    )
    return tables
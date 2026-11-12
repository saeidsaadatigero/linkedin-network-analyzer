# src/config.py
"""Central configuration. Input is ONE fixed synthetic file; no discovery, no scraping."""
from __future__ import annotations

from datetime import date
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
RAW_DATA_PATH: Path = PROJECT_ROOT / "data" / "raw" / "profiles.json"
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR: Path = PROJECT_ROOT / "output"

# Every artifact of this project is built from synthetic data only.
DATA_IS_SYNTHETIC: bool = True

# Fixed "today" so durations and outputs are reproducible.
REFERENCE_DATE: date = date(2026, 11, 1)
RANDOM_SEED: int = 42

REQUIRED_PROFILE_KEYS: tuple[str, ...] = (
    "id",
    "profile_url",
    "basic_info",
    "experience",
    "education",
    "skills",
    "interests",
    "activity",
    "connections",
)

# Messy skill spellings -> canonical form (applied after lower-casing).
SKILL_ALIASES: dict[str, str] = {
    "ml": "machine learning",
    "py": "python",
    "nlp": "natural language processing",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "ux": "ux design",
}

# Edge weights: how strong a declared relation or a single interaction is.
RELATION_WEIGHTS: dict[str, float] = {"reports_to": 2.0, "mentor": 2.0, "colleague": 1.0}
INTERACTION_WEIGHTS: dict[str, float] = {"reaction": 1.0, "comment": 2.0, "repost": 3.0}
DEFAULT_EDGE_WEIGHT: float = 1.0

# Skill clustering: try k in [K_MIN, K_MAX], keep best silhouette score.
CLUSTER_K_MIN: int = 2
CLUSTER_K_MAX: int = 5

# People listed in the "key people" section of the report.
TOP_N_KEY_PEOPLE: int = 5

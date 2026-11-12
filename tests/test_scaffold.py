# tests/test_scaffold.py
"""Smoke tests for the scaffold: modules import and config encodes the data design."""
from __future__ import annotations

import src.analysis as analysis
import src.config as config
import src.exceptions as exceptions
import src.exporter as exporter
import src.graph_builder as graph_builder
import src.loader as loader
import src.normalizer as normalizer
import src.pipeline as pipeline


def test_data_is_synthetic_and_single_file() -> None:
    assert config.DATA_IS_SYNTHETIC is True
    assert config.RAW_DATA_PATH == config.PROJECT_ROOT / "data" / "raw" / "profiles.json"


def test_required_sections_cover_the_full_profile_shape() -> None:
    for key in ("id", "profile_url", "basic_info", "experience", "education",
                "skills", "interests", "activity", "connections"):
        assert key in config.REQUIRED_PROFILE_KEYS


def test_pipeline_wiring_exists() -> None:
    assert hasattr(pipeline, "run_pipeline")
    assert hasattr(graph_builder, "build_graph")
    assert hasattr(analysis, "compute_centrality")
    assert hasattr(analysis, "cluster_skills")
    assert hasattr(exporter, "build_report")


def test_exception_hierarchy() -> None:
    assert issubclass(exceptions.ProfileLoadError, exceptions.ProjectError)
    assert issubclass(exceptions.AnalysisError, exceptions.ProjectError)

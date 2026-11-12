# src/exporter.py
"""Write tables (CSV/JSON), graph files (graph.json, graph.png) and report.md."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import networkx as nx
import pandas as pd

from src.analysis import CommunityResult, SkillClusterResult
from src.config import RANDOM_SEED, TOP_N_KEY_PEOPLE
from src.normalizer import ProfileTables

logger = logging.getLogger(__name__)


def save_tables(tables: ProfileTables, directory: Path) -> None:
    """Save every table as CSV, plus one combined tables.json."""
    raise NotImplementedError


def save_graph_json(graph: nx.Graph, path: Path) -> None:
    """Serialize the graph as a simple {nodes, edges} JSON document."""
    raise NotImplementedError


def save_graph_png(graph: nx.Graph, path: Path) -> None:
    """Render the graph: node size = influence, color = community, edge width = weight."""
    raise NotImplementedError


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Build a GitHub-flavored markdown table from headers and row strings."""
    raise NotImplementedError


def build_report(
    graph: nx.Graph,
    centrality: pd.DataFrame,
    communities: CommunityResult,
    skill_clusters: SkillClusterResult,
) -> str:
    """Compose report.md: overview, key people, communities, skill clusters, reading guide."""
    raise NotImplementedError


def save_report(report: str, path: Path) -> None:
    """Write the markdown report to disk."""
    raise NotImplementedError

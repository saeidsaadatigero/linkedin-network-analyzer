# src/pipeline.py
"""End-to-end pipeline: load -> normalize -> graph -> analyze -> export."""
from __future__ import annotations

import logging
from pathlib import Path

from src.analysis import annotate_graph, cluster_skills, compute_centrality, detect_communities
from src.exporter import build_report, save_graph_json, save_graph_png, save_report, save_tables
from src.graph_builder import build_graph
from src.loader import load_raw_profiles
from src.normalizer import build_tables

logger = logging.getLogger(__name__)


def run_pipeline(input_path: Path, processed_dir: Path, output_dir: Path) -> None:
    """Run every stage and write all artifacts (CSV/JSON/graph.png/report.md)."""
    raw_profiles = load_raw_profiles(input_path)
    tables = build_tables(raw_profiles)
    save_tables(tables, processed_dir)

    graph = build_graph(tables)
    centrality = compute_centrality(graph)
    communities = detect_communities(graph)
    skill_clusters = cluster_skills(tables)
    annotate_graph(graph, centrality, communities, skill_clusters)

    output_dir.mkdir(parents=True, exist_ok=True)
    centrality.to_csv(output_dir / "centrality.csv", index=False, encoding="utf-8")
    save_graph_json(graph, output_dir / "graph.json")
    save_graph_png(graph, output_dir / "graph.png")
    save_report(build_report(graph, centrality, communities, skill_clusters), output_dir / "report.md")
    logger.info("Pipeline finished. Outputs are in %s", output_dir)

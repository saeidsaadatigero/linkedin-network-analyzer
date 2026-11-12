# src/exporter.py
"""Write tables (CSV/JSON), graph files (graph.json, graph.png) and report.md."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend: no window needed
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from src.analysis import CommunityResult, SkillClusterResult  # noqa: E402
from src.config import RANDOM_SEED, TOP_N_KEY_PEOPLE  # noqa: E402
from src.normalizer import ProfileTables  # noqa: E402

logger = logging.getLogger(__name__)


def save_tables(tables: ProfileTables, directory: Path) -> None:
    """Save every table as CSV, plus one combined tables.json."""
    directory.mkdir(parents=True, exist_ok=True)
    combined: dict[str, list[dict]] = {}
    for name, frame in tables.as_dict().items():
        frame.to_csv(directory / f"{name}.csv", index=False, encoding="utf-8")
        combined[name] = json.loads(frame.to_json(orient="records", force_ascii=False))
    with (directory / "tables.json").open("w", encoding="utf-8") as file:
        json.dump(combined, file, indent=2, ensure_ascii=False)
    logger.info("Saved %d tables to %s", len(combined), directory)


def save_graph_json(graph: nx.Graph, path: Path) -> None:
    """Serialize the graph as a simple {nodes, edges} JSON document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "nodes": [{"id": node, **attrs} for node, attrs in graph.nodes(data=True)],
        "edges": [
            {"source": u, "target": v, **attrs} for u, v, attrs in graph.edges(data=True)
        ],
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
    logger.info("Saved graph JSON to %s", path)


def save_graph_png(graph: nx.Graph, path: Path) -> None:
    """Draw the graph: node size = influence, color = community, edge width = tie strength."""
    path.parent.mkdir(parents=True, exist_ok=True)
    position = nx.spring_layout(graph, weight="weight", seed=RANDOM_SEED)
    colormap = plt.get_cmap("tab10")
    communities = sorted({graph.nodes[n]["community"] for n in graph.nodes})

    node_colors = [colormap(graph.nodes[n]["community"] % 10) for n in graph.nodes]
    node_sizes = [400 + 2800 * graph.nodes[n]["influence_score"] for n in graph.nodes]
    edge_widths = [0.5 + 0.5 * min(data["weight"], 8) for _, _, data in graph.edges(data=True)]
    labels = {n: graph.nodes[n]["name"].replace(" ", "\n") for n in graph.nodes}

    fig, ax = plt.subplots(figsize=(11, 8))
    nx.draw_networkx_edges(graph, position, width=edge_widths, alpha=0.35, ax=ax)
    nx.draw_networkx_nodes(graph, position, node_size=node_sizes, node_color=node_colors, ax=ax)
    nx.draw_networkx_labels(graph, position, labels=labels, font_size=8, ax=ax)
    ax.legend(
        handles=[Patch(color=colormap(c % 10), label=f"Community {c}") for c in communities],
        loc="lower left",
    )
    ax.set_title("Organization graph (size = influence, color = community)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Saved graph image to %s", path)


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Build a GitHub-flavored markdown table from headers and row strings."""
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def _members(graph: nx.Graph, node_ids: list[str]) -> str:
    """Comma-separated display names of a group of nodes."""
    return ", ".join(graph.nodes[node]["name"] for node in node_ids)


def build_report(
    graph: nx.Graph,
    centrality: pd.DataFrame,
    communities: CommunityResult,
    skill_clusters: SkillClusterResult,
) -> str:
    """Compose report.md: overview, key people, communities, skill clusters, reading guide."""
    top = centrality.head(TOP_N_KEY_PEOPLE)
    bridge = centrality.sort_values("betweenness", ascending=False).iloc[0]
    strongest = top.iloc[0]

    key_rows = [
        [
            str(int(row["rank"])),
            row["name"],
            row["title"],
            f"{row['degree_centrality']:.2f}",
            f"{row['betweenness']:.2f}",
            f"{row['influence_score']:.2f}",
        ]
        for row in top.to_dict("records")
    ]

    community_rows = []
    for community_id in sorted(set(communities.labels.values())):
        members = [n for n, c in communities.labels.items() if c == community_id]
        community_rows.append([str(community_id), str(len(members)), _members(graph, members)])

    cluster_rows = []
    for cluster_id in sorted(set(skill_clusters.labels.values())):
        members = [n for n, c in skill_clusters.labels.items() if c == cluster_id]
        cluster_rows.append(
            [str(cluster_id), ", ".join(skill_clusters.top_terms.get(cluster_id, [])), _members(graph, members)]
        )

    return "\n".join(
        [
            "# Analysis Report",
            "",
            "> Data is synthetic (see README). Findings describe the sample organization only.",
            "",
            "## 1. Graph overview",
            "",
            f"- People (nodes): **{graph.number_of_nodes()}**",
            f"- Ties (edges): **{graph.number_of_edges()}**",
            f"- Density: **{nx.density(graph):.2f}**",
            f"- Connected: **{nx.is_connected(graph)}**",
            "",
            "## 2. Key people (centrality)",
            "",
            _md_table(["Rank", "Name", "Title", "Degree", "Betweenness", "Influence"], key_rows),
            "",
            f"- **{strongest['name']}** has the highest combined influence score.",
            f"- **{bridge['name']}** has the highest betweenness ({bridge['betweenness']:.2f}): "
            "most often on the shortest path between others, i.e. the main bridge.",
            "",
            "## 3. Communities (who works closely together)",
            "",
            f"Greedy modularity found **{len(community_rows)}** communities "
            f"(modularity = {communities.modularity:.2f}).",
            "",
            _md_table(["Community", "Size", "Members"], community_rows),
            "",
            "## 4. Skill clusters (TF-IDF + KMeans)",
            "",
            f"Best k = **{skill_clusters.best_k}** (silhouette = {skill_clusters.silhouette:.2f}).",
            "",
            _md_table(["Cluster", "Top skills", "Members"], cluster_rows),
            "",
            "## 5. How to read this",
            "",
            "- High degree = many direct ties. High betweenness = connects otherwise separate groups.",
            "- A person with high betweenness but modest degree is a hidden broker: losing them "
            "would split the network more than their title suggests.",
            "- Communities come from *relationships*, skill clusters from *profile content*. "
            "When both agree, teams are well aligned; when they differ, there is "
            "cross-functional collaboration.",
            "",
        ]
    )


def save_report(report: str, path: Path) -> None:
    """Write the markdown report to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    logger.info("Saved report to %s", path)
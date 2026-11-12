# src/analysis.py
"""Graph analysis (centrality, communities) and ML analysis (TF-IDF + KMeans)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms import community as nx_community
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

from src.config import CLUSTER_K_MAX, CLUSTER_K_MIN, RANDOM_SEED
from src.exceptions import AnalysisError
from src.normalizer import ProfileTables

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommunityResult:
    """Community id per node plus the graph's modularity score."""

    labels: dict[str, int]
    modularity: float


@dataclass(frozen=True)
class SkillClusterResult:
    """KMeans result: label per profile, chosen k, silhouette, top terms per cluster."""

    labels: dict[str, int]
    best_k: int
    silhouette: float
    top_terms: dict[int, list[str]]


def _min_max(series: pd.Series) -> pd.Series:
    """Scale to [0, 1]; a constant series becomes all zeros."""
    span = series.max() - series.min()
    if span == 0:
        return series * 0.0
    return (series - series.min()) / span


def compute_centrality(graph: nx.Graph) -> pd.DataFrame:
    """Rank people by degree/weighted degree/betweenness/closeness + combined influence.

    Betweenness and closeness use edge 'distance' (1 / weight), so strong ties
    count as short paths. influence_score = mean of min-max scaled degree
    centrality, weighted degree and betweenness.
    """
    if graph.number_of_nodes() == 0:
        raise AnalysisError("Cannot compute centrality on an empty graph.")

    degree = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph, weight="distance", normalized=True)
    closeness = nx.closeness_centrality(graph, distance="distance")
    strength = dict(graph.degree(weight="weight"))

    rows = [
        {
            "profile_id": node,
            "name": graph.nodes[node]["name"],
            "title": graph.nodes[node]["title"],
            "degree_centrality": degree[node],
            "weighted_degree": strength[node],
            "betweenness": betweenness[node],
            "closeness": closeness[node],
        }
        for node in graph.nodes
    ]
    frame = pd.DataFrame(rows)
    frame["influence_score"] = (
        _min_max(frame["degree_centrality"])
        + _min_max(frame["weighted_degree"])
        + _min_max(frame["betweenness"])
    ) / 3.0
    frame = frame.sort_values("influence_score", ascending=False).reset_index(drop=True)
    frame.insert(0, "rank", frame.index + 1)
    return frame


def detect_communities(graph: nx.Graph) -> CommunityResult:
    """Find densely connected groups via greedy modularity optimization."""
    if graph.number_of_nodes() == 0:
        raise AnalysisError("Cannot detect communities on an empty graph.")
    groups = nx_community.greedy_modularity_communities(graph, weight="weight")
    ordered = sorted(groups, key=lambda group: (-len(group), sorted(group)[0]))
    labels = {node: index for index, group in enumerate(ordered) for node in group}
    modularity = nx_community.modularity(graph, ordered, weight="weight") if ordered else 0.0
    return CommunityResult(labels=labels, modularity=float(modularity))


def _identity(document: list[str]) -> list[str]:
    """Analyzer for TF-IDF: a document is already a list of skill tokens."""
    return document


def cluster_skills(tables: ProfileTables) -> SkillClusterResult:
    """Cluster people by skill sets: TF-IDF vectors + KMeans, best k by silhouette."""
    grouped = tables.skills.groupby("profile_id")["skill"].apply(list)
    profile_ids = [pid for pid in tables.profiles["profile_id"] if pid in grouped.index]
    if len(profile_ids) < 3:
        raise AnalysisError("Skill clustering needs at least 3 profiles with skills.")

    documents = [grouped[pid] for pid in profile_ids]
    vectorizer = TfidfVectorizer(analyzer=_identity)
    matrix = vectorizer.fit_transform(documents)
    terms = np.array(vectorizer.get_feature_names_out())

    best: tuple[float, int, np.ndarray, np.ndarray] | None = None
    upper = min(CLUSTER_K_MAX, len(profile_ids) - 1)
    for k in range(CLUSTER_K_MIN, upper + 1):
        model = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_SEED)
        labels = model.fit_predict(matrix)
        if len(set(labels)) < 2:
            continue
        score = float(silhouette_score(matrix, labels))
        logger.info("KMeans k=%d silhouette=%.3f", k, score)
        if best is None or score > best[0]:
            best = (score, k, labels, model.cluster_centers_)

    if best is None:
        raise AnalysisError("KMeans could not produce at least two clusters.")

    score, best_k, labels, centers = best
    top_terms = {
        cluster: [str(term) for term in terms[np.argsort(centers[cluster])[::-1][:5]]]
        for cluster in range(best_k)
    }
    return SkillClusterResult(
        labels={pid: int(label) for pid, label in zip(profile_ids, labels)},
        best_k=best_k,
        silhouette=score,
        top_terms=top_terms,
    )


def annotate_graph(
    graph: nx.Graph,
    centrality: pd.DataFrame,
    communities: CommunityResult,
    skill_clusters: SkillClusterResult,
) -> None:
    """Store analysis results on graph nodes so exports are self-contained."""
    scores = centrality.set_index("profile_id")
    for node in graph.nodes:
        graph.nodes[node]["influence_score"] = float(scores.loc[node, "influence_score"])
        graph.nodes[node]["betweenness"] = float(scores.loc[node, "betweenness"])
        graph.nodes[node]["degree_centrality"] = float(scores.loc[node, "degree_centrality"])
        graph.nodes[node]["community"] = int(communities.labels[node])
        graph.nodes[node]["skill_cluster"] = int(skill_clusters.labels.get(node, -1))
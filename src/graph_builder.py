# src/graph_builder.py
"""Build the weighted people graph of ONE synthetic organization.

Nodes = the 10 profile ids. Edges = declared relations (reports_to/mentor/
colleague) + activity interactions between these people, weighted per config.
"""
from __future__ import annotations

import logging

import networkx as nx

from src.config import DEFAULT_EDGE_WEIGHT, INTERACTION_WEIGHTS, RELATION_WEIGHTS
from src.normalizer import ProfileTables

logger = logging.getLogger(__name__)


def _add_or_update_edge(graph: nx.Graph, source: str, target: str, relation: str, weight: float) -> bool:
    """Add an edge or accumulate weight on an existing one; skip self-loops/unknown ids."""
    if source == target:
        return False
    if source not in graph or target not in graph:
        logger.warning("Skipping edge %s -> %s: person outside the profile set", source, target)
        return False
    if graph.has_edge(source, target):
        graph[source][target]["weight"] += weight
        graph[source][target]["relations"].add(relation)
    else:
        graph.add_edge(source, target, weight=weight, relations={relation})
    return True


def _add_nodes(graph: nx.Graph, tables: ProfileTables) -> None:
    """Add one node per profile with name/title/company/location attributes."""
    for row in tables.profiles.itertuples(index=False):
        graph.add_node(
            row.profile_id,
            name=row.full_name,
            title=row.current_title,
            company=row.current_company,
            location=row.location,
        )


def _add_declared_connections(graph: nx.Graph, tables: ProfileTables) -> None:
    """Organizational edges; a (pair, relation) combination counts only once."""
    seen: set[tuple[frozenset[str], str]] = set()
    for row in tables.connections.itertuples(index=False):
        key = (frozenset((row.profile_id, row.target_profile_id)), row.relation)
        if key in seen:
            continue
        seen.add(key)
        weight = RELATION_WEIGHTS.get(row.relation, DEFAULT_EDGE_WEIGHT)
        _add_or_update_edge(graph, row.profile_id, row.target_profile_id, row.relation, weight)


def _add_interactions(graph: nx.Graph, tables: ProfileTables) -> None:
    """Edges from targeted activity (comment/reaction/repost on someone's post)."""
    targeted = tables.activity.dropna(subset=["target_profile_id"])
    for row in targeted.itertuples(index=False):
        weight = INTERACTION_WEIGHTS.get(row.type, DEFAULT_EDGE_WEIGHT)
        _add_or_update_edge(graph, row.profile_id, row.target_profile_id, f"activity:{row.type}", weight)


def _finalize_edges(graph: nx.Graph) -> None:
    """Make relations JSON-friendly and add distance = 1 / weight (strong tie = short path)."""
    for _, _, data in graph.edges(data=True):
        data["relations"] = sorted(data["relations"])
        data["distance"] = 1.0 / data["weight"]


def build_graph(tables: ProfileTables) -> nx.Graph:
    """Create the undirected weighted graph of people."""
    graph = nx.Graph()
    _add_nodes(graph, tables)
    _add_declared_connections(graph, tables)
    _add_interactions(graph, tables)
    _finalize_edges(graph)
    logger.info(
        "Graph built: %d nodes, %d edges, density=%.2f, connected=%s",
        graph.number_of_nodes(),
        graph.number_of_edges(),
        nx.density(graph),
        nx.is_connected(graph),
    )
    return graph
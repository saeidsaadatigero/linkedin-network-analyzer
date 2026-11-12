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
    raise NotImplementedError


def _add_nodes(graph: nx.Graph, tables: ProfileTables) -> None:
    """Add one node per profile with name/title/company/location attributes."""
    raise NotImplementedError


def _add_declared_connections(graph: nx.Graph, tables: ProfileTables) -> None:
    """Organizational edges; a (pair, relation) combination counts only once."""
    raise NotImplementedError


def _add_interactions(graph: nx.Graph, tables: ProfileTables) -> None:
    """Edges from targeted activity (comment/reaction/repost on someone's post)."""
    raise NotImplementedError


def _finalize_edges(graph: nx.Graph) -> None:
    """Make relations JSON-friendly and add distance = 1 / weight."""
    raise NotImplementedError


def build_graph(tables: ProfileTables) -> nx.Graph:
    """Create the undirected weighted graph of people."""
    raise NotImplementedError

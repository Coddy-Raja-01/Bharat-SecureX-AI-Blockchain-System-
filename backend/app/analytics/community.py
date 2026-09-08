import networkx as nx
from typing import Dict, List, Set

def detect_communities(G: nx.Graph) -> Dict[str, int]:
    """
    Computes Louvain communities for clustering nodes into distinct criminal/syndicate cells.
    Returns a mapping of node_id -> community_id (0-indexed integer).
    """
    if G.number_of_nodes() == 0:
        return {}

    try:
        # Undirected view for community detection
        G_undirected = G.to_undirected() if G.is_directed() else G
        communities = list(nx.community.louvain_communities(G_undirected, weight='weight', seed=42))
        
        community_map: Dict[str, int] = {}
        for comm_id, node_set in enumerate(communities):
            for node in node_set:
                community_map[node] = comm_id
        return community_map
    except Exception as e:
        print(f"Louvain community detection fallback: {e}")
        return {node: 0 for node in G.nodes()}

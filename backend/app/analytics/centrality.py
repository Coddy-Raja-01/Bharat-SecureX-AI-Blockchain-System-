import networkx as nx
from typing import List, Dict, Tuple, Any
from ..models.schemas import NodeSchema, EdgeSchema, KeyIndividualSchema

def compute_centrality_and_rank(
    G: nx.Graph,
    nodes_dict: Dict[str, NodeSchema],
    edges: List[EdgeSchema]
) -> Tuple[Dict[str, float], List[KeyIndividualSchema]]:
    """
    Computes PageRank and Betweenness Centrality on the graph.
    Combines them into a normalized centrality score [0.0, 1.0].
    Generates a ranked list of Key Individuals with explainable 1-line rationales.
    """
    if G.number_of_nodes() == 0:
        return {}, []

    # 1. PageRank
    try:
        pr = nx.pagerank(G, weight='weight', alpha=0.85, max_iter=200)
    except Exception:
        pr = {n: 1.0 / len(G) for n in G.nodes()}

    # 2. Betweenness Centrality
    try:
        bc = nx.betweenness_centrality(G, weight='weight', normalized=True)
    except Exception:
        bc = {n: 0.0 for n in G.nodes()}

    # 3. Degree Centrality
    degree_dict = dict(G.degree(weight='weight'))

    # Normalize metrics to 0.0 - 1.0 scale
    max_pr = max(pr.values()) if pr and max(pr.values()) > 0 else 1.0
    max_bc = max(bc.values()) if bc and max(bc.values()) > 0 else 1.0

    centrality_scores: Dict[str, float] = {}
    for node_id in G.nodes():
        norm_pr = pr.get(node_id, 0.0) / max_pr
        norm_bc = bc.get(node_id, 0.0) / max_bc
        # Blend: 60% PageRank (network influence), 40% Betweenness (bridge/broker role)
        composite = 0.60 * norm_pr + 0.40 * norm_bc
        centrality_scores[node_id] = round(composite, 4)

    # 4. Generate Key Individuals (filtered to Person & Organization types, ranked highest to lowest)
    key_individuals: List[KeyIndividualSchema] = []
    
    # Sort nodes by centrality score
    ranked_nodes = sorted(centrality_scores.keys(), key=lambda n: centrality_scores[n], reverse=True)

    for node_id in ranked_nodes:
        node_obj = nodes_dict.get(node_id)
        if not node_obj or node_obj.type not in ("Person", "Organization"):
            continue

        c_score = centrality_scores[node_id]
        p_val = round(pr.get(node_id, 0.0), 4)
        b_val = round(bc.get(node_id, 0.0), 4)
        deg = degree_dict.get(node_id, 0)
        neighbors = list(G.neighbors(node_id))

        # Check call, transaction, or mention counts for this entity
        calls_count = 0
        txns_count = 0
        mention_count = 0
        total_txn_val = 0.0

        for e in edges:
            if e.source == node_id or e.target == node_id:
                if e.type == "Call":
                    calls_count += 1
                elif e.type == "Transaction":
                    txns_count += 1
                    total_txn_val += float(e.attributes.get('amount', 0.0))
                elif e.type in ("Mentioned_In", "Co_Mentioned"):
                    mention_count += 1

        # Synthesize explainable one-line rationale
        rationale_parts = []
        if b_val > 0.15:
            rationale_parts.append(f"Critical bridge node (betweenness {b_val}) connecting multiple cells")
        elif p_val > 0.08:
            rationale_parts.append(f"High network authority hub with {len(neighbors)} direct associates")

        if txns_count > 0:
            rationale_parts.append(f"routed ₹{int(total_txn_val):,} across {txns_count} financial transfers")
        if calls_count > 0:
            rationale_parts.append(f"placed/received {calls_count} monitored telecom interactions")
        if mention_count > 0 and len(rationale_parts) < 2:
            rationale_parts.append(f"referenced in {mention_count} formal law enforcement documents")

        if not rationale_parts:
            rationale = f"Connected to {len(neighbors)} peripheral entities across the network graph."
        else:
            rationale = "; ".join(rationale_parts).capitalize() + "."

        key_individuals.append(KeyIndividualSchema(
            id=node_id,
            label=node_obj.label,
            type=node_obj.type,
            centrality_score=c_score,
            pagerank=p_val,
            betweenness=b_val,
            community_id=node_obj.community_id,
            rationale=rationale,
            risk_flag=(c_score >= 0.35 or txns_count >= 3)
        ))

    return centrality_scores, key_individuals

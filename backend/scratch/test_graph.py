import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.graph import graph_manager

db = SessionLocal()
try:
    graph_manager.load_models()
    graph_manager.load_graph_from_db(db)
    
    nodes = list(graph_manager.G.nodes())
    if nodes:
        node = nodes[0]
        print(f"Testing node: {node}")
        score = graph_manager.get_risk_score(node)
        print(f"Risk score: {score}")
        
        explanation = graph_manager.get_risk_explanation(node)
        print(f"Explanation: {explanation}")
        
        if len(nodes) > 1:
            link_prob = graph_manager.get_link_probability(nodes[0], nodes[1])
            print(f"Link probability: {link_prob}")
    else:
        print("No nodes in graph!")
finally:
    db.close()

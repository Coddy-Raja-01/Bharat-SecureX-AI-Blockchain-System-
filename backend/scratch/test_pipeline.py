import sys
import os

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.case_store import case_store

try:
    print("Loading sample dataset...")
    d = case_store.load_sample_dataset()
    print("SUCCESSFULLY LOADED SAMPLE CASE!")
    print(f"Total Nodes: {len(d.nodes)}")
    print(f"Total Edges: {len(d.edges)}")
    print(f"Total Key Individuals: {len(d.key_individuals)}")
    print(f"Total Flagged Anomalies: {len(d.anomalies)}")
    print(f"Temporal Heatmap Slots: {len(d.temporal_heatmap)}")
    print(f"Geo Hotspots: {len(d.geo_heatmap)}")
    
    print("\n--- TOP 5 KEY INDIVIDUALS ---")
    for ki in d.key_individuals[:5]:
        print(f"[{ki.type}] {ki.label} (Centrality: {ki.centrality_score:.3f}, PR: {ki.pagerank:.3f}, BC: {ki.betweenness:.3f})")
        print(f"   Rationale: {ki.rationale}")

    print("\n--- FLAGGED ANOMALIES ---")
    for a in d.anomalies:
        print(f"[{a.severity.upper()}] {a.id}: {a.description}")
        print(f"   Evidence refs: {a.evidence_refs}")

    print("\n--- GEO HOTSPOTS ---")
    for g in d.geo_heatmap[:5]:
        print(f"   {g.location} ({g.lat}, {g.lng}) -> Weight: {g.weight}")

except Exception as e:
    import traceback
    traceback.print_exc()

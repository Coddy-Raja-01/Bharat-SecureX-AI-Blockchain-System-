import sys, os, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

t0 = time.time()
print("1. Importing ner...", flush=True)
from app.pipeline.ner import extract_entities_from_text
print(f"   Done ner in {time.time() - t0:.2f}s", flush=True)

t1 = time.time()
print("2. Importing resolve_entities...", flush=True)
from app.pipeline.resolve_entities import EntityResolver
print(f"   Done resolve in {time.time() - t1:.2f}s", flush=True)

t2 = time.time()
print("3. Testing PDF parse...", flush=True)
from app.pipeline.parse_pdf import parse_pdf_document
pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_unstructured_reports.pdf"))
res = EntityResolver()
nodes, edges, warns = parse_pdf_document(pdf_path, "sample.pdf", res)
print(f"   Done PDF in {time.time() - t2:.2f}s: {len(nodes)} nodes, {len(edges)} edges", flush=True)

t3 = time.time()
print("4. Testing CDR parse...", flush=True)
from app.pipeline.parse_cdr import parse_cdr_file
csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_cdr_data.csv"))
c_nodes, c_edges, c_warns = parse_cdr_file(csv_path, "sample.csv", res)
print(f"   Done CDR in {time.time() - t3:.2f}s: {len(c_nodes)} nodes, {len(c_edges)} edges", flush=True)

t4 = time.time()
print("5. Testing XLSX parse...", flush=True)
from app.pipeline.parse_txn import parse_financial_transactions
xlsx_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_financial_transactions.xlsx"))
x_nodes, x_edges, x_warns = parse_financial_transactions(xlsx_path, "sample.xlsx", res)
print(f"   Done XLSX in {time.time() - t4:.2f}s: {len(x_nodes)} nodes, {len(x_edges)} edges", flush=True)

t5 = time.time()
print("6. Testing Analytics...", flush=True)
from app.analytics.centrality import compute_centrality_and_rank
from app.analytics.community import detect_communities
from app.analytics.anomaly import detect_anomalies
import networkx as nx
G = nx.Graph()
all_nodes = {n.id: n for n in nodes + c_nodes + x_nodes}
all_edges = edges + c_edges + x_edges
for e in all_edges:
    G.add_edge(e.source, e.target, weight=e.weight)

comm = detect_communities(G)
print(f"   Communities detected: {len(set(comm.values()))}", flush=True)
cent, ki = compute_centrality_and_rank(G, all_nodes, all_edges)
print(f"   Key individuals: {len(ki)}", flush=True)
anom = detect_anomalies(all_edges)
print(f"   Anomalies: {len(anom)}", flush=True)
print(f"TOTAL PIPELINE EXECUTION TIME: {time.time() - t0:.2f}s", flush=True)

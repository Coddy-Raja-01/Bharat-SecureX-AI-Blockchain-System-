import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

AUTH_HEADERS = {"X-API-Key": os.environ["API_KEY"]}
client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_load_sample_case():
    response = client.post("/api/demo/load-sample", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "nodes" in data
    assert "edges" in data
    assert "key_individuals" in data
    assert "anomalies" in data
    assert "temporal_heatmap" in data
    assert "geo_heatmap" in data
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0
    assert len(data["key_individuals"]) > 0
    assert len(data["anomalies"]) >= 2

def test_case_graph():
    response = client.get("/api/cases/demo_case_001/graph", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data

def test_key_individuals():
    response = client.get("/api/cases/demo_case_001/key-individuals", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Check that rationales exist
    assert all("rationale" in ki and len(ki["rationale"]) > 0 for ki in data)

def test_anomalies():
    response = client.get("/api/cases/demo_case_001/anomalies", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # Check that evidence references are present
    assert any(len(a.get("evidence_refs", [])) > 0 for a in data)

def test_heatmaps():
    response = client.get("/api/cases/demo_case_001/heatmaps", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "temporal" in data
    assert "geo" in data
    assert "cooccurrence" in data

def test_search():
    response = client.get("/api/search?q=Vikram", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] > 0

def test_paste_intel():
    payload = {
        "case_id": "demo_case_001",
        "text": "Informant reports suspect Rajesh Verma (+919899112233) spotted in vehicle DL-04-XY-9999 delivering contraband to Amit Sharma in Rohini.",
        "source_label": "Informant Tip 99"
    }
    response = client.post("/api/intel/paste", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    # Verify new node added or connected
    node_labels = [n["label"].lower() for n in data["nodes"]]
    assert any("rajesh verma" in nl for nl in node_labels)

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
AUTH_HEADERS = {"X-API-Key": os.environ["API_KEY"]}

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "message" in res.json()

def test_protected_endpoint_requires_api_key(client):
    res = client.get("/network")
    assert res.status_code == 401

def test_health_endpoint_is_public(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_network_endpoint(client):
    res = client.get("/network", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0

def test_communities_endpoint(client):
    res = client.get("/communities", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "modularity" in data
    assert "communities" in data

def test_predicted_links_endpoint(client):
    res = client.get("/predicted-links", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

def test_anomalies_endpoint(client):
    res = client.get("/anomalies", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

def test_add_case_endpoint(client):
    # Submit a minimal case payload
    payload = {
        "case_id": "TEST_CASE_999",
        "description": "Integration test suspect linkages",
        "nodes": [
            {
                "id": "person_test_api_999",
                "type": "Person",
                "label": "Test Suspect",
                "attributes": {"prior_cases": 0}
            }
        ],
        "edges": [
            {
                "source": "person_test_api_999",
                "target": "account_normal_0", # Connects to existing normal account
                "type": "TRANSACTION",
                "attributes": {"amount": 250.0}
            }
        ]
      }
    res = client.post("/case", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "updated_scores" in data
    assert "person_test_api_999" in data["updated_scores"]

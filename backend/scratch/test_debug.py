import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    payload = {
        "case_id": "TEST_CASE_DEBUG_1001",
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
                "target": "account_normal_0",
                "type": "TRANSACTION",
                "attributes": {"amount": 250.0}
            }
        ]
    }
    print("Calling /case...")
    res = client.post("/case", json=payload)
    print("Status:", res.status_code)
    if res.status_code != 200:
        print("Error:", res.text)
    else:
        print("Success:", res.json())

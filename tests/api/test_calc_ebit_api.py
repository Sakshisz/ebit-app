
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_calculate_ebit_api():
    payload = {
        "assignments": [
            {
                "row_index": 0,
                "consultant_id": 1,
                "project_id": 1,
                "utilization": 1.0,
                "project_percent": 1.0,
                "consultant_work_pct": 1.0,
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "utlegg_mode": "Prosent",
                "expense_pct": 0.1
            }
        ],
        "yearly_work_hours": 1625,
        "pex_pct": 0.3,
        "month": 1
    }

    response = client.post("/calculate-ebit", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert "department" in data

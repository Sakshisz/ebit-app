import pytest
import json
import os
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Create test data files before running tests"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Create test consultants
    consultants = {
        "last_id": 2,
        "items": [
            {
                "id": 1,
                "name": "Test Consultant 1",
                "salary": 600000,
                "default_utilization": 0.8
            },
            {
                "id": 2,
                "name": "Test Consultant 2",
                "salary": 700000,
                "default_utilization": 0.85
            }
        ]
    }

    # Create test projects
    projects = {
        "last_id": 2,
        "items": [
            {
                "id": 1,
                "name": "Test Project 1",
                "hourly_rate": 1200
            },
            {
                "id": 2,
                "name": "Test Project 2",
                "hourly_rate": 1500
            }
        ]
    }

    # Create test settings
    settings = {
        "pex_pct": 0.32,
        "expense_pct": 0.40,
        "yearly_work_hours": 1625
    }

    # Write files
    with open(data_dir / "consultants.json", "w", encoding="utf-8") as f:
        json.dump(consultants, f, ensure_ascii=False, indent=2)

    with open(data_dir / "projects.json", "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)

    with open(data_dir / "settings.json", "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

    yield

    # Cleanup is optional - you can keep test data or remove it

"""
test_e2e.py
Owner: Krutika
Task 4, Week 4 — End-to-End Integration Test

Tests the full pipeline via the running API server.
Requires: docker-compose up (or uvicorn running locally on port 8000)
Requires: data/test/held_out_contract.pdf (a real test PDF)

Run with: pytest tests/test_e2e.py -v
"""

import re
import pytest
import requests

BASE_URL = "http://localhost:8000"


def test_health_check():
    """API server is reachable and healthy."""
    # TODO (Krutika): Uncomment once API is running
    # response = requests.get(f"{BASE_URL}/health")
    # assert response.status_code == 200
    # assert response.json()["status"] == "healthy"
    pass


def test_full_pipeline_on_held_out_contract():
    """
    Upload a real PDF and verify the full pipeline returns valid entities.

    Prerequisites:
        - docker-compose up (or uvicorn api.main:app running on port 8000)
        - data/test/held_out_contract.pdf exists
    """
    # TODO (Krutika): Implement once API is operational
    # with open("data/test/held_out_contract.pdf", "rb") as f:
    #     response = requests.post(
    #         f"{BASE_URL}/extract",
    #         files={"file": ("contract.pdf", f, "application/pdf")}
    #     )
    #
    # assert response.status_code == 200
    # data = response.json()
    #
    # assert len(data["entities"]["parties"]) >= 2
    # assert data["entities"]["effective_date"] is not None
    # assert re.match(r'\d{4}-\d{2}-\d{2}', data["entities"]["effective_date"])
    # assert data["entities"]["total_amount"] is not None
    # assert data["validation_flags"] == []
    pass

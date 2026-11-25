"""The API runs (already passes): create a session and read it back."""

from __future__ import annotations

from fastapi.testclient import TestClient

from report_builder.api import create_app


def test_create_and_get(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    created = client.post("/sessions", json={"dataset": "harbour_bikes", "month": "2026-06"},
                          headers={"X-User": "ana"})
    assert created.status_code == 201
    sid = created.json()["id"]
    assert client.get(f"/sessions/{sid}", headers={"X-User": "ana"}).json()["month"] == "2026-06"
    assert [s["id"] for s in client.get("/sessions", headers={"X-User": "ana"}).json()] == [sid]


def test_unknown_dataset_and_month(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    h = {"X-User": "ana"}
    assert client.post("/sessions", json={"dataset": "nope", "month": "2026-06"}, headers=h).status_code == 404
    assert client.post("/sessions", json={"dataset": "harbour_bikes", "month": "2030-01"},
                       headers=h).status_code == 422

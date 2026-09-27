"""FastAPI → MCP Client → MCP Server（stdio）の疎通テスト。Geminiは呼ばない（fakeモード）。"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_D1 = json.loads((ROOT / "app/static/sample_d1.json").read_text(encoding="utf-8"))


@pytest.fixture
def client():
    return TestClient(app)


def test_generate_via_mcp_fake(client, monkeypatch):
    monkeypatch.setenv("QUIZ_GENERATOR", "fake")
    res = client.post("/api/v1/commits", json=SAMPLE_D1)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "ok"
    assert body["validation_errors"] == []
    assert len(body["result"]["questions"]) == 3


def test_missing_api_key_is_502(client, monkeypatch):
    monkeypatch.setenv("QUIZ_GENERATOR", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    res = client.post("/api/v1/commits", json=SAMPLE_D1)
    assert res.status_code == 502
    assert "GEMINI_API_KEY" in res.json()["detail"]


def test_invalid_d1_is_422(client):
    bad = dict(SAMPLE_D1, commit_sha="xyz")
    assert client.post("/api/v1/commits", json=bad).status_code == 422


def test_insufficient_evidence_is_422(client, monkeypatch):
    monkeypatch.setenv("QUIZ_GENERATOR", "fake_insufficient")
    res = client.post("/api/v1/commits", json=SAMPLE_D1)
    assert res.status_code == 422
    assert "INSUFFICIENT_EVIDENCE" in res.json()["detail"]

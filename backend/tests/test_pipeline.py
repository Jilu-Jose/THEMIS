"""Pipeline and API security tests: key requirements and document staging."""
import os
import time

os.environ["THEMIS_DATA_DIR"] = os.path.join(os.path.dirname(__file__), "_data")

from fastapi.testclient import TestClient  # noqa: E402
from app import config  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_run_requires_api_key(monkeypatch):
    """Attempting to run without an API key must fail immediately with HTTP 400."""
    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    sid = client.post("/api/sessions/demo").json()["id"]
    r = client.post(f"/api/sessions/{sid}/run", json={})
    assert r.status_code == 400
    assert "GROQ_API_KEY is required" in r.json()["detail"]


def test_upload_path_and_exports():
    """Verify document upload validation and staging."""
    from app.demo_data import build_demo
    tender, bids = build_demo()
    files = [("tender", ("tender.md", tender.encode(), "text/markdown"))]
    files += [("bids", (b["filename"], b["text"].encode(), "text/markdown")) for b in bids]
    r = client.post("/api/sessions", files=files, data={"meta": "[]"})
    assert r.status_code == 200 and len(r.json()["bids"]) == 4

    bad = client.post("/api/sessions", files=[("tender", ("t.exe", b"x", "x")), ("bids", ("b.md", b"y", "x"))])
    assert bad.status_code == 400

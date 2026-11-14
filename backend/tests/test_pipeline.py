"""End-to-end tests in offline demo mode (no API key, no network).   Run:  pytest -q"""
import os
import time

os.environ["THEMIS_DEMO"] = "1"
os.environ["THEMIS_DEMO_DELAY"] = "0"
os.environ["THEMIS_DATA_DIR"] = os.path.join(os.path.dirname(__file__), "_data")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def run_demo():
    sid = client.post("/api/sessions/demo").json()["id"]
    assert client.post(f"/api/sessions/{sid}/run", json={}).json()["started"]
    for _ in range(200):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in ("complete", "error"):
            return s
        time.sleep(0.1)
    raise AssertionError("pipeline did not finish")


def test_planted_issues_are_caught():
    s = run_demo()
    assert s["status"] == "complete", s["error"]
    elig = {n: c["verdict"] for n, c in s["compliance"].items()}
    assert elig["HydroNova Systems Pvt Ltd"] == "DISQUALIFIED"
    types = [(f["type"], f["bidders"]) for f in s["risk_flags"]]
    assert any(t == "SIMILARITY" for t, _ in types)
    assert any(t == "PRICE_OUTLIER" and "AquaSense Infra Pvt Ltd" in b for t, b in types)
    assert any(t == "ARITHMETIC" and "BlueRiver Analytics Pvt Ltd" in b for t, b in types)
    fin = s["financial"]["BlueRiver Analytics Pvt Ltd"]
    assert fin["stated_total"] == 45000000 and fin["recomputed_total"] == 48000000
    by = {r["bidder"]: r for r in s["ranking"]}
    assert by["SecureFlow Technologies Pvt Ltd"]["rank"] == 1
    assert by["AquaSense Infra Pvt Ltd"]["status"] == "PENDING_DISQUALIFICATION"
    assert s["blockers"] == ["AquaSense Infra Pvt Ltd"]


def test_approval_is_gated_until_human_resolves_disqualification():
    s = run_demo()
    r = client.post(f"/api/sessions/{s['id']}/approval", json={"decision": "APPROVED", "officer": "A. Officer"})
    assert r.status_code == 409
    d = next(d for d in s["decisions"] if "RECOMMEND_DISQUALIFY" in d["actions"].values())
    bidder = next(b for b, a in d["actions"].items() if a == "RECOMMEND_DISQUALIFY")
    r = client.post(f"/api/sessions/{s['id']}/rulings",
                    json={"index": d["index"], "bidder": bidder, "decision": "concur", "officer": "A. Officer"})
    assert r.status_code == 200 and r.json()["blockers"] == []
    r = client.post(f"/api/sessions/{s['id']}/approval", json={"decision": "APPROVED", "officer": "A. Officer"})
    assert r.status_code == 200 and r.json()["approval"]["winner"] == "SecureFlow Technologies Pvt Ltd"


def test_audit_chain_detects_tampering():
    s = run_demo()
    assert client.get(f"/api/sessions/{s['id']}/audit/verify").json()["valid"] is True
    from app.state import store
    store.get(s["id"]).audit[3]["detail"] = {"tampered": True}
    v = client.get(f"/api/sessions/{s['id']}/audit/verify").json()
    assert v["valid"] is False and v["first_bad_seq"] == 4


def test_upload_path_and_exports():
    from app.demo_data import build_demo
    tender, bids = build_demo()
    files = [("tender", ("tender.md", tender.encode(), "text/markdown"))]
    files += [("bids", (b["filename"], b["text"].encode(), "text/markdown")) for b in bids]
    r = client.post("/api/sessions", files=files, data={"meta": "[]"})
    assert r.status_code == 200 and len(r.json()["bids"]) == 4
    bad = client.post("/api/sessions", files=[("tender", ("t.exe", b"x", "x")), ("bids", ("b.md", b"y", "x"))])
    assert bad.status_code == 400
    s = run_demo()
    for kind in ("report.md", "ranking.csv", "audit.json", "full.json"):
        assert client.get(f"/api/sessions/{s['id']}/export/{kind}").status_code == 200

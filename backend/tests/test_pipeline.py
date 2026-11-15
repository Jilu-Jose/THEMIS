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


def test_delete_session():
    """Verify session deletion endpoint removes data properly."""
    sid = client.post("/api/sessions/demo").json()["id"]
    assert client.get(f"/api/sessions/{sid}").status_code == 200
    r = client.delete(f"/api/sessions/{sid}")
    assert r.status_code == 200 and r.json()["deleted"] is True
    assert client.get(f"/api/sessions/{sid}").status_code == 404


def test_benchmark_data_structure():
    """Verify 4 synthetic benchmark tenders are properly structured with 3-4 bids each and designated winners."""
    from app.benchmark_data import build_benchmark_data
    tenders = build_benchmark_data()
    assert len(tenders) == 4

    for tender_text, bids, known_winner, known_dq in tenders:
        assert isinstance(tender_text, str) and len(tender_text) > 100
        assert 3 <= len(bids) <= 4
        bid_names = [b["name"] for b in bids]
        for b in bids:
            assert "name" in b and "filename" in b and "text" in b and "submitted_at" in b
            assert len(b["text"]) > 100
        assert known_winner in bid_names
        for dq in known_dq:
            assert dq in bid_names
        assert known_winner not in known_dq


def test_clarification_state_and_endpoints():
    """Verify clarification structure in session and retrieval endpoint."""
    sid = client.post("/api/sessions/demo").json()["id"]
    # Check session to_public has clarifications field
    s_data = client.get(f"/api/sessions/{sid}").json()
    assert "clarifications" in s_data
    assert isinstance(s_data["clarifications"], dict)

    # Check GET clarifications endpoint
    r = client.get(f"/api/sessions/{sid}/clarifications")
    assert r.status_code == 200
    assert r.json() == {}


def test_semantic_kernel_integration():
    """Verify Microsoft Semantic Kernel integration, plugins, and health endpoint."""
    import asyncio
    import semantic_kernel as sk
    from app.sk_kernel import build_kernel

    # 1. Health endpoint exposes semantic-kernel framework
    h = client.get("/api/health").json()
    assert h["framework"] == "semantic-kernel"
    assert "RetrievalPlugin" in h["plugins"]
    assert "FinancialArithmeticPlugin" in h["plugins"]

    # 2. Kernel builds and registers all agent plugins
    kernel = build_kernel(api_key="mock_key_for_test")
    assert "RetrievalPlugin" in kernel.plugins
    assert "FinancialArithmeticPlugin" in kernel.plugins
    assert "TenderParserPlugin" in kernel.plugins
    assert "ClarificationAgentPlugin" in kernel.plugins

    # 3. Kernel function invocation works for grounded retrieval & arithmetic
    async def invoke_tools():
        # Test financial arithmetic plugin
        func = kernel.get_function("FinancialArithmeticPlugin", "recompute_item")
        res = await kernel.invoke(func, qty=10, unit_price=250.5)
        assert float(str(res)) == 2505.0

        # Test quote verification plugin
        v_func = kernel.get_function("RetrievalPlugin", "verify_quote")
        v_res = await kernel.invoke(v_func, quote="NABL certified", document_text="All probes are NABL certified standards.")
        assert str(v_res).lower() == "true"

    asyncio.run(invoke_tools())



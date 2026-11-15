"""Exercises the real-Groq code path with a fake client (no network): parsing, retries, JSON-mode fallback."""
import json
import os
import time
import types

os.environ["THEMIS_DEMO"] = "1"
os.environ["THEMIS_DEMO_DELAY"] = "0"
os.environ["THEMIS_DATA_DIR"] = os.path.join(os.path.dirname(__file__), "_data")
os.environ["GROQ_API_KEY"] = "test-key"

from app import llm as llm_mod  # noqa: E402
from app.demo_data import build_demo  # noqa: E402
from app.agents import compliance, parser  # noqa: E402


def _resp(content):
    msg = types.SimpleNamespace(content=content)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)],
                                 usage=types.SimpleNamespace(total_tokens=123))


class FakeClient:
    """Answers like Groq would: JSON (sometimes wrapped in prose), with scripted failures."""
    def __init__(self, fail_first=0, reject_json_mode=False, wrap=False):
        self.calls, self.fail_first, self.reject, self.wrap = [], fail_first, reject_json_mode, wrap
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls.append(kw)
        if self.fail_first:
            self.fail_first -= 1
            raise RuntimeError("429 rate limit")
        if self.reject and "response_format" in kw:
            raise RuntimeError("400 response_format json not supported")
        user = kw["messages"][-1]["content"]
        if "Tender No" in user:
            data = {"tender_id": "PHED/IOT/2026/017", "title": "Water Quality",
                    "eligibility": [{"id": f"E{i}", "title": f"Rule {i}", "requirement": "Required", "evidence": "Doc"} for i in range(1, 8)],
                    "technical": [{"id": f"T{i}", "criterion": f"Criteria {i}", "weight": 20, "description": "Desc"} for i in range(1, 6)],
                    "scoring_formula": "QCBS", "min_technical_score": 60}
        else:
            data = {"results": [{"id": f"E{i}", "status": "PASS", "evidence_quote": "Valid", "reason": "Meets criteria"} for i in range(1, 8)]}
        out = json.dumps(data)
        return _resp(("Here is the JSON:\n" + out + "\nDone.") if self.wrap else out)


def make(client):
    l = llm_mod.LLM("groq", "openai/gpt-oss-120b", "high")
    l.client = client
    return l


def test_groq_agents_parse_and_pass_model_and_effort(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    c = FakeClient(wrap=True)
    l = make(c)
    tender, bids = build_demo()
    rubric = parser.run(l, tender)
    assert len(rubric["eligibility"]) == 7 and abs(sum(t["weight"] for t in rubric["technical"]) - 100) < 1e-6
    res = compliance.run(l, rubric, bids[0]["name"], bids[0]["text"])
    assert res["verdict"] == "ELIGIBLE"
    first = c.calls[0]
    assert first["model"] == "openai/gpt-oss-120b" and first["reasoning_effort"] == "high"
    assert first["response_format"] == {"type": "json_object"}
    assert l.stats["Compliance"]["tokens"] == 123


def test_retry_after_rate_limit(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    c = FakeClient(fail_first=2)
    l = make(c)
    tender, _ = build_demo()
    assert parser.run(l, tender)["tender_id"]
    assert len(c.calls) == 3


def test_json_mode_rejected_falls_back_to_plain_parsing(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    c = FakeClient(reject_json_mode=True, wrap=True)
    l = make(c)
    tender, _ = build_demo()
    assert parser.run(l, tender)["tender_id"]
    assert "response_format" not in c.calls[-1]


def test_gives_up_after_retries(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    l = make(FakeClient(fail_first=99))
    try:
        l.json("TenderParser", "s", "Tender No: x")
        raise AssertionError("should have raised")
    except RuntimeError as e:
        assert "failed after 3 attempts" in str(e)

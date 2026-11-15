"""T.H.E.M.I.S API + static frontend host.   Run:  uvicorn app.main:app --port 8000"""
import asyncio
import csv
import io
import json
import threading
from datetime import datetime

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import actions, config
from .demo_data import build_demo
from .documents import extract_text, sha256_bytes
from .pipeline import run_pipeline
from .state import Session, store

app = FastAPI(title="T.H.E.M.I.S", version="1.0.0",
              description="Tender Human-in-the-loop Evaluation & Misconduct Inspection System")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

MAX_BYTES = 25 * 1024 * 1024
ALLOWED = (".pdf", ".txt", ".md")


# ------------------------------------------------------------------ helpers
def get_session(sid: str) -> Session:
    s = store.get(sid)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


def _wrap(fn, *a):
    try:
        return fn(*a)
    except actions.ActionError as e:
        raise HTTPException(e.code, str(e))


def _doc(filename: str, text: str, raw: bytes) -> dict:
    return {"filename": filename, "sha256": sha256_bytes(raw), "words": len(text.split()), "text": text}


@app.exception_handler(Exception)
async def unhandled(_, exc):
    return JSONResponse({"detail": f"{type(exc).__name__}: {exc}"}, status_code=500)


# ------------------------------------------------------------------ meta
@app.get("/api/health")
def health():
    import semantic_kernel as _sk
    return {
        "ok": True,
        "mode": config.llm_mode(),
        "model": config.DEFAULT_MODEL,
        "models": config.MODELS,
        "has_key": bool(config.GROQ_API_KEY),
        "defaults": config.DEFAULT_SETTINGS,
        "framework": "semantic-kernel",
        "semantic_kernel_version": getattr(_sk, "__version__", "1.47.0"),
        "plugins": [
            "RetrievalPlugin",
            "FinancialArithmeticPlugin",
            "TenderParserPlugin",
            "ClarificationAgentPlugin",
        ],
    }


# ------------------------------------------------------------------ sessions
@app.get("/api/sessions")
def list_sessions():
    return [{"id": s.id, "created_at": s.created_at, "status": s.status, "mode": s.mode,
             "title": (s.rubric or {}).get("title") or (s.tender or {}).get("filename"), "bids": len(s.bids)}
            for s in sorted(store.sessions.values(), key=lambda x: x.created_at, reverse=True)]


@app.get("/api/sessions/latest")
def latest():
    s = store.latest()
    return s.to_public() if s else None


@app.post("/api/sessions/demo")
def create_demo():
    s = Session()
    tender, bids = build_demo()
    s.tender = _doc("tender_notice.md", tender, tender.encode())
    for b in bids:
        s.bids[b["name"]] = {**_doc(b["filename"], b["text"], b["text"].encode()), "submitted_at": b["submitted_at"]}
    store.add(s)
    s.add_audit("System", "session_created", {"source": "demo data", "bids": len(bids)})
    store.save(s)
    return s.to_public()


@app.post("/api/sessions")
async def create_session(tender: UploadFile = File(...), bids: list[UploadFile] = File(...), meta: str = Form("[]")):
    """Multipart upload: one tender file + one file per bidder. `meta` = JSON list aligned with `bids`:
    [{"name": "Bidder Pvt Ltd", "submitted_at": "2026-10-02 10:14"}, ...]"""
    if not 1 <= len(bids) <= 25:
        raise HTTPException(400, "Upload between 1 and 25 bid files.")
    try:
        meta_list = json.loads(meta or "[]")
    except json.JSONDecodeError:
        raise HTTPException(400, "meta must be valid JSON.")
    s = Session()

    async def read(f: UploadFile, label: str):
        if not f.filename.lower().endswith(ALLOWED):
            raise HTTPException(400, f"{label}: only PDF, TXT or MD files are supported ({f.filename}).")
        raw = await f.read()
        if len(raw) > MAX_BYTES:
            raise HTTPException(400, f"{label}: file larger than 25 MB.")
        try:
            text = extract_text(f.filename, raw)
        except Exception as e:                                   # noqa: BLE001
            raise HTTPException(400, f"{label}: could not read file ({e}).")
        if len(text.split()) < 20:
            raise HTTPException(400, f"{label}: no extractable text (scanned PDF? OCR is not supported).")
        return _doc(f.filename, text, raw)

    s.tender = await read(tender, "Tender")
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    for i, f in enumerate(bids):
        m = meta_list[i] if i < len(meta_list) and isinstance(meta_list[i], dict) else {}
        base = f.filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip()
        name = (m.get("name") or base).strip()[:80] or f"Bidder {i + 1}"
        if name in s.bids:
            name = f"{name} ({i + 1})"
        s.bids[name] = {**(await read(f, name)), "submitted_at": (m.get("submitted_at") or stamp)}
    store.add(s)
    s.add_audit("System", "session_created", {"source": "upload", "bids": len(s.bids)})
    store.save(s)
    return s.to_public()


@app.get("/api/sessions/{sid}")
def get_one(sid: str):
    return get_session(sid).to_public()


@app.delete("/api/sessions/{sid}")
def delete_session(sid: str):
    store.delete(sid)
    return {"deleted": True, "id": sid}


@app.delete("/api/sessions")
def clear_all_sessions():
    store.clear()
    return {"cleared": True}


class RunBody(BaseModel):
    settings: dict | None = None


@app.post("/api/sessions/{sid}/run")
def run(sid: str, body: RunBody | None = None):
    s = get_session(sid)
    if s.status == "running":
        raise HTTPException(409, "Evaluation already running.")
    if not s.tender or not s.bids:
        raise HTTPException(400, "Session has no documents.")
    if not config.GROQ_API_KEY:
        raise HTTPException(400, "GROQ_API_KEY is required to run the evaluation. Please configure your key in .env.")
    st = dict(s.settings)
    for k, v in ((body.settings if body else None) or {}).items():
        if k in config.DEFAULT_SETTINGS:
            st[k] = v
    if st["reasoning_effort"] not in ("low", "medium", "high"):
        raise HTTPException(400, "reasoning_effort must be low, medium or high.")
    for k in ("low_price_ratio", "high_price_ratio", "similarity_threshold"):
        try:
            st[k] = float(st[k])
        except (TypeError, ValueError):
            raise HTTPException(400, f"{k} must be a number.")
    if not (0 < st["low_price_ratio"] < 1 < st["high_price_ratio"]) or not (0 < st["similarity_threshold"] < 1):
        raise HTTPException(400, "Thresholds out of range (low < 1 < high; similarity between 0 and 1).")
    st["blind_technical"] = bool(st["blind_technical"])
    s.settings = st
    s.mode = config.llm_mode()
    start = len(s.events)
    threading.Thread(target=run_pipeline, args=(s,), daemon=True).start()
    return {"started": True, "from": start, "mode": s.mode}


@app.get("/api/sessions/{sid}/events")
async def events(sid: str, frm: int = 0):
    s = get_session(sid)

    async def gen():
        i, idle = frm, 0
        while True:
            batch = s.events[i:]
            for e in batch:
                yield f"id: {e['i']}\ndata: {json.dumps(e, default=str)}\n\n"
                i = e["i"] + 1
            if batch:
                idle = 0
            if s.status in ("complete", "error") and i >= len(s.events):
                break
            idle += 1
            if idle % 100 == 0:
                yield ": keepalive\n\n"
            await asyncio.sleep(0.15)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ------------------------------------------------------------------ human actions
class RulingBody(BaseModel):
    index: int
    bidder: str
    decision: str
    action: str | None = None
    note: str | None = None
    officer: str | None = None


class NoteBody(BaseModel):
    target: str
    kind: str = "note"
    text: str = ""
    officer: str | None = None


class ClarificationDraftBody(BaseModel):
    bidder: str
    criterion_id: str
    officer: str | None = None
    llm_mode: str | None = None
    model: str | None = None
    effort: str | None = None


class ClarificationReplyBody(BaseModel):
    bidder: str
    criterion_id: str
    vendor_reply: str
    officer: str | None = None
    llm_mode: str | None = None
    model: str | None = None
    effort: str | None = None


class OfficerBody(BaseModel):
    officer: str | None = None


class ApprovalBody(BaseModel):
    decision: str
    officer: str
    comment: str | None = None


@app.post("/api/sessions/{sid}/rulings")
def rulings(sid: str, b: RulingBody):
    return _wrap(actions.resolve_decision, get_session(sid), b.index, b.bidder, b.decision, b.action, b.note, b.officer)


@app.post("/api/sessions/{sid}/notes")
def notes(sid: str, b: NoteBody):
    return _wrap(actions.add_note, get_session(sid), b.target, b.kind, b.text, b.officer)


@app.post("/api/sessions/{sid}/clarifications/draft")
def draft_clarification(sid: str, b: ClarificationDraftBody):
    return _wrap(actions.draft_clarification, get_session(sid), b.bidder, b.criterion_id, b.officer, b.llm_mode, b.model, b.effort)


@app.post("/api/sessions/{sid}/clarifications/reply")
def submit_reply(sid: str, b: ClarificationReplyBody):
    return _wrap(actions.submit_clarification_reply, get_session(sid), b.bidder, b.criterion_id, b.vendor_reply, b.officer, b.llm_mode, b.model, b.effort)


@app.get("/api/sessions/{sid}/clarifications")
def get_clarifications(sid: str):
    return get_session(sid).clarifications


@app.post("/api/sessions/{sid}/attest-blind")
def attest(sid: str, b: OfficerBody):
    return _wrap(actions.attest_blind, get_session(sid), b.officer)


@app.post("/api/sessions/{sid}/reveal-identities")
def reveal(sid: str, b: OfficerBody):
    return _wrap(actions.reveal_identities, get_session(sid), b.officer)


@app.post("/api/sessions/{sid}/approval")
def approval(sid: str, b: ApprovalBody):
    return _wrap(actions.approve, get_session(sid), b.decision, b.officer, b.comment)


@app.post("/api/sessions/{sid}/report/regenerate")
def regen(sid: str):
    return _wrap(actions.regenerate_report, get_session(sid))


# ------------------------------------------------------------------ audit + exports
@app.get("/api/sessions/{sid}/audit")
def audit(sid: str):
    return get_session(sid).audit


@app.get("/api/sessions/{sid}/audit/verify")
def audit_verify(sid: str):
    return get_session(sid).verify_audit()


@app.get("/api/sessions/{sid}/export/{kind}")
def export(sid: str, kind: str):
    s = get_session(sid)
    name = (s.rubric or {}).get("tender_id", "tender").replace("/", "-")
    if kind == "report.md":
        return Response(s.report_md, media_type="text/markdown",
                        headers={"Content-Disposition": f'attachment; filename="{name}_report.md"'})
    if kind == "ranking.csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Rank", "Bidder", "Status", "Eligibility", "Technical raw", "Chair action", "Penalty",
                    "Technical adj", "Price INR", "Financial score", "Final QCBS"])
        for r in s.ranking:
            w.writerow([r["rank"] or "-", r["bidder"], r["status_label"], r["eligibility"], r["tech_raw"], r["chair_action"],
                        r["penalty"], r["tech_adj"], r["price"], r["fin_score"], r["final_score"]])
        return Response(buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{name}_ranking.csv"'})
    if kind == "audit.json":
        body = {"session": s.id, "chain": s.verify_audit(), "records": s.audit}
        return Response(json.dumps(body, indent=2, default=str), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{name}_audit.json"'})
    if kind == "full.json":
        return Response(json.dumps(s.to_public(), indent=2, default=str), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{name}_full.json"'})
    raise HTTPException(404, "Unknown export")


# ------------------------------------------------------------------ frontend (must be last)
if config.FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="frontend")

"""Session state: documents, results, hash-chained audit log, event stream, JSON persistence."""
import hashlib
import json
import threading
import time
import uuid
from datetime import datetime, timezone

from . import config
from .agents import scoring

STAGES = [
    ("parser", "Tender Parser"),
    ("compliance", "Compliance"),
    ("technical", "Technical (blind)"),
    ("financial", "Financial"),
    ("risk", "Risk & Fraud"),
    ("chair", "Chair"),
    ("scoring", "QCBS Scoring"),
    ("report", "Report"),
    ("approval", "Human Approval"),
]
GENESIS = "0" * 64


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Session:
    def __init__(self, sid=None):
        self.lock = threading.RLock()
        self.id = sid or uuid.uuid4().hex[:10]
        self.created_at = now_iso()
        self.status = "created"          # created | running | complete | error
        self.error = None
        self.mode = config.llm_mode()
        self.settings = dict(config.DEFAULT_SETTINGS)
        self.tender = None               # {filename, sha256, words, text}
        self.bids = {}                   # name -> {filename, sha256, words, text, submitted_at}
        self.reset_results()
        self.audit = []
        self.events = []
        self.human_actions = []
        self.approval = None
        self.blind_attested = None
        self.identities_revealed = False

    def reset_results(self):
        self.stages = [{"id": i, "label": l, "status": "pending", "summary": "", "seconds": None} for i, l in STAGES]
        self.rubric = None
        self.compliance, self.technical, self.financial = {}, {}, {}
        self.risk_flags, self.decisions, self.ranking = [], [], []
        self.aliases = {}
        self.report_md, self.report_stale = "", False
        self.agent_stats = {}

    # ------------------------------------------------------------ events + audit
    def emit(self, kind, **kw):
        with self.lock:
            self.events.append({"i": len(self.events), "t": round(time.time(), 3), "kind": kind, **kw})

    def add_audit(self, agent, action, detail=None):
        """Append a tamper-evident audit record: hash = SHA-256(prev_hash + canonical record)."""
        with self.lock:
            prev = self.audit[-1]["hash"] if self.audit else GENESIS
            rec = {"seq": len(self.audit) + 1, "time": now_iso(), "agent": agent, "action": action, "detail": detail}
            canon = json.dumps(rec, sort_keys=True, default=str, ensure_ascii=False)
            rec["prev_hash"] = prev
            rec["hash"] = hashlib.sha256((prev + canon).encode()).hexdigest()
            self.audit.append(rec)
            self.emit("log", agent=agent, action=action, detail=detail, seq=rec["seq"])
            return rec

    def verify_audit(self):
        prev, bad = GENESIS, None
        for rec in self.audit:
            core = {k: rec[k] for k in ("seq", "time", "agent", "action", "detail")}
            canon = json.dumps(core, sort_keys=True, default=str, ensure_ascii=False)
            if rec["prev_hash"] != prev or rec["hash"] != hashlib.sha256((prev + canon).encode()).hexdigest():
                bad = rec["seq"]
                break
            prev = rec["hash"]
        return {"valid": bad is None, "records": len(self.audit), "first_bad_seq": bad, "head": prev}

    # ------------------------------------------------------------ stages
    def set_stage(self, sid, status, summary=None, seconds=None):
        with self.lock:
            for st in self.stages:
                if st["id"] == sid:
                    st["status"] = status
                    if summary is not None:
                        st["summary"] = summary
                    if seconds is not None:
                        st["seconds"] = round(seconds, 2)
            self.emit("stage", stage=sid, status=status, summary=summary, seconds=seconds)

    # ------------------------------------------------------------ views
    def to_public(self):
        with self.lock:
            return {
                "id": self.id, "created_at": self.created_at, "status": self.status, "error": self.error,
                "mode": self.mode, "settings": self.settings,
                "tender": {k: v for k, v in (self.tender or {}).items() if k != "text"} or None,
                "bids": [{"name": n, **{k: v for k, v in b.items() if k != "text"}} for n, b in self.bids.items()],
                "stages": self.stages, "rubric": self.rubric,
                "compliance": self.compliance, "technical": self.technical, "financial": self.financial,
                "risk_flags": self.risk_flags, "decisions": self.decisions, "ranking": self.ranking,
                "blockers": scoring.blockers(self.decisions),
                "report_md": self.report_md, "report_stale": self.report_stale,
                "approval": self.approval, "human_actions": self.human_actions,
                "aliases": self.aliases, "agent_stats": self.agent_stats,
                "blind_attested": self.blind_attested, "identities_revealed": self.identities_revealed,
                "audit_len": len(self.audit), "event_count": len(self.events),
            }

    def to_disk(self):
        d = self.to_public()
        d["tender_text"] = (self.tender or {}).get("text", "")
        d["bid_texts"] = {n: b["text"] for n, b in self.bids.items()}
        d["audit"] = self.audit
        return d

    @classmethod
    def from_disk(cls, d):
        s = cls(d["id"])
        for k in ("created_at", "status", "error", "mode", "settings", "stages", "rubric", "compliance", "technical",
                  "financial", "risk_flags", "decisions", "ranking", "report_md", "report_stale", "approval",
                  "human_actions", "aliases", "agent_stats", "blind_attested", "identities_revealed", "audit"):
            setattr(s, k, d.get(k, getattr(s, k)))
        if d.get("tender"):
            s.tender = {**d["tender"], "text": d.get("tender_text", "")}
        for b in d.get("bids", []):
            s.bids[b["name"]] = {**{k: v for k, v in b.items() if k != "name"}, "text": d.get("bid_texts", {}).get(b["name"], "")}
        if s.status == "running":           # server restarted mid-run
            s.status, s.error = "error", "Server restarted while the evaluation was running."
        return s


class Store:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        for f in sorted(config.SESSIONS_DIR.glob("*.json")):
            try:
                s = Session.from_disk(json.loads(f.read_text(encoding="utf-8")))
                self.sessions[s.id] = s
            except Exception:
                continue

    def add(self, s):
        with self.lock:
            self.sessions[s.id] = s

    def get(self, sid):
        return self.sessions.get(sid)

    def latest(self):
        return max(self.sessions.values(), key=lambda s: s.created_at, default=None)

    def save(self, s):
        try:
            (config.SESSIONS_DIR / f"{s.id}.json").write_text(
                json.dumps(s.to_disk(), ensure_ascii=False, default=str), encoding="utf-8")
        except Exception:
            pass


store = Store()

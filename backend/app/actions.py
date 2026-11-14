"""Human-in-the-loop actions: concur / override Chair rulings, notes, approval, report refresh."""
import hashlib
import json

from .agents import report, scoring
from .agents.chair import ACTIONS
from .llm import LLM
from .state import store, now_iso


class ActionError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


def _need_complete(s):
    if s.status != "complete":
        raise ActionError("Evaluation has not completed yet.", 409)


def _rerank(s):
    s.ranking = scoring.run(s.rubric, s.compliance, s.technical, s.financial, s.decisions)
    s.report_stale = True


def resolve_decision(s, idx, bidder, decision, action, note, officer):
    _need_complete(s)
    if s.approval:
        raise ActionError("The evaluation is already signed off; start a new evaluation to change rulings.", 409)
    d = next((x for x in s.decisions if x["index"] == idx), None)
    if not d or bidder not in d["bidders"]:
        raise ActionError("Unknown ruling or bidder.", 404)
    if decision not in ("concur", "override"):
        raise ActionError("decision must be 'concur' or 'override'.")
    if decision == "override" and action not in ACTIONS:
        raise ActionError(f"action must be one of {ACTIONS}")
    officer = (officer or "").strip() or "Evaluation Officer"
    before = d["actions"].get(bidder)
    with s.lock:
        d.setdefault("human", {})[bidder] = {"decision": decision, "action": action if decision == "override" else None,
                                              "note": (note or "").strip(), "by": officer, "at": now_iso()}
        _rerank(s)
    s.human_actions.append({"type": "ruling_" + decision, "target": f"{d['flag_type']}:{bidder}", "by": officer,
                            "note": (note or "").strip(), "at": now_iso()})
    s.add_audit("HumanCommittee", "ruling_" + decision,
                {"flag": d["flag_type"], "bidder": bidder, "ai_action": before, "human_action": action, "by": officer, "note": note})
    store.save(s)
    return s.to_public()


def add_note(s, target, kind, text, officer):
    _need_complete(s)
    if kind not in ("note", "clarification", "concur"):
        raise ActionError("kind must be note, clarification or concur.")
    officer = (officer or "").strip() or "Evaluation Officer"
    rec = {"type": kind, "target": target, "by": officer, "note": (text or "").strip(), "at": now_iso()}
    s.human_actions.append(rec)
    s.add_audit("HumanCommittee", f"committee_{kind}", rec)
    store.save(s)
    return s.to_public()


def attest_blind(s, officer):
    _need_complete(s)
    officer = (officer or "").strip() or "Evaluation Officer"
    s.blind_attested = {"by": officer, "at": now_iso()}
    s.add_audit("HumanCommittee", "blind_scores_attested", s.blind_attested)
    store.save(s)
    return s.to_public()


def reveal_identities(s, officer):
    _need_complete(s)
    officer = (officer or "").strip() or "Evaluation Officer"
    s.identities_revealed = True
    s.add_audit("HumanCommittee", "identities_revealed", {"by": officer, "at": now_iso()})
    store.save(s)
    return s.to_public()


def approve(s, decision, officer, comment):
    _need_complete(s)
    if s.approval:
        raise ActionError("Already signed off.", 409)
    if decision not in ("APPROVED", "REJECTED"):
        raise ActionError("decision must be APPROVED or REJECTED.")
    officer = (officer or "").strip()
    if not officer:
        raise ActionError("Officer name is required for sign-off.")
    pending = scoring.blockers(s.decisions)
    if decision == "APPROVED" and pending:
        raise ActionError("Resolve the recommended disqualification(s) first: " + ", ".join(pending), 409)
    win = next((r for r in s.ranking if r["rank"] == 1), None)
    if decision == "APPROVED" and not win:
        raise ActionError("There is no qualified bidder to approve.", 409)
    head = s.audit[-1]["hash"] if s.audit else ""
    digest = hashlib.sha256(json.dumps(s.ranking, sort_keys=True, default=str).encode()).hexdigest()
    seal = hashlib.sha256((head + digest + decision + officer).encode()).hexdigest()
    s.approval = {"decision": decision, "by": officer, "comment": (comment or "").strip(), "at": now_iso(),
                  "winner": win["bidder"] if (win and decision == "APPROVED") else None,
                  "ranking_digest": digest, "seal": seal}
    s.report_stale = True
    s.add_audit("HumanCommittee", "final_decision", {k: v for k, v in s.approval.items()})
    s.set_stage("approval", "done" if decision == "APPROVED" else "error",
                f"{'Approved' if decision == 'APPROVED' else 'Rejected'} by {officer}")
    store.save(s)
    return s.to_public()


def regenerate_report(s):
    _need_complete(s)
    llm = LLM(s.mode, s.settings["model"], s.settings["reasoning_effort"], on_event=s.add_audit)
    s.report_md = report.run(llm, s)
    s.report_stale = False
    s.add_audit("Report", "report_regenerated", {"chars": len(s.report_md)})
    store.save(s)
    return s.to_public()

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


def draft_clarification(s, bidder: str, criterion_id: str, officer: str, llm_mode: str, model: str, effort: str):
    """LLM drafts a formal clarification question for an UNCLEAR criterion."""
    from .agents.clarification import draft_question
    _need_complete(s)
    if s.approval:
        raise ActionError("Evaluation already signed off.", 409)
    comp = s.compliance.get(bidder)
    if not comp:
        raise ActionError(f"Bidder '{bidder}' not found.", 404)
    check = next((c for c in comp["checks"] if c["id"] == criterion_id), None)
    if not check:
        raise ActionError(f"Criterion '{criterion_id}' not found for bidder '{bidder}'.", 404)
    if check["status"] != "UNCLEAR":
        raise ActionError(f"Criterion {criterion_id} is {check['status']}, not UNCLEAR — clarification only applies to UNCLEAR criteria.")
    officer = (officer or "").strip() or "Evaluation Officer"
    llm = LLM(llm_mode or s.mode, model or s.settings["model"], effort or s.settings["reasoning_effort"], on_event=s.add_audit)
    result = draft_question(llm, {"id": criterion_id, "criterion": check["criterion"], "evidence_required": ""}, bidder, check.get("evidence_quote", ""))
    key = f"{bidder}:{criterion_id}"
    with s.lock:
        s.clarifications[key] = {
            "bidder": bidder,
            "criterion_id": criterion_id,
            "criterion": check["criterion"],
            "question": result["question"],
            "what_is_needed": result["what_is_needed"],
            "drafted_at": now_iso(),
            "officer": officer,
            "vendor_reply": None,
            "reply_at": None,
            "rescore": None,
        }
    s.human_actions.append({"type": "clarification_drafted", "target": f"compliance:{bidder}:{criterion_id}", "by": officer, "note": result["question"][:200], "at": now_iso()})
    s.add_audit("ClarificationAgent", "question_drafted", {"bidder": bidder, "criterion_id": criterion_id, "question": result["question"], "by": officer})
    store.save(s)
    return s.to_public()


def submit_clarification_reply(s, bidder: str, criterion_id: str, vendor_reply: str, officer: str, llm_mode: str, model: str, effort: str):
    """Accept vendor reply, re-score the criterion, update compliance verdict."""
    from .agents.clarification import rescore_criterion
    from .agents import scoring as _scoring
    _need_complete(s)
    if s.approval:
        raise ActionError("Evaluation already signed off.", 409)
    if not vendor_reply or not vendor_reply.strip():
        raise ActionError("vendor_reply cannot be empty.")
    key = f"{bidder}:{criterion_id}"
    clar = s.clarifications.get(key)
    if not clar:
        raise ActionError(f"No clarification was drafted for {bidder}:{criterion_id}. Draft it first.", 404)
    comp = s.compliance.get(bidder)
    if not comp:
        raise ActionError(f"Bidder '{bidder}' not found.", 404)
    check = next((c for c in comp["checks"] if c["id"] == criterion_id), None)
    if not check:
        raise ActionError(f"Criterion '{criterion_id}' not found.", 404)
    officer = (officer or "").strip() or "Evaluation Officer"
    # Get original bid text
    bid_text = (s.bids.get(bidder) or {}).get("text", "")
    llm = LLM(llm_mode or s.mode, model or s.settings["model"], effort or s.settings["reasoning_effort"], on_event=s.add_audit)
    criterion_obj = {"id": criterion_id, "criterion": check["criterion"], "evidence_required": ""}
    new_check = rescore_criterion(llm, criterion_obj, bidder, check.get("evidence_quote", ""), vendor_reply, bid_text)
    with s.lock:
        # Update the clarification record
        clar["vendor_reply"] = vendor_reply.strip()
        clar["reply_at"] = now_iso()
        clar["rescore"] = new_check
        clar["officer"] = officer
        # Update the compliance check in-place
        for i, c in enumerate(comp["checks"]):
            if c["id"] == criterion_id:
                comp["checks"][i] = new_check
                break
        # Recalculate verdict
        checks = comp["checks"]
        if any(c["status"] == "FAIL" for c in checks):
            comp["verdict"] = "DISQUALIFIED"
        elif any(c["status"] == "UNCLEAR" for c in checks):
            comp["verdict"] = "NEEDS_HUMAN_REVIEW"
        else:
            comp["verdict"] = "ELIGIBLE"
        # Re-rank
        _rerank(s)
    s.human_actions.append({"type": "clarification_reply_submitted", "target": f"compliance:{bidder}:{criterion_id}", "by": officer, "note": f"Re-scored to {new_check['status']}", "at": now_iso()})
    s.add_audit("ClarificationAgent", "criterion_rescored", {"bidder": bidder, "criterion_id": criterion_id, "new_status": new_check["status"], "by": officer})
    store.save(s)
    return s.to_public()

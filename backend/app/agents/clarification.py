"""Clarification Agent: drafts questions for UNCLEAR criteria and re-scores after vendor reply."""
import json
from ..documents import verify_quote

DRAFT_SYSTEM = (
    "You are the Procurement Clarification Agent. "
    "A mandatory eligibility criterion is UNCLEAR in a bidder's submission. "
    "Draft a precise, formal clarification question to send to the vendor. "
    "Specify exactly what document/evidence is missing, the tender clause it relates to, "
    "and what format the reply should take. "
    'Return JSON: {"question": "formal clarification question text", '
    '"criterion_id": "E1", "what_is_needed": "short phrase"}'
)

RESCORE_SYSTEM = (
    "You are the Procurement Compliance Agent. "
    "Re-evaluate a single eligibility criterion after the vendor has provided a clarification reply. "
    "Decide PASS, FAIL, or UNCLEAR based on the original bid text AND the vendor reply. "
    "Be strict: PASS only if the combined evidence explicitly satisfies the criterion. "
    'Return JSON: {"id": "E1", "status": "PASS|FAIL|UNCLEAR", '
    '"extracted_value": "short value", "evidence_quote": "short exact quote", "reason": "one sentence"}'
)


def draft_question(llm, criterion: dict, bidder: str, current_evidence: str) -> dict:
    """Draft a formal clarification question for an UNCLEAR criterion."""
    payload = {
        "bidder": bidder,
        "criterion_id": criterion["id"],
        "criterion": criterion["criterion"],
        "evidence_required": criterion.get("evidence_required", ""),
        "current_evidence_found": current_evidence,
    }
    out = llm.json("ClarificationAgent", DRAFT_SYSTEM, json.dumps(payload, indent=1))
    return {
        "question": out.get("question", f"Please provide evidence for criterion {criterion['id']}: {criterion['criterion']}"),
        "criterion_id": out.get("criterion_id", criterion["id"]),
        "what_is_needed": out.get("what_is_needed", criterion.get("evidence_required", "")),
    }


def rescore_criterion(llm, criterion: dict, bidder: str, original_text: str, vendor_reply: str, bid_text: str) -> dict:
    """Re-evaluate a single criterion after vendor reply; returns updated check dict."""
    from ..documents import Retriever, verify_quote
    retr = Retriever(bid_text + "\n\n## Vendor Clarification Reply\n" + vendor_reply)
    evidence = retr.search(criterion["criterion"] + " " + criterion.get("evidence_required", ""), k=4)
    payload = {
        "criterion": criterion,
        "original_bid_evidence": original_text,
        "vendor_reply": vendor_reply,
        "retrieved_combined_evidence": evidence,
    }
    out = llm.json("ClarificationAgent", RESCORE_SYSTEM, json.dumps(payload, indent=1))
    st = str(out.get("status", "UNCLEAR")).upper()
    quote = str(out.get("evidence_quote", "") or "")
    return {
        "id": criterion["id"],
        "criterion": criterion["criterion"],
        "status": st if st in ("PASS", "FAIL", "UNCLEAR") else "UNCLEAR",
        "reason": str(out.get("reason") or "Re-scored after vendor clarification"),
        "extracted_value": str(out.get("extracted_value") or ""),
        "evidence_quote": quote,
        "quote_verified": verify_quote(quote, bid_text + "\n" + vendor_reply),
        "rescored_after_clarification": True,
    }

"""Agent 2 - Compliance: pass/fail on every mandatory criterion with quoted, verified evidence."""
import json

from ..documents import Retriever, verify_quote

SYSTEM = (
    "You are the Compliance Agent. For EACH eligibility criterion decide PASS, FAIL or UNCLEAR using only the retrieved bid evidence. "
    "Be strict: PASS only if the evidence explicitly satisfies the criterion (check numbers, dates, validity, and that documents are enclosed). "
    "FAIL if the evidence shows the requirement is not met or the document is missing. UNCLEAR if the evidence is insufficient. "
    'Return JSON: {"results": [{"id": "E1", "status": "PASS|FAIL|UNCLEAR", "extracted_value": "very short value, e.g. INR 7.3 Cr avg", '
    '"evidence_quote": "short exact quote from the bid", "reason": "one sentence"}]}'
)


def run(llm, rubric: dict, bidder: str, text: str) -> dict:
    retr = Retriever(text)
    evidence = {c["id"]: retr.search(c["criterion"] + " " + c["evidence_required"], k=4) for c in rubric["eligibility"]}
    payload = {"criteria": rubric["eligibility"], "retrieved_evidence": evidence}
    out = llm.json("Compliance", SYSTEM, json.dumps(payload, indent=1))
    got = {r.get("id"): r for r in out.get("results", [])}
    checks = []
    for c in rubric["eligibility"]:
        r = dict(got.get(c["id"], {}))
        st = str(r.get("status", "UNCLEAR")).upper()
        quote = str(r.get("evidence_quote", "") or "")
        checks.append({
            "id": c["id"], "criterion": c["criterion"],
            "status": st if st in ("PASS", "FAIL", "UNCLEAR") else "UNCLEAR",
            "reason": str(r.get("reason") or "No verdict returned"),
            "extracted_value": str(r.get("extracted_value") or ""),
            "evidence_quote": quote,
            "quote_verified": verify_quote(quote, text),
        })
    if any(c["status"] == "FAIL" for c in checks):
        verdict = "DISQUALIFIED"
    elif any(c["status"] == "UNCLEAR" for c in checks):
        verdict = "NEEDS_HUMAN_REVIEW"
    else:
        verdict = "ELIGIBLE"
    return {"bidder": bidder, "verdict": verdict, "checks": checks}

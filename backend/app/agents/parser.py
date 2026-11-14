"""Agent 1 - Tender Parser: tender document -> structured rubric."""
from ..documents import to_num

SYSTEM = (
    "You are the Tender Parser Agent of a public procurement evaluation committee. "
    "Extract the evaluation rubric from the tender document. Return JSON with this schema: "
    '{"tender_id": str, "title": str, "issuer": str, '
    '"eligibility": [{"id": "E1", "criterion": str, "evidence_required": str}], '
    '"technical": [{"id": "T1", "criterion": str, "weight": number}], '
    '"min_technical_score": number, '
    '"weights": {"technical": number, "financial": number}, "financial_method": str}. '
    "Keep the ids used in the tender (E1.., T1..) and extract every criterion."
)


def run(llm, tender_text: str) -> dict:
    rubric = llm.json("TenderParser", SYSTEM, tender_text[:20000])
    elig = [{"id": str(c.get("id", f"E{i}")), "criterion": str(c.get("criterion", "")),
             "evidence_required": str(c.get("evidence_required", ""))} for i, c in enumerate(rubric.get("eligibility", []), 1)]
    tech = [{"id": str(c.get("id", f"T{i}")), "criterion": str(c.get("criterion", "")),
             "weight": to_num(c.get("weight", 0))} for i, c in enumerate(rubric.get("technical", []), 1)]
    if not elig or not tech:
        raise ValueError("Tender parser found no eligibility or technical criteria - check the tender document.")
    tw = sum(c["weight"] for c in tech) or 100.0
    for c in tech:                       # normalise technical weights to a 100-mark scale
        c["weight"] = round(c["weight"] * 100.0 / tw, 2)
    w = rubric.get("weights") or {"technical": 70, "financial": 30}
    wt, wf = to_num(w.get("technical", 70)), to_num(w.get("financial", 30))
    total = (wt + wf) or 100.0
    return {
        "tender_id": rubric.get("tender_id") or "UNKNOWN",
        "title": rubric.get("title") or "Untitled tender",
        "issuer": rubric.get("issuer") or "",
        "eligibility": elig,
        "technical": tech,
        "min_technical_score": to_num(rubric.get("min_technical_score", 60)),
        "weights": {"technical": wt / total, "financial": wf / total},
        "financial_method": rubric.get("financial_method") or "QCBS",
    }

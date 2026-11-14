"""Agent 7 - Report Agent: writes the evaluation report from the recorded results (no new facts)."""
import json

SYSTEM = (
    "You are the Report Agent. Write a formal, concise Bid Evaluation Report in Markdown for a government audit file. "
    "Sections: 1 Executive Summary, 2 Eligibility Evaluation, 3 Technical Evaluation, 4 Financial Evaluation, "
    "5 Risk Findings and Chair Decisions, 6 Final Ranking (table), 7 Recommendation and Items Requiring Human Attention. "
    "Use ONLY the numbers and facts in the provided JSON; do not invent anything. Keep exact figures in tables."
)


def build_summary(s) -> dict:
    """Compact, factual digest of a finished session - the only thing the Report Agent sees."""
    return {
        "tender": {"id": s.rubric["tender_id"], "title": s.rubric["title"], "method": s.rubric["financial_method"],
                   "weights": s.rubric["weights"], "min_technical_score": s.rubric["min_technical_score"]},
        "eligibility": {n: {"verdict": c["verdict"],
                            "non_passing": [{"id": k["id"], "status": k["status"], "reason": k["reason"]}
                                            for k in c["checks"] if k["status"] != "PASS"]}
                        for n, c in s.compliance.items()},
        "technical": {n: {"raw_score": t["raw_score"],
                          "criteria": [{"id": x["id"], "score": x["score"], "justification": x["justification"]} for x in t["scores"]]}
                      for n, t in s.technical.items()},
        "financial": {n: {"stated_total": f["stated_total"], "recomputed_total": f["recomputed_total"], "issues": f["flags"]}
                      for n, f in s.financial.items()},
        "risk_flags": [{k: v for k, v in f.items() if k not in ("diff", "longest_shared_passage")} for f in s.risk_flags],
        "chair_decisions": [{"type": d["flag_type"], "bidders": d["bidders"], "actions": d["actions"],
                             "rationale": d["rationale"], "human_resolution": d.get("human", {})} for d in s.decisions],
        "final_ranking": s.ranking,
        "human_approval": (s.approval or {}).get("decision"),
    }


def run(llm, s) -> str:
    return llm.text("Report", SYSTEM, json.dumps(build_summary(s), indent=1, default=str))

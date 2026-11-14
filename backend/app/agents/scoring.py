"""QCBS scoring + ranking. Pure deterministic Python - no LLM touches a number here."""
from .chair import ACTIONS, SEVERITY

PENALTY = {"PENALIZE_10": 0.10, "PENALIZE_25": 0.25}

STATUS_LABELS = {
    "QUALIFIED": "Qualified",
    "DISQUALIFIED_ELIGIBILITY": "Disqualified (eligibility)",
    "DISQUALIFIED_COMMITTEE": "Disqualified (committee concurred)",
    "PENDING_DISQUALIFICATION": "Recommended for disqualification - needs committee decision",
    "TECH_NOT_QUALIFIED": "Technically not qualified",
}


def effective_action(decision: dict, bidder: str):
    """(action, resolved_by_human) after applying any human concur / override."""
    ai = decision["actions"].get(bidder, "NO_ACTION")
    h = (decision.get("human") or {}).get(bidder)
    if not h:
        return ai, False
    if h["decision"] == "override" and h.get("action") in ACTIONS:
        return h["action"], True
    return ai, True


def worst_actions(decisions):
    """bidder -> (action, resolved). The most severe action wins; resolved only if every serious one was."""
    worst = {}
    for d in decisions:
        for b in d["bidders"]:
            a, resolved = effective_action(d, b)
            cur = worst.get(b)
            if cur is None or SEVERITY[a] > SEVERITY[cur[0]]:
                worst[b] = (a, resolved)
    return worst


def blockers(decisions):
    """Bidders whose recommended disqualification still awaits a human decision (blocks final approval)."""
    out = []
    for d in decisions:
        for b in d["bidders"]:
            a, resolved = effective_action(d, b)
            if a == "RECOMMEND_DISQUALIFY" and not resolved:
                out.append(b)
    return sorted(set(out))


def run(rubric, compliance, tech, fin, decisions) -> list:
    worst = worst_actions(decisions)
    rows = []
    for b in compliance:
        act, resolved = worst.get(b, ("NO_ACTION", True))
        r = {"rank": None, "bidder": b, "eligibility": compliance[b]["verdict"],
             "chair_action": act if b in worst else None, "chair_resolved": resolved,
             "tech_raw": None, "penalty": 0.0, "tech_adj": None, "price": None,
             "fin_score": None, "final_score": None, "status": ""}
        if compliance[b]["verdict"] == "DISQUALIFIED":
            r["status"] = "DISQUALIFIED_ELIGIBILITY"
        else:
            raw = tech[b]["raw_score"]
            pen = PENALTY.get(act, 0.0)
            r.update({"tech_raw": raw, "penalty": pen, "tech_adj": round(raw * (1 - pen), 2),
                      "price": fin[b]["recomputed_total"] if b in fin else None})
            if act == "RECOMMEND_DISQUALIFY":
                r["status"] = "DISQUALIFIED_COMMITTEE" if resolved else "PENDING_DISQUALIFICATION"
            elif r["tech_adj"] < rubric["min_technical_score"]:
                r["status"] = "TECH_NOT_QUALIFIED"
            else:
                r["status"] = "QUALIFIED"
        rows.append(r)

    qualified = [r for r in rows if r["status"] == "QUALIFIED" and r["price"]]
    for r in rows:
        if r["status"] == "QUALIFIED" and not r["price"]:
            r["status"] = "TECH_NOT_QUALIFIED"       # no readable financial bid -> cannot be ranked
    if qualified:
        l1 = min(r["price"] for r in qualified)
        wt, wf = rubric["weights"]["technical"], rubric["weights"]["financial"]
        for r in qualified:
            r["fin_score"] = round(l1 / r["price"] * 100, 2)
            r["final_score"] = round(wt * r["tech_adj"] + wf * r["fin_score"], 2)
        qualified.sort(key=lambda r: r["final_score"], reverse=True)
        for i, r in enumerate(qualified, 1):
            r["rank"] = i
    others = [r for r in rows if r["status"] != "QUALIFIED"]
    order = {"PENDING_DISQUALIFICATION": 0, "TECH_NOT_QUALIFIED": 1, "DISQUALIFIED_COMMITTEE": 2, "DISQUALIFIED_ELIGIBILITY": 3}
    others.sort(key=lambda r: order.get(r["status"], 9))
    for r in rows:
        r["status_label"] = STATUS_LABELS[r["status"]]
    return qualified + others

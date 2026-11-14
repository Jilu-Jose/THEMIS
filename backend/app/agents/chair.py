"""Agent 6 - Chair: turns risk flags into bounded actions. Humans can concur or override each one."""
import json

ACTIONS = ["NO_ACTION", "REQUEST_CLARIFICATION", "PENALIZE_10", "PENALIZE_25", "RECOMMEND_DISQUALIFY"]
SEVERITY = {a: i for i, a in enumerate(ACTIONS)}

SYSTEM = (
    "You are the Chair of the evaluation committee. A risk flag has been raised. Decide ONE action per bidder from exactly this list: "
    f"{ACTIONS}. Guidance: for copied text, the bid submitted LATER and containing claims inconsistent with its own documents is the likely copier "
    "(RECOMMEND_DISQUALIFY); the earlier original bidder should get NO_ACTION. For an abnormally low price use REQUEST_CLARIFICATION or a penalty unless there is other evidence of fraud. "
    'Return JSON: {"actions": {"<bidder name>": "<ACTION>"}, "rationale": "two or three sentences citing the evidence"}'
)


def _trim(flag):
    keep = {k: v for k, v in flag.items() if k not in ("diff", "longest_shared_passage")}
    return keep


def run(llm, flags, compliance, tech) -> list:
    decisions = []
    for idx, f in enumerate(flags):
        if f["type"] == "ARITHMETIC":
            decisions.append({
                "index": idx, "flag_type": f["type"], "bidders": f["bidders"],
                "actions": {f["bidders"][0]: "NO_ACTION"},
                "rationale": "Tender policy: arithmetical errors are corrected by recomputing from unit prices; the recomputed total is used for scoring.",
                "human": {},
            })
            continue
        ctx = {"flag": _trim(f), "bidder_context": {
            b: {"eligibility": compliance[b]["verdict"], "technical_score": tech[b]["raw_score"] if b in tech else None}
            for b in f["bidders"]}}
        out = llm.json("Chair", SYSTEM, json.dumps(ctx, indent=1))
        acts = {}
        for b in f["bidders"]:
            a = (out.get("actions") or {}).get(b, "REQUEST_CLARIFICATION")
            acts[b] = a if a in ACTIONS else "REQUEST_CLARIFICATION"
        decisions.append({"index": idx, "flag_type": f["type"], "bidders": f["bidders"], "actions": acts,
                          "rationale": out.get("rationale", ""), "human": {}})
    return decisions

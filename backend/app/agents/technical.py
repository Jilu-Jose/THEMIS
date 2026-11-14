"""Agent 3 - Technical Evaluator: anonymised, evidence-cited scoring against the rubric."""
import json
import re

from ..documents import Retriever, to_num, verify_quote

SYSTEM = (
    "You are the Technical Evaluator. Score the anonymised bid against each technical criterion from 0 to 10 using ONLY the retrieved evidence. "
    "Scale: 0-2 absent or irrelevant; 3-5 generic or vague; 6-8 specific and credible; 9-10 excellent with measurable details. "
    "Do not reward length or marketing language; reward specifics, numbers, and feasibility. "
    'Return JSON: {"scores": [{"id": "T1", "score": number, "justification": "one or two sentences", "evidence_quote": "short exact quote"}]}'
)


def make_aliases(bidders):
    return {b: f"Bidder-{chr(65 + i)}" for i, b in enumerate(bidders)}


def anonymize(text: str, name: str, alias: str) -> str:
    for token in {name, name.split()[0]}:
        text = re.sub(re.escape(token), alias, text, flags=re.I)
    return text


def run(llm, rubric: dict, bidder: str, alias: str, text: str, blind: bool = True) -> dict:
    visible = anonymize(text, bidder, alias) if blind else text
    retr = Retriever(visible)
    evidence = {c["id"]: retr.search(c["criterion"], k=3) for c in rubric["technical"]}
    payload = {"bidder": alias if blind else bidder, "criteria": rubric["technical"], "retrieved_evidence": evidence}
    out = llm.json("Technical", SYSTEM, json.dumps(payload, indent=1))
    got = {s.get("id"): s for s in out.get("scores", [])}
    scores, raw = [], 0.0
    for c in rubric["technical"]:
        s = got.get(c["id"], {})
        sc = max(0.0, min(10.0, to_num(s.get("score", 0))))
        quote = str(s.get("evidence_quote", "") or "")
        weighted = round(sc / 10.0 * c["weight"], 2)
        raw += weighted
        scores.append({
            "id": c["id"], "criterion": c["criterion"], "weight": c["weight"], "score": sc, "weighted": weighted,
            "justification": str(s.get("justification") or "No score returned"),
            "evidence_quote": quote, "quote_verified": verify_quote(quote, visible),
            "evidence_chunks": evidence[c["id"]][:2],
        })
    return {"bidder": bidder, "alias": alias, "blind": blind, "scores": scores, "raw_score": round(raw, 2)}

"""Agent 4 - Financial Evaluator: LLM extracts the price schedule, Python re-computes every number."""
from ..documents import inr, section_or_all, to_num

SYSTEM = (
    "You are the Financial Evaluator. Extract the price schedule from the bid. Use plain numbers in INR without commas or symbols. "
    'Return JSON: {"line_items": [{"item": str, "qty": number, "unit_price": number, "amount": number}], "stated_total": number}'
)


def run(llm, bidder: str, text: str) -> dict:
    fin = section_or_all(text, "Financial Bid", None)
    out = llm.json("Financial", SYSTEM, fin)
    items, flags, recomputed = [], [], 0.0
    for it in out.get("line_items", []):
        q, u, a = to_num(it.get("qty")), to_num(it.get("unit_price")), to_num(it.get("amount"))
        if abs(q * u - a) > 1:
            flags.append(f"Line '{it.get('item')}': qty x unit price = {inr(q * u)} but amount stated {inr(a)}")
        recomputed += q * u
        items.append({"item": it.get("item"), "qty": q, "unit_price": u, "amount": a, "recomputed": q * u})
    stated = to_num(out.get("stated_total"))
    if not items:
        flags.append("No priced line items could be extracted - manual review required.")
    elif abs(recomputed - stated) > 1:
        flags.append(f"Stated total INR {inr(stated)} differs from recomputed INR {inr(recomputed)}")
    return {"bidder": bidder, "line_items": items, "stated_total": stated, "recomputed_total": recomputed, "flags": flags}

"""Agent 5 - Risk / Fraud: copied text between bids, abnormal prices, arithmetic errors, inconsistent claims."""
import difflib
import json
import re
import statistics

from ..documents import section_or_all

SYSTEM = (
    "You are the Risk Agent. Two bids share near-identical technical text. Using each bidder's own eligibility documents, "
    "check whether the shared text makes claims (projects, clients, experience) that are inconsistent with a bidder's own documents. "
    'Return JSON: {"inconsistencies": [str], "assessment": "two sentences"}'
)


def _norm(w):
    return re.sub(r"\W+", "", w.lower())


def shingles(text, k=5):
    w = re.findall(r"\w+", text.lower())
    return {" ".join(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


def longest_shared(a, b, max_words=40):
    wa, wb = a.split(), b.split()
    m = difflib.SequenceMatcher(None, wa, wb, autojunk=False).find_longest_match(0, len(wa), 0, len(wb))
    return " ".join(wa[m.a:m.a + m.size][:max_words])


def shared_segments(a_text, b_text, k=5, cap=900):
    """Split each text into [{text, shared}] runs so the UI can highlight copied passages side by side."""
    clean = lambda t: re.sub(r"^#+\s*", "", t, flags=re.M)       # hide markdown heading markers in the display
    wa, wb = clean(a_text).split()[:cap], clean(b_text).split()[:cap]
    na, nb = [_norm(w) for w in wa], [_norm(w) for w in wb]
    grams = lambda n: {tuple(n[i:i + k]) for i in range(len(n) - k + 1)}
    common = grams(na) & grams(nb)

    def mark(words, n):
        flags = [False] * len(n)
        for i in range(len(n) - k + 1):
            if tuple(n[i:i + k]) in common:
                for j in range(i, i + k):
                    flags[j] = True
        segs = []
        for w, f in zip(words, flags):
            if segs and segs[-1]["shared"] == f:
                segs[-1]["text"] += " " + w
            else:
                segs.append({"text": w, "shared": f})
        return segs, sum(flags)

    sa, ca = mark(wa, na)
    sb, cb = mark(wb, nb)
    return {"a": sa, "b": sb, "shared_words_a": ca, "shared_words_b": cb, "words_a": len(wa), "words_b": len(wb)}


def run(llm, bids: dict, names: list, fin_results: dict, settings: dict) -> list:
    flags = []
    techs = {n: section_or_all(bids[n]["text"], "Technical Proposal", "Financial Bid") for n in names}
    elig = {n: section_or_all(bids[n]["text"], "Eligibility Documents", "Technical Proposal", 4000) for n in names}

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sim = jaccard(shingles(techs[a]), shingles(techs[b]))
            if sim < settings["similarity_threshold"]:
                continue
            passage = longest_shared(techs[a], techs[b])
            payload = {
                "shared_passage_sample": passage,
                "bidder_A": {"name": a, "eligibility_documents": elig[a]},
                "bidder_B": {"name": b, "eligibility_documents": elig[b]},
                "technical_text_A": techs[a][:2500], "technical_text_B": techs[b][:2500],
            }
            review = llm.json("Risk", SYSTEM, json.dumps(payload, indent=1))
            flags.append({
                "type": "SIMILARITY", "severity": "HIGH", "bidders": [a, b], "similarity": round(sim, 2),
                "longest_shared_passage": passage,
                "submitted_at": {a: bids[a]["submitted_at"], b: bids[b]["submitted_at"]},
                "llm_review": {"inconsistencies": review.get("inconsistencies", []), "assessment": review.get("assessment", "")},
                "diff": shared_segments(techs[a], techs[b]),
            })

    totals = {n: fin_results[n]["recomputed_total"] for n in names if n in fin_results and fin_results[n]["recomputed_total"] > 0}
    if len(totals) >= 3:                       # a median over <3 bids says nothing about outliers
        med = statistics.median(totals.values())
        for n, t in totals.items():
            ratio = t / med if med else 1.0
            if ratio < settings["low_price_ratio"] or ratio > settings["high_price_ratio"]:
                flags.append({"type": "PRICE_OUTLIER", "severity": "MEDIUM", "bidders": [n], "price": t, "median": med,
                              "ratio_to_median": round(ratio, 2), "direction": "LOW" if ratio < 1 else "HIGH"})

    for n in names:
        for f in fin_results.get(n, {}).get("flags", []):
            flags.append({"type": "ARITHMETIC", "severity": "LOW", "bidders": [n], "detail": f})
    return flags

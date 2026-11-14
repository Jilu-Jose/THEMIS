"""Offline rule-based stand-in for the LLM (demo mode).

It is NOT an LLM: it applies regex / counting heuristics to the same payloads the real agents send to
Groq, so the whole app can be demonstrated and tested without an API key. Set GROQ_API_KEY to use gpt-oss.
"""
import datetime
import json
import re


# ============================================================ helpers
def _blob(chunks):
    return " ".join(re.sub(r"^\[[^\]]*\]\s*", "", c) for c in chunks)


def _sentence_with(text: str, pattern: str, limit: int = 200) -> str:
    """Return an exact substring of `text` (one sentence) matching `pattern` – keeps quotes verifiable."""
    for s in re.split(r"(?<=[.;])\s+|\n", text):
        if re.search(pattern, s, re.I) and len(s.strip()) > 8:
            return s.strip()[:limit]
    return ""


def _fmt_cr(x: float) -> str:
    return f"₹{x:.1f} Cr"


# ============================================================ dispatch
def mock_json(agent: str, system: str, user: str) -> dict:
    return {
        "TenderParser": _parser,
        "Compliance": _compliance,
        "Technical": _technical,
        "Financial": _financial,
        "Risk": _risk,
        "Chair": _chair,
    }[agent](user)


def mock_text(agent: str, system: str, user: str) -> str:
    if agent == "Report":
        return _report(json.loads(user))
    return ""


# ============================================================ 1. tender parser
def _parser(text: str) -> dict:
    g = lambda p: (re.search(p, text, re.I | re.M) or [None, ""])[1].strip()
    eligibility, technical = [], []
    for m in re.finditer(r"^(E\d+)\.\s*(.+)$", text, re.M):
        body = m.group(2)
        crit, _, ev = body.partition("Evidence:")
        eligibility.append({"id": m.group(1), "criterion": crit.strip(), "evidence_required": ev.strip().rstrip(".")})
    for m in re.finditer(r"^(T\d+)\.\s*(.+?)\s*[-–]\s*(\d+)\s*marks", text, re.M | re.I):
        technical.append({"id": m.group(1), "criterion": m.group(2).strip(), "weight": float(m.group(3))})
    w = re.search(r"Technical\s*(\d+)\s*,?\s*Financial\s*(\d+)", text, re.I)
    method = g(r"^##\s*\d*\.?\s*Selection Method\s*\n+(.+)")
    return {
        "tender_id": g(r"Tender No:\s*(.+)"),
        "title": g(r"Title:\s*(.+)"),
        "issuer": g(r"Issued by:\s*(.+)"),
        "eligibility": eligibility,
        "technical": technical,
        "min_technical_score": float(g(r"Minimum technical qualifying score:\s*(\d+)") or 60),
        "weights": {"technical": float(w.group(1)) if w else 70, "financial": float(w.group(2)) if w else 30},
        "financial_method": (method.split(".")[0] + ".") if method else "QCBS",
    }


# ============================================================ 2. compliance
def _compliance(user: str) -> dict:
    p = json.loads(user)
    all_ev = _blob(list(dict.fromkeys(c for v in p["retrieved_evidence"].values() for c in v)))   # de-duplicated chunks
    now = datetime.date.today().year
    results = []
    for c in p["criteria"]:
        ct = c["criterion"].lower()
        ev = _blob(p["retrieved_evidence"].get(c["id"], [])) or all_ev
        st, reason, value, quote = "UNCLEAR", "Insufficient evidence retrieved.", "", ""

        if "registered" in ct and "year" in ct:
            need = int((re.search(r"(\d+)\s*years", ct) or [0, 5])[1])
            m = re.search(r"incorporated in (\d{4})", all_ev, re.I)
            if m:
                age = now - int(m.group(1))
                st = "PASS" if age >= need else "FAIL"
                reason = f"Incorporated in {m.group(1)} ({age} years); {need} required."
                value, quote = f"Inc. {m.group(1)} · {age} yrs", _sentence_with(all_ev, r"incorporated in")
        elif "turnover" in ct:
            need = float((re.search(r"INR\s*([\d.]+)\s*crore", c["criterion"], re.I) or [0, 5])[1])
            vals = [float(x) for x in re.findall(r"FY[\d\-]+\s*INR\s*([\d.]+)\s*crore", all_ev, re.I)]
            if vals:
                avg = sum(vals) / len(vals)
                st = "PASS" if avg >= need else "FAIL"
                reason = f"Average turnover over {len(vals)} years is INR {avg:.2f} crore against INR {need:g} crore required."
                value, quote = f"{_fmt_cr(avg)} avg", _sentence_with(all_ev, r"turnover statement")
        elif "project" in ct:
            n = int((re.search(r"at least (\d+)", ct) or [0, 2])[1])
            minv = float((re.search(r"INR\s*([\d.]+)\s*crore or more", c["criterion"], re.I) or [0, 1])[1])
            projs = re.findall(r"\(\d+\)\s*([^;]+?)INR\s*([\d.]+)\s*crore,\s*completed\s*(\d{4})", all_ev, re.I)
            good = [x for x in projs if float(x[1]) >= minv and now - int(x[2]) <= 5]
            st = "PASS" if len(good) >= n else "FAIL"
            reason = f"{len(good)} qualifying project(s) found (value ≥ INR {minv:g} crore, completed within 5 years); {n} required."
            value, quote = f"{len(good)} projects", _sentence_with(all_ev, r"similar completed projects")
        elif "gst" in ct or "pan" in ct:
            ok = "gst" in all_ev.lower() and "pan" in all_ev.lower() and re.search(r"valid|attached", all_ev, re.I)
            st = "PASS" if ok else "FAIL"
            reason = "GST registration and PAN copies are stated as attached and valid." if ok else "GST / PAN not evidenced."
            value, quote = "GST + PAN", _sentence_with(all_ev, r"GST")
        elif "iso" in ct:
            if re.search(r"not enclosed|in progress|not attached|expired", all_ev, re.I):
                st, reason, value = "FAIL", "ISO 9001 certificate is not enclosed (renewal in progress).", "Certificate missing"
                quote = _sentence_with(all_ev, r"ISO")
            elif re.search(r"ISO 9001", all_ev, re.I) and re.search(r"attached|valid till", all_ev, re.I):
                v = re.search(r"valid till ([A-Za-z]+ \d{4})", all_ev)
                st, reason = "PASS", "Valid ISO 9001 certificate is enclosed."
                value, quote = ("Valid till " + v.group(1)) if v else "ISO 9001", _sentence_with(all_ev, r"ISO")
        elif "earnest" in ct or "emd" in ct:
            need = int(re.sub(r"[^\d]", "", (re.search(r"INR\s*([\d,]+)", c["criterion"]) or [0, "200000"])[1]) or 0)
            m = re.search(r"EMD of INR ([\d,]+) submitted via ([\w\- ]+?) ([A-Z]{2}-\d+)", all_ev)
            if m:
                amt = int(m.group(1).replace(",", ""))
                st = "PASS" if amt >= need else "FAIL"
                reason = f"EMD of INR {m.group(1)} submitted via {m.group(2)} {m.group(3)}."
                value, quote = m.group(3), _sentence_with(all_ev, r"EMD of")
        elif "blacklist" in ct or "debar" in ct:
            if re.search(r"has not been blacklisted|not been debarred|not blacklisted", all_ev, re.I):
                st, reason, value = "PASS", "Self-declaration of no blacklisting / debarment is present.", "Declaration signed"
                quote = _sentence_with(all_ev, r"blacklisted")

        results.append({"id": c["id"], "status": st, "reason": reason, "extracted_value": value, "evidence_quote": quote})
    return {"results": results}


# ============================================================ 3. technical
def _technical(user: str) -> dict:
    p = json.loads(user)
    scores = []
    for c in p["criteria"]:
        ev = _blob(p["retrieved_evidence"].get(c["id"], []))
        words = len(ev.split())
        nums = len(re.findall(r"\d+(?:\.\d+)?", ev))
        raw = 3.4 + min(nums, 12) * 0.34 + min(words / 60.0, 3.0) * 0.55
        s = round(min(raw, 9.0) * 2) / 2
        quote = _sentence_with(ev, r"\d") or ev[:140]
        scores.append({
            "id": c["id"], "score": s, "evidence_quote": quote[:200],
            "justification": f"Evidence contains {nums} concrete figures over ~{words} words; "
                             f"{'specific and measurable' if s >= 7 else 'moderately specific' if s >= 5 else 'generic with few measurable commitments'}.",
        })
    return {"scores": scores}


# ============================================================ 4. financial
def _financial(text: str) -> dict:
    items, total = [], 0.0
    for line in text.splitlines():
        if line.startswith("|") and "Item" not in line and not set(line) <= set("|-: "):
            cells = [x.strip() for x in line.strip("|").split("|")]
            try:
                nums = [float(re.sub(r"[^\d.]", "", x)) for x in cells[1:4]]
            except ValueError:
                continue
            items.append({"item": cells[0], "qty": nums[0], "unit_price": nums[1], "amount": nums[2]})
        m = re.search(r"Total[^:]*:\s*([\d,]+)", line)
        if m:
            total = float(m.group(1).replace(",", ""))
    return {"line_items": items, "stated_total": total}


# ============================================================ 5. risk review
def _risk(user: str) -> dict:
    p = json.loads(user)
    found = []
    for side, other in (("A", "B"), ("B", "A")):
        who = p[f"bidder_{side}"]
        own = who["eligibility_documents"]
        tech = p[f"technical_text_{side}"]
        names = set(re.findall(r"\b(?:[A-Z][a-z]{3,}|[A-Z]{3,})\b", tech))
        common = {"The", "This", "Data", "Each", "Team", "Sensors", "Implementation", "Support", "Training", "Technical",
                  "Approach", "Methodology", "Qualifications", "Experience", "Hardware", "Specifications", "Machine",
                  "Maintenance", "Plan", "Timeline", "Accuracy", "Delivery", "Dashboard", "Multi", "Rule"}
        for n in sorted(names - common):
            if re.search(rf"(delivered|completed|executed).{{0,60}}\b{n}\b", tech) and n.lower() not in own.lower():
                found.append(f"{who['name']}'s technical proposal claims work on '{n}', which is not among the projects listed in its own eligibility documents.")
    return {
        "inconsistencies": found,
        "assessment": ("The two proposals share long identical passages. "
                       + (f"{len(found)} claim(s) are inconsistent with the bidder's own documents, which is consistent with text reuse."
                          if found else "No claim inconsistent with the bidders' own documents was detected.")),
    }


# ============================================================ 6. chair
def _chair(user: str) -> dict:
    p = json.loads(user)
    f = p["flag"]
    if f["type"] == "SIMILARITY":
        sub = f["submitted_at"]
        later = max(f["bidders"], key=lambda b: sub[b])
        earlier = [b for b in f["bidders"] if b != later][0]
        inc = (f.get("llm_review") or {}).get("inconsistencies", [])
        bad = [b for b in f["bidders"] if any(b in x for x in inc)]
        target = bad[0] if bad else later
        return {
            "actions": {target: "RECOMMEND_DISQUALIFY", **{b: "NO_ACTION" for b in f["bidders"] if b != target}},
            "rationale": f"{int(round(f['similarity'] * 100))}% of the technical text is shared. {target} "
                         f"{'submitted later and ' if target == later else ''}has claims that its own documents do not support, "
                         f"so it is the likely copier; {earlier if target == later else later} appears to be the original author.",
        }
    if f["type"] == "PRICE_OUTLIER":
        b = f["bidders"][0]
        ratio = f["ratio_to_median"]
        act = "PENALIZE_10" if ratio < 0.5 else "REQUEST_CLARIFICATION"
        return {"actions": {b: act},
                "rationale": f"Price is {int(round(ratio * 100))}% of the median of qualified bids. "
                             f"{'Abnormally low pricing without other proof of fraud warrants a clarification or modest penalty.' }"}
    return {"actions": {b: "NO_ACTION" for b in f["bidders"]}, "rationale": "No action needed."}


# ============================================================ 7. report
def _report(s: dict) -> str:
    t = s["tender"]
    rank = s["final_ranking"]
    win = next((r for r in rank if r.get("rank") == 1), None)
    L = []
    L.append(f"# Bid Evaluation Report: {t['title']}\n")
    L.append(f"**Tender No:** {t['id']}  \n**Method:** {t['method']}  \n"
             f"**Weightage:** Technical {int(round(t['weights']['technical'] * 100))} / Financial {int(round(t['weights']['financial'] * 100))}  \n"
             f"**Minimum technical score:** {t['min_technical_score']:g}\n")
    L.append("## 1. Executive Summary\n")
    if win:
        L.append(f"The committee's AI recommendation is **{win['bidder']}** with a combined QCBS score of **{win['final_score']}**. "
                 f"{len(rank)} bids were evaluated; {sum(1 for r in rank if r['status'] == 'QUALIFIED')} qualified. "
                 "The recommendation is advisory and requires committee approval.\n")
    else:
        L.append("No bidder qualified for award on the current record.\n")
    L.append("## 2. Eligibility Evaluation\n")
    for n, e in s["eligibility"].items():
        L.append(f"- **{n}**: {e['verdict']}" + ("".join(f"\n  - {c['id']} {c['status']}: {c['reason']}" for c in e["non_passing"])))
    L.append("\n## 3. Technical Evaluation\n")
    L.append("| Bidder | Raw technical score /100 |\n|---|---|")
    for n, tt in s["technical"].items():
        L.append(f"| {n} | {tt['raw_score']} |")
    L.append("\n## 4. Financial Evaluation\n")
    L.append("| Bidder | Stated total (INR) | Recomputed total (INR) | Issues |\n|---|---|---|---|")
    for n, f in s["financial"].items():
        L.append(f"| {n} | {f['stated_total']:,.0f} | {f['recomputed_total']:,.0f} | {'; '.join(f['issues']) or '-'} |")
    L.append("\n## 5. Risk Findings and Chair Decisions\n")
    if not s["chair_decisions"]:
        L.append("No risk flags were raised.\n")
    for d in s["chair_decisions"]:
        res = d.get("human_resolution") or {}
        tail = (" Human resolution: " + "; ".join(f"{b} {h['decision']}" + (f" -> {h['action']}" if h.get('action') else "") for b, h in res.items()) + ".") if res else ""
        L.append(f"- **{d['type']}** ({', '.join(d['bidders'])}): {d['actions']}. {d['rationale']}{tail}")
    L.append("\n## 6. Final Ranking\n")
    L.append("| Rank | Bidder | Status | Technical (adj) | Price (INR) | Financial score | Final score |\n|---|---|---|---|---|---|---|")
    for r in rank:
        price = f"{r['price']:,.0f}" if r.get("price") else "-"
        L.append(f"| {r['rank'] or '-'} | {r['bidder']} | {r['status_label']} | {r.get('tech_adj') or '-'} | {price} | {r.get('fin_score') or '-'} | {r.get('final_score') or '-'} |")
    L.append("\n## 7. Recommendation and Items Requiring Human Attention\n")
    pend = [r for r in rank if r["status"] == "PENDING_DISQUALIFICATION"]
    L.append(f"- Human approval status: **{s['human_approval'] or 'pending'}**")
    for r in pend:
        L.append(f"- Committee must decide on the recommended disqualification of **{r['bidder']}**.")
    L.append("- All AI outputs are recommendations; the award rests with the Tender Evaluation Committee.")
    L.append("\n_Generated by the offline demo engine (rule-based). Set a Groq API key for LLM-written reports._")
    return "\n".join(L)

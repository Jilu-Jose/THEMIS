/* Pages B: Compliance matrix, Technical scoring (blind), Financial analysis */
(function () {
  const { html, icon, pill } = T;
  T.ui = T.ui || { comp: { tab: "all" }, tech: { bidder: null, crit: null }, fin: { bidder: null } };
  const post = async (path, body, okMsg) => {
    try { T.state.session = await T.api.post(`/api/sessions/${T.state.session.id}/${path}`, body); if (okMsg) T.toast(okMsg, "ok"); T.refreshChrome(); T.render(true); return true; }
    catch (e) { T.toast(e.message, "err", 6000); return false; }
  };
  T.post = post;
  const verBadge = (ok) => (ok ? pill("green", "Quote verified in document", "dot") : pill("amber", "Quote not found verbatim: check manually", "dot"));

  // ================================================================ COMPLIANCE
  T.pages.compliance = (S) => {
    const gate = T.needsRun(S); if (gate) return gate;
    const R = S.rubric, names = S.bids.map((b) => b.name), cm = S.compliance;
    const nq = names.filter((n) => cm[n].verdict !== "DISQUALIFIED").length;
    const checks = names.flatMap((n) => cm[n].checks), okq = checks.filter((c) => c.quote_verified).length;
    const tab = T.ui.comp.tab;
    return html`${T.head("Mandatory Eligibility Compliance Matrix", `Preliminary qualification audit of all ${names.length} bids against criteria ${R.eligibility[0].id} to ${R.eligibility.at(-1).id}. Click any cell for evidence.`,
      html`<a class="btn primary" href="${T.apiBase}/api/sessions/${S.id}/export/full.json">${icon("download")} Export scrutiny sheet (JSON)</a>`)}
      <div class="grid g4 stagger" style="margin-bottom:16px">
        <div class="tile"><div class="l">Bidders audited</div><div class="v" data-count="${names.length}">0</div></div>
        <div class="tile"><div class="l">Qualified</div><div class="v" style="color:var(--green)" data-count="${nq}">0</div></div>
        <div class="tile"><div class="l">Disqualified</div><div class="v" style="color:var(--red)" data-count="${names.length - nq}">0</div></div>
        <div class="tile"><div class="l">Evidence quotes verified</div><div class="v"><span data-count="${okq}">0</span> / ${checks.length}</div><div class="s">checked against the document text</div></div></div>
      <div class="card rise" style="margin-bottom:16px"><div class="row wrap"><div class="tabs" id="c-tabs">${[["all", `All (${names.length})`], ["ok", `Qualified (${nq})`], ["dq", `Disqualified (${names.length - nq})`]].map(([k, l]) => html`<button data-t="${k}" class="${tab === k ? "on" : ""}">${l}</button>`)}</div>
        <div class="field right" style="min-width:240px"><input class="input" id="c-q" placeholder="Filter by bidder name…"></div>
        <div class="legend"><span>${pill("green", "PASS")}</span><span>${pill("red", "FAIL")}</span><span>${pill("amber", "REVIEW")}</span></div></div></div>
      <div class="card rise matrix"><div class="scroll-x"><table class="t"><thead><tr><th>Bidder entity</th>${R.eligibility.map((e) => html`<th style="text-align:center" title="${e.criterion}">${e.id}</th>`)}<th>Verdict</th></tr></thead><tbody>
        ${names.map((n) => { const c = cm[n], dq = c.verdict === "DISQUALIFIED", b = S.bids.find((x) => x.name === n);
          return html`<tr class="${dq ? "dq" : ""}" data-name="${n.toLowerCase()}" data-state="${dq ? "dq" : "ok"}"><td><b class="nm">${n}</b><div class="tiny muted mono">${b.filename}</div></td>
            ${c.checks.map((k, i) => {
              const clar = (S.clarifications || {})[`${n}:${k.id}`];
              const clarBadge = clar ? (clar.vendor_reply ? " • clarified" : " • pending Q") : "";
              return html`<td class="cell"><button class="cellbtn ${k.status}" style="--i:${i}" data-cell="${n}|${k.id}"><span>${icon(k.status === "PASS" ? "check" : k.status === "FAIL" ? "x" : "alert", "sm")}</span><small>${(k.extracted_value || k.status)}${clarBadge}</small></button></td>`;
            })}
            <td>${pill(dq ? "red" : c.verdict === "ELIGIBLE" ? "green" : "amber", dq ? "DISQUALIFIED" : c.verdict.replace("_", " "))}</td></tr>`; })}</tbody></table></div></div>
      <div class="grid g3 stagger" style="margin-top:16px">${R.eligibility.slice(0, 6).map((e) => html`<div class="card"><div class="row"><b class="small" style="color:var(--blue-ink)">${e.id}</b><span class="grow"></span></div><p class="small" style="margin-top:6px">${e.criterion}</p><p class="tiny muted" style="margin-top:6px">Evidence: ${e.evidence_required || "-"}</p></div>`)}</div>`;
  };
  T.mounts.compliance = (root, S) => {
    const apply = () => {
      const q = root.querySelector("#c-q").value.trim().toLowerCase(), tab = T.ui.comp.tab;
      root.querySelectorAll("tbody tr[data-name]").forEach((tr) => { tr.style.display = (tab === "all" || tr.dataset.state === tab) && tr.dataset.name.includes(q) ? "" : "none"; });
    };
    root.querySelectorAll("#c-tabs button").forEach((b) => b.addEventListener("click", () => { T.ui.comp.tab = b.dataset.t; root.querySelectorAll("#c-tabs button").forEach((x) => x.classList.toggle("on", x === b)); apply(); }));
    root.querySelector("#c-q").addEventListener("input", apply); apply();
    root.querySelectorAll("[data-cell]").forEach((b) => b.addEventListener("click", () => {
      root.querySelectorAll(".cellbtn.sel").forEach((x) => x.classList.remove("sel")); b.classList.add("sel");
      const [n, id] = b.dataset.cell.split("|"), k = S.compliance[n].checks.find((x) => x.id === id), target = `compliance:${n}:${id}`;
      const clarKey = `${n}:${id}`;
      const clar = (S.clarifications || {})[clarKey];
      const hist = S.human_actions.filter((h) => h.target === target);
      const tone = k.status === "PASS" ? "good" : k.status === "FAIL" ? "bad" : "warn";
      T.drawer.open(html`<div class="dh"><div class="grow"><div class="tiny" style="opacity:.75;letter-spacing:.8px">CRITERION DEEP DIVE</div><h3 style="font-size:18px;margin-top:4px">${k.id}: ${k.criterion}</h3><div class="small" style="opacity:.85;margin-top:3px">Bidder: ${n}</div></div><button class="btn sm" data-close>${icon("x", "sm")}</button></div>
        <div class="db"><div class="alert ${tone}">${icon(k.status === "PASS" ? "check" : "alert")}<div><b>${k.status}</b>${k.extracted_value ? " · " + k.extracted_value : ""}<div class="small" style="margin-top:4px">${k.reason}</div></div></div>
          <div><div class="tiny muted" style="font-weight:700;letter-spacing:.6px;margin-bottom:6px">EVIDENCE QUOTED FROM THE BID</div>${k.evidence_quote ? html`<div class="quote ${k.status === "FAIL" ? "bad" : ""}">“${k.evidence_quote}”<div class="ver">${verBadge(k.quote_verified)}</div></div>` : html`<div class="muted small">No quote was returned.</div>`}</div>
          ${k.status === "UNCLEAR" && !clar ? html`<div class="alert warn small" style="margin-top:12px">${icon("alert", "sm")}<div><b>Clarification Needed:</b> This mandatory criterion is unclear. Click "Draft Clarification" below to have the system draft a formal request to the bidder.</div></div>` : ""}
          ${clar ? html`<div class="card" style="margin-top:12px;padding:12px;background:#f8fafc;border:1px solid var(--border-color);border-radius:6px">
            <div class="tiny muted" style="font-weight:700;letter-spacing:.6px;margin-bottom:6px">CLARIFICATION INQUIRY</div>
            <div class="quote" style="margin-bottom:8px"><b>Q:</b> ${clar.question}</div>
            <div class="tiny muted" style="margin-bottom:10px">What is required: ${clar.what_is_needed || "Documentation"} · Drafted by: ${clar.officer}</div>
            ${clar.vendor_reply ? html`<div class="quote" style="margin-bottom:8px;background:#eef6ff"><b>Vendor Reply:</b> ${clar.vendor_reply}<div class="tiny muted" style="margin-top:4px">${T.dt(clar.reply_at)}</div></div>
              ${clar.rescore ? html`<div class="alert ${clar.rescore.status === 'PASS' ? 'good' : clar.rescore.status === 'FAIL' ? 'bad' : 'warn'} small"><div><b>Re-scored verdict: ${clar.rescore.status}</b>${clar.rescore.extracted_value ? " · " + clar.rescore.extracted_value : ""}<div class="tiny">${clar.rescore.reason}</div></div></div>` : ""}`
            : html`<div class="field" style="margin-top:8px"><label style="font-weight:600">Enter Vendor's Response</label><textarea class="textarea" id="d-clar-reply" rows="3" placeholder="Paste vendor's clarification response here…"></textarea></div>`}
          </div>` : ""}
          ${hist.length ? html`<div style="margin-top:12px"><div class="tiny muted" style="font-weight:700;letter-spacing:.6px;margin-bottom:6px">COMMITTEE RECORD</div><div class="col">${hist.map((h) => html`<div class="alert info small"><div><b>${h.type}</b> by ${h.by}${h.note ? ": " + h.note : ""}<div class="tiny muted">${T.dt(h.at)}</div></div></div>`)}</div></div>` : ""}
          <div class="field" style="margin-top:12px"><label>Committee note (recorded in the audit trail)</label><textarea class="textarea" id="d-note" placeholder="Optional note…"></textarea></div></div>
        <div class="df">${k.status === "FAIL" ? html`<button class="btn danger" data-k="concur">${icon("gavel", "sm")} Concur with finding</button>` : html`<button class="btn green" data-k="concur">${icon("check", "sm")} Concur with finding</button>`}
          ${(k.status === "UNCLEAR" && !clar) ? html`<button class="btn blue" data-k="draft-clar">${icon("alert", "sm")} Draft Clarification</button>` : ""}
          ${(clar && !clar.vendor_reply) ? html`<button class="btn blue" data-k="submit-clar">${icon("check", "sm")} Submit Reply & Re-score</button>` : ""}
          <button class="btn" data-k="note">Add note</button></div>`,
        (w) => w.querySelectorAll("[data-k]").forEach((a) => a.addEventListener("click", async () => {
          const kind = a.dataset.k;
          if (kind === "draft-clar") {
            a.disabled = true; a.textContent = "Drafting with AI…";
            try {
              T.state.session = await T.api.post(`/api/sessions/${S.id}/clarifications/draft`, { bidder: n, criterion_id: id, officer: T.officer() });
              T.toast("Clarification question drafted", "ok");
              T.refreshChrome(); T.render(true); T.drawer.close();
            } catch (err) {
              T.toast(err.message, "err", 6000);
              a.disabled = false; a.textContent = "Draft Clarification";
            }
          } else if (kind === "submit-clar") {
            const reply = w.querySelector("#d-clar-reply")?.value?.trim();
            if (!reply) { T.toast("Please enter vendor's reply first.", "err"); return; }
            a.disabled = true; a.textContent = "Re-scoring…";
            try {
              T.state.session = await T.api.post(`/api/sessions/${S.id}/clarifications/reply`, { bidder: n, criterion_id: id, vendor_reply: reply, officer: T.officer() });
              T.toast(`Criterion ${id} re-scored successfully`, "ok");
              T.refreshChrome(); T.render(true); T.drawer.close();
            } catch (err) {
              T.toast(err.message, "err", 6000);
              a.disabled = false; a.textContent = "Submit Reply & Re-score";
            }
          } else {
            if (await post("notes", { target, kind, text: w.querySelector("#d-note").value, officer: T.officer() }, "Recorded in audit trail")) T.drawer.close();
          }
        })));
    }));
  };

  // ================================================================ TECHNICAL (blind)
  const heat = (p) => (p >= 0.85 ? ["#bff0d4", "#0c5a33"] : p >= 0.7 ? ["#dcf4e6", "#127a47"] : p >= 0.55 ? ["#fdf3c9", "#8a6204"] : p >= 0.4 ? ["#fdefd3", "#a85a07"] : ["#fde3e3", "#c62828"]);
  const PAL = ["#12285a", "#2f63e6", "#f59e0b", "#16a05b", "#a855f7"];
  T.pages.technical = (S) => {
    const gate = T.needsRun(S); if (gate) return gate;
    const R = S.rubric, tech = S.technical, names = Object.keys(tech), excluded = S.bids.map((b) => b.name).filter((n) => !tech[n]);
    const lab = (n) => T.label(S, n), blind = S.settings.blind_technical && !S.identities_revealed;
    const avg = names.length ? names.reduce((a, n) => a + tech[n].raw_score, 0) / names.length : 0;
    const q = names.filter((n) => tech[n].raw_score >= R.min_technical_score).length;
    const all = names.flatMap((n) => tech[n].scores), okq = all.filter((s) => s.quote_verified).length;
    if (!T.ui.tech.bidder || !tech[T.ui.tech.bidder]) { T.ui.tech.bidder = names[0]; T.ui.tech.crit = R.technical[0].id; }
    const att = S.blind_attested;
    return html`${T.head(blind ? "Technical Proposal Evaluation (Blind Mode)" : "Technical Proposal Evaluation", "Objective scoring against the rubric criteria, with every score tied to a passage from the proposal.",
      html`<a class="btn" href="${T.apiBase}/api/sessions/${S.id}/export/full.json">${icon("download")} Export CSV/JSON</a>`)}
      <div class="card rise" style="margin-bottom:16px"><div class="row wrap"><div class="grow"><div class="row wrap">${pill("blue", blind ? "Blind ledger active" : "Open evaluation")}${pill("gray", `Passing threshold ${R.min_technical_score}/100`)}${pill("gray", `Technical weight ${Math.round(R.weights.technical * 100)}%`)}</div>
        <p class="muted small" style="margin-top:8px">${blind ? "Bidder names were replaced with aliases before the technical agent saw any text." : S.settings.blind_technical ? "Identities were revealed by the committee (recorded in the audit trail)." : "Blind evaluation was switched off for this run."}</p>
        ${excluded.length ? html`<div class="alert bad small" style="margin-top:10px">${icon("alert", "sm")}<div><b>Excluded:</b> ${excluded.join(", ")}: disqualified at the eligibility stage, so no technical scoring was performed.</div></div>` : ""}</div>
        ${S.settings.blind_technical ? html`<div class="sbox row" style="min-width:290px"><span>${icon(blind ? "lock" : "eye", "lg")}</span><div class="grow"><b>${blind ? "Identities masked" : "Identities revealed"}</b><div class="tiny muted">${names.map((n) => lab(n)).join(", ")}</div></div>
          ${blind ? html`<button class="btn sm" id="t-reveal">Reveal</button>` : ""}</div>` : ""}</div></div>
      <div class="grid g4 stagger" style="margin-bottom:16px">
        <div class="tile"><div class="l">Active bidders</div><div class="v"><span data-count="${names.length}">0</span> <span class="muted small">/ ${S.bids.length} evaluated</span></div></div>
        <div class="tile"><div class="l">Committee average</div><div class="v"><span data-count="${avg}" data-dec="1">0</span> <span class="muted small">/ 100</span></div></div>
        <div class="tile"><div class="l">Above cut-off</div><div class="v" style="color:var(--green)"><span data-count="${q}">0</span> qualified</div><div class="s">${names.length - q} below minimum</div></div>
        <div class="tile"><div class="l">Evidence verified</div><div class="v"><span data-count="${all.length ? okq / all.length * 100 : 0}" data-suf="%">0</span></div><div class="s">${okq}/${all.length} quotes found in the bid</div></div></div>
      <div class="card rise"><div class="sec-h"><div class="grow"><h2>Criteria heat-map & weighted scoring grid</h2><div class="sub">Marks per criterion (max shown in header). Click a row cell for the full justification.</div></div></div>
        <div class="scroll-x"><table class="t"><thead><tr><th>${blind ? "Anonymised bidder" : "Bidder"}</th>${R.technical.map((c) => html`<th style="text-align:center">${c.id}: ${c.criterion.split(" ").slice(0, 3).join(" ")}<div class="tiny muted" style="text-transform:none">max ${T.num(c.weight)}</div></th>`)}<th style="text-align:center">Total /100</th></tr></thead><tbody>
          ${names.map((n) => html`<tr><td><b>${lab(n)}</b>${blind ? html`<div class="tiny muted">identity masked</div>` : ""}</td>${tech[n].scores.map((s, i) => { const [bg, fg] = heat(s.score / 10);
            return html`<td style="text-align:center"><button class="heat" style="background:${bg};color:${fg};border:0;--i:${i};cursor:pointer;${T.ui.tech.bidder === n && T.ui.tech.crit === s.id ? "outline:3px solid rgba(29,78,216,.5)" : ""}" data-pick="${n}|${s.id}">${T.num(s.weighted)}<small>${Math.round(s.score * 10)}%</small></button></td>`; })}
            <td style="text-align:center"><b style="font-size:17px;color:${tech[n].raw_score >= R.min_technical_score ? "var(--green)" : "var(--red)"}">${T.num(tech[n].raw_score)}</b></td></tr>`)}</tbody></table></div></div>
      <div class="card rise" id="t-detail" style="margin-top:16px"></div>
      <div class="grid g-aside" style="margin-top:16px">
        <div class="card rise"><div class="sec-h"><div class="grow"><h2>Criterion-wise performance</h2><div class="sub">Share of maximum marks achieved</div></div><div class="legend">${names.map((n, i) => html`<span><i style="background:${PAL[i % 5]}"></i>${lab(n)}</span>`)}</div></div>
          <div class="chart" style="gap:14px">${R.technical.map((c) => html`<div class="bar"><div style="display:flex;gap:4px;align-items:flex-end;height:100%;width:100%;justify-content:center">${names.map((n, i) => { const s = tech[n].scores.find((x) => x.id === c.id); return html`<div class="col2" style="width:22px;background:${PAL[i % 5]}" data-h="${s.score * 10}" title="${lab(n)}: ${Math.round(s.score * 10)}%"></div>`; })}</div></div>`)}</div>
          <div class="chart-x" style="gap:14px">${R.technical.map((c) => html`<span>${c.id}</span>`)}</div></div>
        <div class="card rise" data-i="1"><div class="sec-h"><h2>${icon("shield")} Integrity attestation</h2></div>
          ${att ? html`<div class="alert good">${icon("check")}<div><b>Blind scores ratified</b><div class="small">by ${att.by} · ${T.dt(att.at)}</div></div></div>`
            : html`<p class="small muted">I certify that the technical scores were reviewed independently of the commercial envelopes.</p>
            <label class="row small" style="margin:12px 0"><input type="checkbox" id="t-ack"> I ratify the scores for ${names.map((n) => lab(n)).join(", ")}.</label>
            <button class="btn primary" id="t-attest" disabled>${icon("check", "sm")} Approve blind scores</button>`}</div></div>`;
  };
  T.mounts.technical = (root, S) => {
    const draw = () => {
      const n = T.ui.tech.bidder, c = S.rubric.technical.find((x) => x.id === T.ui.tech.crit), s = S.technical[n].scores.find((x) => x.id === c.id);
      const d = root.querySelector("#t-detail");
      d.innerHTML = html`<div class="sec-h"><h2>Detailed evaluation: ${T.label(S, n)} · ${c.id} ${c.criterion}</h2><span class="right">${pill("blue", `${T.num(s.weighted)} / ${T.num(c.weight)} marks`)}</span></div>
        <div class="tabs" style="margin-bottom:12px">${S.rubric.technical.map((x) => html`<button data-crit="${x.id}" class="${x.id === c.id ? "on" : ""}">${x.id}</button>`)}</div>
        <div class="grid g2"><div><div class="tiny muted" style="font-weight:700;letter-spacing:.6px;margin-bottom:6px">AI EVALUATION NOTE</div><p>${s.justification}</p>
          <div class="bar-track" style="margin-top:12px"><div class="bar-fill ${s.score >= 7 ? "green" : s.score >= 5 ? "amber" : "red"}" data-w="${s.score * 10}"></div></div><div class="tiny muted" style="margin-top:4px">Score ${s.score}/10</div></div>
          <div><div class="tiny muted" style="font-weight:700;letter-spacing:.6px;margin-bottom:6px">EXTRACTED PROPOSAL EXCERPT</div>${s.evidence_quote ? html`<div class="quote">“${s.evidence_quote}”<div class="ver">${verBadge(s.quote_verified)}</div></div>` : html`<div class="muted small">No quote returned.</div>`}</div></div>`.s;
      T.animate(d);
      d.querySelectorAll("[data-crit]").forEach((b) => b.addEventListener("click", () => { T.ui.tech.crit = b.dataset.crit; T.render(true); }));
    };
    draw();
    root.querySelectorAll("[data-pick]").forEach((b) => b.addEventListener("click", () => { const [n, c] = b.dataset.pick.split("|"); T.ui.tech = { bidder: n, crit: c }; T.render(true); root.querySelector("#t-detail")?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }));
    root.querySelector("#t-reveal")?.addEventListener("click", () => { if (confirm("Reveal bidder identities? This is recorded in the audit trail and ends blind review.")) post("reveal-identities", { officer: T.officer() }, "Identities revealed (logged)"); });
    const ack = root.querySelector("#t-ack"), at = root.querySelector("#t-attest");
    ack?.addEventListener("change", () => (at.disabled = !ack.checked));
    at?.addEventListener("click", () => post("attest-blind", { officer: T.officer() }, "Blind scores ratified"));
  };

  // ================================================================ FINANCIAL
  T.pages.financial = (S) => {
    const gate = T.needsRun(S); if (gate) return gate;
    const R = S.rubric, fin = S.financial, names = Object.keys(fin), skipped = S.bids.map((b) => b.name).filter((n) => !fin[n]);
    if (!names.length) return html`${T.head("Financial Analysis", "No financial envelopes were opened.")}${T.empty("No financial bids opened", "Financial envelopes are opened only for technically qualified bidders.")}`;
    if (!T.ui.fin.bidder || !fin[T.ui.fin.bidder]) T.ui.fin.bidder = names[0];
    const totals = names.map((n) => fin[n].recomputed_total).sort((a, b) => a - b), med = totals.length % 2 ? totals[(totals.length - 1) / 2] : (totals[totals.length / 2 - 1] + totals[totals.length / 2]) / 2;
    const max = Math.max(...totals, 1) * 1.15, l1 = totals[0], issues = names.reduce((a, n) => a + fin[n].flags.length, 0);
    const cur = fin[T.ui.fin.bidder], rank = Object.fromEntries(S.ranking.map((r) => [r.bidder, r]));
    return html`${T.head("Financial Analysis", "Price schedules extracted by the Financial Auditor. Every amount is recomputed in Python and compared with what the bidder stated.",
      html`<a class="btn" href="${T.apiBase}/api/sessions/${S.id}/export/ranking.csv">${icon("download")} Export ranking CSV</a>`)}
      <div class="grid g4 stagger" style="margin-bottom:16px">
        <div class="tile"><div class="l">Lowest price (L1)</div><div class="v">${T.cr(l1)}</div></div>
        <div class="tile"><div class="l">Median of opened bids</div><div class="v">${T.cr(med)}</div></div>
        <div class="tile"><div class="l">Envelopes opened</div><div class="v"><span data-count="${names.length}">0</span> <span class="muted small">/ ${S.bids.length}</span></div></div>
        <div class="tile"><div class="l">Arithmetic issues</div><div class="v" style="color:${issues ? "var(--red)" : "var(--green)"}"><span data-count="${issues}">0</span></div></div></div>
      ${skipped.length ? html`<div class="alert info small rise" style="margin-bottom:16px">${icon("info", "sm")}<div>Financial envelope not opened for: <b>${skipped.join(", ")}</b> (not technically qualified or disqualified earlier).</div></div>` : ""}
      <div class="grid g-aside"><div class="card rise"><div class="sec-h"><h2>Price schedule</h2></div>
        <div class="tabs" id="f-tabs" style="margin-bottom:14px">${names.map((n) => html`<button data-b="${n}" class="${n === T.ui.fin.bidder ? "on" : ""}">${n.split(" ")[0]}</button>`)}</div>
        ${cur.flags.map((f) => html`<div class="alert bad" style="margin-bottom:10px">${icon("alert")}<div><b>Discrepancy</b><div class="small">${f}. The recomputed value is used for scoring (tender policy).</div></div></div>`)}
        <div class="scroll-x"><table class="t"><thead><tr><th>Item</th><th style="text-align:right">Qty</th><th style="text-align:right">Unit price</th><th style="text-align:right">Stated amount</th><th style="text-align:right">Recomputed</th></tr></thead><tbody class="stagger">
          ${cur.line_items.map((it) => { const bad = Math.abs(it.qty * it.unit_price - it.amount) > 1; return html`<tr><td>${it.item}</td><td style="text-align:right">${T.inr(it.qty)}</td><td style="text-align:right">${T.rs(it.unit_price)}</td><td style="text-align:right">${T.rs(it.amount)}</td><td style="text-align:right;${bad ? "color:var(--red);font-weight:700" : ""}">${T.rs(it.recomputed)}</td></tr>`; })}
          <tr style="background:#f3f7ff"><td colspan="3"><b>Total</b></td><td style="text-align:right"><b>${T.rs(cur.stated_total)}</b><div class="tiny muted">as stated</div></td><td style="text-align:right"><b style="${Math.abs(cur.stated_total - cur.recomputed_total) > 1 ? "color:var(--red)" : ""}">${T.rs(cur.recomputed_total)}</b><div class="tiny muted">recomputed</div></td></tr></tbody></table></div></div>
        <div class="card rise" data-i="1"><div class="sec-h"><h2>Bid comparison</h2></div>
          <div class="chart" style="height:220px"><div class="median" style="bottom:${med / max * 100}%"><span>median ${T.cr(med)}</span></div>
            ${names.map((n) => { const t = fin[n].recomputed_total, r = t / med, out = r < S.settings.low_price_ratio || r > S.settings.high_price_ratio; return html`<div class="bar"><span class="val">${T.cr(t)}</span><div class="col2" style="background:${out ? "linear-gradient(#f6b94d,#e08a12)" : t === l1 ? "linear-gradient(#5bd396,#16a05b)" : "linear-gradient(#6b8dff,#2f63e6)"}" data-h="${t / max * 100}"></div></div>`; })}</div>
          <div class="chart-x">${names.map((n) => html`<span>${n.split(" ")[0]}</span>`)}</div>
          <div class="legend" style="margin-top:12px"><span><i style="background:#16a05b"></i>L1 (lowest)</span><span><i style="background:#e08a12"></i>Outlier vs median</span><span><i style="background:#2f63e6"></i>Within range</span></div>
          <div class="hr"></div><div class="small"><b>QCBS formula.</b> Financial score = L1 ÷ price × 100.<div class="col" style="margin-top:8px">${names.map((n) => html`<div class="row"><span class="grow">${n.split(" ")[0]}</span><b>${rank[n]?.fin_score != null ? T.num(rank[n].fin_score, 2) : "-"}</b></div>`)}</div></div></div></div>`;
  };
  T.mounts.financial = (root) => root.querySelectorAll("#f-tabs button").forEach((b) => b.addEventListener("click", () => { T.ui.fin.bidder = b.dataset.b; T.render(true); }));
})();

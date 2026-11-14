/* Pages C: Risk & Fraud, Chair decisions, Final ranking & approval, Report & audit log */
(function () {
  const { html, icon, pill } = T;
  const ACTIONS = ["NO_ACTION", "REQUEST_CLARIFICATION", "PENALIZE_10", "PENALIZE_25", "RECOMMEND_DISQUALIFY"];

  // ================================================================ RISK
  T.pages.risk = (S) => {
    const gate = T.needsRun(S); if (gate) return gate;
    const order = { HIGH: 0, MEDIUM: 1, LOW: 2 }, flags = [...S.risk_flags].sort((a, b) => order[a.severity] - order[b.severity]);
    const sevPill = (s) => pill(s === "HIGH" ? "red" : s === "MEDIUM" ? "amber" : "gray", s + " severity");
    const C = 2 * Math.PI * 36;
    const card = (f) => {
      if (f.type === "SIMILARITY") {
        const [a, b] = f.bidders, sa = f.submitted_at[a], sb = f.submitted_at[b], d = f.diff, pct = Math.round(f.similarity * 100), first = sa <= sb ? a : b;
        const seg = (list) => html`${list.map((s) => (s.shared ? html`<mark class="sh">${s.text}</mark> ` : html`${s.text} `))}`;
        return html`<div class="card rise"><div class="row wrap" style="gap:18px;align-items:flex-start">
          <svg class="ring" viewBox="0 0 84 84"><circle cx="42" cy="42" r="36" stroke="#e8edf7"/><circle cx="42" cy="42" r="36" stroke="#c62828" transform="rotate(-90 42 42)" stroke-dasharray="0 ${C}" data-dash="${C * f.similarity} ${C}" style="transition:stroke-dasharray 1.2s var(--ease)"/><text x="42" y="47" text-anchor="middle" font-weight="800" font-size="18" fill="#c62828">${pct}%</text></svg>
          <div class="grow"><div class="row wrap">${sevPill(f.severity)}${pill("gray", "SIMILARITY")}</div><h2 style="margin-top:6px">Copied technical text between ${a.split(" ")[0]} and ${b.split(" ")[0]}</h2>
            <div class="small muted" style="margin-top:4px">Submission times: <b>${a.split(" ")[0]}</b> ${sa} · <b>${b.split(" ")[0]}</b> ${sb}. <b>${first.split(" ")[0]}</b> was submitted first.</div></div></div>
          <div class="hr"></div>
          <div class="legend" style="margin-bottom:8px"><span><mark class="sh">&nbsp;&nbsp;</mark> shared 5-word sequences</span><span>${d.shared_words_a} of ${d.words_a} words in ${a.split(" ")[0]}'s text · ${d.shared_words_b} of ${d.words_b} in ${b.split(" ")[0]}'s</span></div>
          <div class="diff"><div><b>${a}</b><br>${seg(d.a)}</div><div><b>${b}</b><br>${seg(d.b)}</div></div>
          <div class="grid g2" style="margin-top:14px"><div><div class="tiny muted" style="font-weight:700;letter-spacing:.6px;margin-bottom:6px">AI ASSESSMENT</div><p>${f.llm_review.assessment || "-"}</p></div>
          <div><div class="tiny muted" style="font-weight:700;letter-spacing:.6px;margin-bottom:6px">INCONSISTENCIES DETECTED</div>${f.llm_review.inconsistencies.length ? html`<ul style="margin:0;padding-left:18px" class="small">${f.llm_review.inconsistencies.map((x) => html`<li>${x}</li>`)}</ul>` : html`<span class="muted small">None found.</span>`}</div></div></div>`;
      }
      if (f.type === "PRICE_OUTLIER") {
        const pct = Math.round(f.ratio_to_median * 100), w = Math.min(100, f.ratio_to_median / 1.6 * 100);
        return html`<div class="card rise"><div class="row wrap">${sevPill(f.severity)}${pill("gray", "PRICE OUTLIER")}</div><h2 style="margin:6px 0">${f.bidders[0]} is priced at ${pct}% of the median</h2>
          <div class="small muted">Bid ${T.cr(f.price)} vs median ${T.cr(f.median)}. Thresholds: below ${Math.round(S.settings.low_price_ratio * 100)}% or above ${Math.round(S.settings.high_price_ratio * 100)}%.</div>
          <div style="position:relative;margin-top:16px"><div class="bar-track" style="height:12px"><div class="bar-fill amber" data-w="${w}"></div></div>
          <div style="position:absolute;left:${100 / 1.6}%;top:-4px;bottom:-4px;border-left:2px dashed var(--navy)"></div><div class="tiny muted" style="margin-top:6px;margin-left:${100 / 1.6 - 5}%">median</div></div></div>`;
      }
      return html`<div class="card rise"><div class="row wrap">${sevPill(f.severity)}${pill("gray", "ARITHMETIC")}</div><h2 style="margin:6px 0">${f.bidders[0]}: totals do not add up</h2><p class="small">${f.detail}. The recomputed total is used for scoring, per tender policy.</p></div>`;
    };
    return html`${T.head("Risk & Fraud Findings", "Cross-bid text similarity, abnormal prices and arithmetic anomalies detected by the Risk Agent. Rulings are on the Chair page.",
      html`<a class="btn primary" href="#/chair">${icon("gavel")} Chair rulings ${icon("chevron", "sm")}</a>`)}
      <div class="grid g3 stagger" style="margin-bottom:16px">${["HIGH", "MEDIUM", "LOW"].map((s) => html`<div class="card kpi ${s === "HIGH" && flags.some((f) => f.severity === s) ? "red" : ""}"><div class="lab">${s} severity</div><div class="big" data-count="${flags.filter((f) => f.severity === s).length}">0</div></div>`)}</div>
      ${flags.length ? html`<div class="col" style="gap:16px">${flags.map(card)}</div>` : html`<div class="card rise"><div class="alert good">${icon("shield")}<div><b>No risk flags raised.</b> No copied text, price outliers or arithmetic errors were detected.</div></div></div>`}`;
  };
  T.mounts.risk = () => {};

  // ================================================================ CHAIR
  T.pages.chair = (S) => {
    const gate = T.needsRun(S); if (gate) return gate;
    const lock = !!S.approval;
    const typeLabel = { SIMILARITY: "Copied text", PRICE_OUTLIER: "Price outlier", ARITHMETIC: "Arithmetic error" };
    return html`${T.head("Chair Decisions & Human Rulings", "The Chair agent proposes one bounded action per bidder for every flag. Concur or override each ruling; the ranking recalculates immediately.",
      html`<a class="btn primary" href="#/ranking">${icon("award")} Final ranking ${icon("chevron", "sm")}</a>`)}
      ${S.blockers.length ? html`<div class="alert warn rise" style="margin-bottom:16px">${icon("gavel")}<div><b>Committee decision required.</b> Recommended disqualification of <b>${S.blockers.join(", ")}</b> must be concurred or overridden before final approval.</div></div>` : ""}
      ${lock ? html`<div class="alert info rise" style="margin-bottom:16px">${icon("lock")}<div>Evaluation is signed off, so rulings are locked.</div></div>` : ""}
      ${S.decisions.length ? html`<div class="col" style="gap:16px">${S.decisions.map((d) => html`<div class="card rise" data-i="${d.index}"><div class="row wrap">${pill("gray", typeLabel[d.flag_type] || d.flag_type)}<b>${d.bidders.join(" · ")}</b></div>
        <p style="margin:10px 0" class="small">${icon("sparkles", "sm")} <b>Chair rationale:</b> ${d.rationale}</p><div class="col" style="gap:10px">
        ${d.bidders.map((b) => { const h = d.human?.[b], eff = h?.decision === "override" ? h.action : d.actions[b], pending = eff === "RECOMMEND_DISQUALIFY" && !h;
          return html`<div class="sbox" style="${pending ? "border-color:var(--amber);background:#fffaf0" : ""}"><div class="row wrap"><b>${b}</b><span>AI proposed:</span>${T.actionPill(d.actions[b])}
            ${h ? html`<span class="right">${pill(h.decision === "concur" ? "green" : "blue", h.decision === "concur" ? "Concurred" : "Overridden → " + h.action.replaceAll("_", " "), "dot")} <span class="tiny muted">${h.by}${h.note ? " · " + h.note : ""}</span></span>` : pending ? html`<span class="right">${pill("amber", "Blocks approval", "dot live")}</span>` : ""}</div>
            ${lock ? "" : html`<div class="row wrap" style="margin-top:10px" data-row="${d.index}|${b}"><button class="btn sm green" data-concur>${icon("check", "sm")} Concur</button>
              <select class="select" style="width:auto" data-sel>${ACTIONS.map((a) => html`<option value="${a}" ${a === eff ? "selected" : ""}>${a.replaceAll("_", " ")}</option>`)}</select>
              <button class="btn sm" data-over>Override</button><input class="input grow" style="min-width:160px" data-note placeholder="Note (recorded in audit)"></div>`}</div>`; })}</div></div>`)}</div>`
      : html`<div class="card rise"><div class="alert good">${icon("shield")}<div>No risk flags, so no rulings are needed.</div></div></div>`}`;
  };
  T.mounts.chair = (root) => {
    root.querySelectorAll("[data-row]").forEach((row) => {
      const [idx, bidder] = row.dataset.row.split("|"), note = () => row.querySelector("[data-note]").value;
      const send = (decision, action) => T.post("rulings", { index: +idx, bidder, decision, action, note: note(), officer: T.officer() }, decision === "concur" ? "Ruling concurred. Ranking updated." : "Ruling overridden. Ranking recalculated.");
      row.querySelector("[data-concur]").addEventListener("click", () => send("concur", null));
      row.querySelector("[data-over]").addEventListener("click", () => send("override", row.querySelector("[data-sel]").value));
    });
  };

  // ================================================================ RANKING + APPROVAL
  T.pages.ranking = (S) => {
    const gate = T.needsRun(S); if (gate) return gate;
    const R = S.rubric, rows = S.ranking, win = rows.find((r) => r.rank === 1), q = rows.filter((r) => r.status === "QUALIFIED");
    const wt = R.weights.technical, wf = R.weights.financial, maxS = 100, A = S.approval;
    const canApprove = !A && !S.blockers.length && win;
    return html`${T.head("Final Ranking & Committee Approval", "Deterministic QCBS scoring. The AI recommends; the committee records the decision.",
      html`<a class="btn" href="${T.apiBase}/api/sessions/${S.id}/export/ranking.csv">${icon("download")} Ranking CSV</a>`)}
      <div class="card rise"><div class="scroll-x"><table class="t compact"><thead><tr><th>Rank</th><th>Bidder</th><th>Status</th><th>Tech (raw)</th><th>Chair action</th><th>Tech (adj)</th><th style="text-align:right">Price (₹)</th><th>Fin. score</th><th>Final QCBS</th></tr></thead><tbody class="stagger">
        ${rows.map((r) => html`<tr class="${r.status.startsWith("DISQ") ? "dq" : r.rank === 1 ? "win" : ""}"><td>${r.rank ? html`<b style="font-size:18px;color:var(--blue-ink)">L${r.rank}</b>` : "-"}</td><td><b class="nm">${r.bidder}</b></td><td>${T.statusPill(r.status, r.status_label)}</td>
          <td>${r.tech_raw == null ? "-" : T.num(r.tech_raw)}</td><td>${r.chair_action ? T.actionPill(r.chair_action) : "-"}</td><td>${r.tech_adj == null ? "-" : T.num(r.tech_adj)}</td>
          <td style="text-align:right">${r.price ? T.inr(r.price) : "-"}</td><td>${r.fin_score == null ? "-" : T.num(r.fin_score, 2)}</td><td>${r.final_score == null ? "-" : html`<b style="font-size:16px">${T.num(r.final_score, 2)}</b>`}</td></tr>`)}</tbody></table></div></div>
      <div class="grid g-aside" style="margin-top:16px">
        <div class="card rise"><div class="sec-h"><div class="grow"><h2>QCBS score composition</h2><div class="sub">Technical ${Math.round(wt * 100)}% + Financial ${Math.round(wf * 100)}% for qualified bidders</div></div></div>
          ${q.length ? html`<div class="chart" style="height:240px">${q.map((r) => { const t = wt * r.tech_adj, f = wf * r.fin_score; return html`<div class="bar"><span class="val">${T.num(r.final_score, 1)}</span><div class="col2" style="height:0;width:70px" data-h="${(t + f) / maxS * 100}"><i style="height:${f / (t + f) * 100}%;background:linear-gradient(#5bd396,#16a05b)"></i><i style="height:${t / (t + f) * 100}%;background:linear-gradient(#6b8dff,#12285a)"></i></div></div>`; })}</div>
            <div class="chart-x">${q.map((r) => html`<span>${r.bidder.split(" ")[0]}</span>`)}</div><div class="legend" style="margin-top:12px"><span><i style="background:#12285a"></i>Technical contribution</span><span><i style="background:#16a05b"></i>Financial contribution</span></div>`
            : html`<div class="muted">No qualified bidders to chart.</div>`}</div>
        <div class="card rise" data-i="1" id="appr"><div class="sec-h"><h2>${icon("gavel")} Committee approval</h2></div>
          ${A ? html`<div style="text-align:center;padding:10px 0"><div class="stamp ${A.decision === "APPROVED" ? "" : "rej"}"><span style="font-size:22px">${A.decision}</span><span style="font-size:11px;letter-spacing:1px">${A.by}</span></div>
              <p class="small muted" style="margin-top:16px">${T.dt(A.at)}${A.winner ? " · Award recommended to " + A.winner : ""}</p>${A.comment ? html`<p class="small">“${A.comment}”</p>` : ""}
              <div class="tiny muted mono" style="margin-top:8px;word-break:break-all">${icon("hash", "sm")} seal ${A.seal}</div></div>`
          : html`${win ? html`<div class="alert info" style="margin-bottom:12px">${icon("award")}<div><b>AI recommendation: ${win.bidder}</b><div class="small">QCBS ${T.num(win.final_score, 2)} · ${T.cr(win.price)}</div></div></div>` : html`<div class="alert bad" style="margin-bottom:12px">${icon("alert")}<div>No qualified bidder is available for award.</div></div>`}
            ${S.blockers.length ? html`<div class="alert warn" style="margin-bottom:12px">${icon("gavel")}<div class="small"><b>Approval is blocked.</b> Resolve the recommended disqualification of ${S.blockers.join(", ")} on the <a href="#/chair">Chair page</a>.</div></div>` : ""}
            <div class="field"><label>Approving officer (name)</label><input class="input" id="a-off" value="${T.officer()}" placeholder="Full name and designation"></div>
            <div class="field" style="margin-top:10px"><label>Comment</label><textarea class="textarea" id="a-com" placeholder="Reasons, conditions, references…"></textarea></div>
            <label class="row small" style="margin:12px 0"><input type="checkbox" id="a-ack"> I confirm that I have reviewed the evidence and take responsibility for this decision.</label>
            <div class="row wrap"><button class="btn green lg grow" id="a-ok" ${canApprove ? "" : "disabled"}>${icon("check")} Approve recommendation</button><button class="btn danger" id="a-no">Reject & re-evaluate</button></div>`}</div></div>`;
  };
  T.mounts.ranking = (root, S) => {
    const ack = root.querySelector("#a-ack"), ok = root.querySelector("#a-ok"), no = root.querySelector("#a-no");
    if (!ack) return;
    const can = () => !S.blockers.length && S.ranking.some((r) => r.rank === 1);
    ack.addEventListener("change", () => (ok.disabled = !(ack.checked && can())));
    ok.disabled = true;
    const go = async (decision) => {
      const officer = root.querySelector("#a-off").value.trim(); if (!officer) return T.toast("Enter the approving officer's name.", "err");
      T.setOfficer(officer); T.refreshChrome();
      if (await T.post("approval", { decision, officer, comment: root.querySelector("#a-com").value }, decision === "APPROVED" ? "Decision recorded and sealed" : "Rejection recorded")) root.querySelector("#appr")?.classList.add("flash");
    };
    ok.addEventListener("click", () => go("APPROVED"));
    no.addEventListener("click", () => { if (ack.checked || confirm("Record a REJECTION of the AI recommendation?")) go("REJECTED"); });
  };

  // ================================================================ REPORT + AUDIT
  T.pages.report = (S) => {
    const gate = T.needsRun(S); if (gate) return gate;
    const tab = T.state.query.tab === "audit" ? "audit" : "report";
    return html`${T.head("Evaluation Report & Audit Log", "The written report is generated from recorded results only. The audit trail is a hash chain: altering any record breaks every later hash.",
      html`<div class="tabs"><button data-tab="report" class="${tab === "report" ? "on" : ""}">${icon("file", "sm")} Report</button><button data-tab="audit" class="${tab === "audit" ? "on" : ""}">${icon("hash", "sm")} Audit log</button></div>`)}
      ${tab === "report" ? html`${S.report_stale ? html`<div class="alert warn rise no-print" style="margin-bottom:14px">${icon("alert")}<div class="grow"><b>This report is out of date.</b> Rulings or sign-off changed after it was written.</div><button class="btn sm" id="r-regen">${icon("refresh", "sm")} Regenerate</button></div>` : ""}
        <div class="card rise"><div class="row wrap no-print" style="margin-bottom:14px"><a class="btn" href="${T.apiBase}/api/sessions/${S.id}/export/report.md">${icon("download", "sm")} Markdown</a><a class="btn" href="${T.apiBase}/api/sessions/${S.id}/export/ranking.csv">${icon("download", "sm")} Ranking CSV</a>
          <button class="btn" id="r-print">${icon("printer", "sm")} Print / Save as PDF</button>${!S.report_stale ? html`<button class="btn" id="r-regen">${icon("refresh", "sm")} Regenerate</button>` : ""}</div>
          <div class="md stagger">${T.md(S.report_md)}</div></div>`
      : html`<div class="grid g4 stagger" style="margin-bottom:16px"><div class="tile"><div class="l">Records</div><div class="v" data-count="${S.audit_len}">0</div></div>
          <div class="tile"><div class="l">Chain status</div><div class="v" id="chain-v">Unverified</div></div><div class="tile"><div class="l">Session</div><div class="v mono" style="font-size:16px">${S.id}</div></div>
          <div class="tile no-print"><div class="l">Actions</div><div class="row" style="margin-top:6px"><button class="btn primary sm" id="a-verify">${icon("shield", "sm")} Verify chain</button><a class="btn sm" href="${T.apiBase}/api/sessions/${S.id}/export/audit.json">${icon("download", "sm")} Export</a></div></div></div>
        <div class="card rise"><div class="row wrap" style="margin-bottom:12px"><div class="row wrap" id="a-chips"></div><div class="field right" style="min-width:240px"><input class="input" id="a-q" placeholder="Search events…"></div></div>
          <div class="scroll-x" style="max-height:560px;overflow:auto"><table class="t"><thead><tr><th>#</th><th>Time</th><th>Agent</th><th>Action</th><th>Details</th><th>Hash</th></tr></thead><tbody id="a-body"><tr><td colspan="6"><div class="skeleton"></div></td></tr></tbody></table></div></div>`}`;
  };
  T.mounts.report = async (root, S) => {
    root.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => { location.hash = "#/report" + (b.dataset.tab === "audit" ? "?tab=audit" : ""); }));
    root.querySelector("#r-print")?.addEventListener("click", () => window.print());
    root.querySelectorAll("#r-regen").forEach((b) => b.addEventListener("click", async () => { b.disabled = true; b.innerHTML = "Regenerating…"; await T.post("report/regenerate", {}, "Report regenerated"); }));
    if (T.state.query.tab !== "audit") return;
    let recs = [], agent = "All";
    try { recs = await T.api.get(`/api/sessions/${S.id}/audit`); } catch (e) { return T.toast(e.message, "err"); }
    const body = root.querySelector("#a-body"); if (!body) return;
    const agents = ["All", ...new Set(recs.map((r) => r.agent))];
    const draw = () => {
      const q = root.querySelector("#a-q").value.toLowerCase();
      const list = recs.filter((r) => (agent === "All" || r.agent === agent) && (!q || JSON.stringify(r).toLowerCase().includes(q)));
      body.innerHTML = list.map((r, i) => `<tr class="hashrow" data-seq="${r.seq}" style="animation:slideUp .35s both;animation-delay:${Math.min(i, 20) * 18}ms"><td><b>${r.seq}</b></td><td class="small mono">${T.esc(T.tm(r.time))}</td><td><span class="pill blue">${T.esc(r.agent)}</span></td><td>${T.esc(r.action)}</td><td class="tiny muted" style="max-width:380px;word-break:break-word">${T.esc(JSON.stringify(r.detail)?.slice(0, 180) || "")}</td><td class="tiny mono muted" title="${T.esc(r.hash)}">${T.esc(r.hash.slice(0, 10))}…</td></tr>`).join("") || `<tr><td colspan="6" class="muted">No matching events.</td></tr>`;
    };
    root.querySelector("#a-chips").innerHTML = agents.map((a) => `<button class="chip ${a === "All" ? "on" : ""}" data-ag="${T.esc(a)}">${T.esc(a)}</button>`).join("");
    root.querySelectorAll("[data-ag]").forEach((c) => c.addEventListener("click", () => { agent = c.dataset.ag; root.querySelectorAll("[data-ag]").forEach((x) => x.classList.toggle("on", x === c)); draw(); }));
    root.querySelector("#a-q").addEventListener("input", draw); draw();
    root.querySelector("#a-verify").addEventListener("click", async (e) => {
      const btn = e.currentTarget; btn.disabled = true; const v = await T.api.get(`/api/sessions/${S.id}/audit/verify`), rows = [...body.querySelectorAll("tr[data-seq]")], out = root.querySelector("#chain-v");
      out.textContent = "Verifying…";
      for (let i = 0; i < rows.length; i++) { if (v.first_bad_seq && +rows[i].dataset.seq >= v.first_bad_seq) { rows[i].style.background = "var(--red-soft)"; break; } rows[i].classList.add("ok"); if (i < 60) await new Promise((r) => setTimeout(r, 22)); }
      out.innerHTML = v.valid ? `<span style="color:var(--green)">✓ Valid</span>` : `<span style="color:var(--red)">✗ Broken at #${v.first_bad_seq}</span>`;
      T.toast(v.valid ? `Hash chain intact (${v.records} records)` : `Chain broken at record ${v.first_bad_seq}`, v.valid ? "ok" : "err"); btn.disabled = false;
    });
  };
})();

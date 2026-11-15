/* Pages A: Dashboard, New Evaluation (intake), Tender Rubric */
(function () {
  const { html, icon, pill } = T;
  T.mounts = T.mounts || {};

  const AGENTS = [
    { id: "parser", stat: "TenderParser", name: "Tender Parser Agent", ico: "file", page: "rubric", cta: "View Rubric & Rules", desc: "Parses the tender, extracts eligibility clauses, technical criteria and weights." },
    { id: "compliance", stat: "Compliance", name: "Compliance Verifier", ico: "compliance", page: "compliance", cta: "View Compliance Matrix", desc: "Strict pass/fail on every mandatory criterion, with quotes checked against the bid." },
    { id: "technical", stat: "Technical", name: "Technical Evaluator", ico: "chart", page: "technical", cta: "View Technical Scoring", desc: "Blind scoring against the rubric with direct passage citations." },
    { id: "financial", stat: "Financial", name: "Financial Auditor", ico: "rupee", page: "financial", cta: "View Financial Sheet", desc: "Extracts price schedules. Every total is recomputed in Python, never by the LLM." },
    { id: "risk", stat: "Risk", name: "Risk & Fraud Detector", ico: "alert", page: "risk", cta: "Inspect Flagged Risks", desc: "Cross-bid text similarity, price outliers and arithmetic anomalies." },
    { id: "chair", stat: "Chair", name: "Committee Chair", ico: "gavel", page: "chair", cta: "Review Chair Rulings", desc: "Turns flags into bounded actions. Humans concur or override each one." },
    { id: "scoring", stat: null, name: "QCBS Scoring Engine", ico: "award", page: "ranking", cta: "Final Ranking & Approval", desc: "Deterministic Quality-and-Cost-Based scoring and ranking. No LLM involved." },
    { id: "report", stat: "Report", name: "Report Compiler", ico: "file", page: "report", cta: "Open Report & Audit Log", desc: "Writes the evaluation report from recorded results only, with a hash-chained audit trail." },
  ];
  T.AGENTS = AGENTS;

  // ================================================================ DASHBOARD
  T.pages.dashboard = (S) => {
    if (!S) {
      return html`<div class="card empty rise"><div class="orb2">${icon("scale", "lg")}</div>
        <h2>Welcome to T.H.E.M.I.S</h2>
        <p>A committee of seven AI agents that evaluates public tender bids: eligibility, blind technical scoring, price verification, fraud detection and a full audit trail. You make the final call.</p>
        <div class="row" style="justify-content:center"><button class="btn primary lg" data-act="demo">${icon("sparkles")} Load demo tender</button><a class="btn lg" href="#/intake">${icon("upload")} Upload documents</a></div></div>`;
    }
    const R = S.rubric, stages = S.stages, win = S.ranking.find((r) => r.rank === 1);
    const eligible = Object.values(S.compliance).filter((c) => c.verdict !== "DISQUALIFIED").length;
    const dq = Object.values(S.compliance).filter((c) => c.verdict === "DISQUALIFIED").map((c) => c.bidder);
    const high = S.risk_flags.filter((f) => f.severity === "HIGH").length, med = S.risk_flags.filter((f) => f.severity === "MEDIUM").length;
    const ran = !!R;
    const stepper = html`<div class="stepper">${stages.map((st, i) => html`<div class="step ${st.status} ${st.id === "approval" ? "final" : ""}">
      <div class="node">${st.status === "done" ? icon("check", "sm") : st.status === "error" ? icon("x", "sm") : i + 1}</div>
      <div class="lb">${i + 1}. ${st.label}</div><div class="sm">${st.status === "pending" && st.id !== "approval" ? "Pending" : st.summary || ""}</div></div>`)}</div>`;

    const snapshot = ran ? html`<div class="card rise" data-i="5"><div class="sec-h"><div class="grow"><h2>Comparative Evaluation Snapshot</h2>
      <div class="sub">Combined Quality and Cost Based Selection (QCBS ${Math.round(R.weights.technical * 100)}:${Math.round(R.weights.financial * 100)}) · Score = (Technical × ${R.weights.technical.toFixed(2)}) + (Financial × ${R.weights.financial.toFixed(2)})</div></div></div>
      <div class="scroll-x"><table class="t"><thead><tr><th>Bidder entity</th><th>Eligibility</th><th>Tech score</th><th>Financial bid</th><th>QCBS</th><th>Risk level</th><th>Committee status</th></tr></thead>
      <tbody class="stagger">${S.ranking.map((r) => { const b = S.bids.find((x) => x.name === r.bidder) || {}, rk = T.riskOf(S, r.bidder), dqd = r.status.startsWith("DISQUALIFIED");
        return html`<tr class="${dqd ? "dq" : r.rank === 1 ? "win" : ""}"><td><b class="nm">${r.bidder}</b><div class="tiny muted mono">${b.filename || ""} · sha256 ${T.short(b.sha256, 8)}</div></td>
          <td>${pill(r.eligibility === "ELIGIBLE" ? "green" : r.eligibility === "DISQUALIFIED" ? "red" : "amber", r.eligibility.replace("_", " "))}</td>
          <td>${r.tech_raw == null ? html`<span class="muted">N/A</span>` : html`<b>${T.num(r.tech_raw)}</b> <span class="muted">/ 100</span>`}</td>
          <td>${r.price ? T.lakh(r.price) : html`<span class="muted">${r.status === "DISQUALIFIED_ELIGIBILITY" ? "Packet unopened" : "-"}</span>`}</td>
          <td>${r.final_score == null ? html`<span class="muted">-</span>` : html`<b style="font-size:16px;color:var(--blue-ink)">${T.num(r.final_score, 2)}</b>`}</td>
          <td>${r.eligibility === "DISQUALIFIED" ? html`<span class="muted">-</span>` : pill(rk.cls, rk.lvl + (rk.n ? ` (${rk.n})` : ""))}</td>
          <td>${r.rank === 1 ? pill("navy", "Recommended L1") : T.statusPill(r.status, r.status === "QUALIFIED" ? `Rank L${r.rank}` : r.status_label.split(" - ")[0])}</td></tr>`; })}</tbody></table></div></div>` : "";

    const agents = html`<div><div class="sec-h rise"><div class="grow"><h2>Autonomous Evaluation Agents</h2><div class="sub">Each agent shows measured latency and model usage from this run.</div></div>
      ${pill("blue", "Groq · " + S.settings.model)}</div>
      <div class="agents stagger">${AGENTS.map((a) => { const st = stages.find((x) => x.id === a.id) || {}, ag = a.stat && S.agent_stats[a.stat];
        return html`<div class="card hover agent ${st.status}"><div class="top2"><div class="ai">${icon(a.ico)}</div><b>${a.name}</b><span class="lat">${st.seconds != null ? st.seconds + "s" : st.status === "running" ? "running" : "-"}</span></div>
          <p>${a.desc}</p><div class="meta"><span>${pill(st.status === "done" ? "green" : st.status === "error" ? "red" : st.status === "running" ? "blue" : "gray", st.status === "done" ? "Completed" : st.status, "dot")}</span>
          ${ag ? html`<span>${ag.calls} call${ag.calls > 1 ? "s" : ""}${ag.tokens ? " · " + ag.tokens.toLocaleString() + " tok" : ""}</span>` : ""}</div>
          <a class="go" href="#/${a.page}">${a.cta} ${icon("chevron", "sm")}</a></div>`; })}</div></div>`;

    return html`
      <div class="card rise"><div class="hero"><div>
        <div class="row wrap">${pill("navy", "Tender No: " + (R?.tender_id || "-"))}${pill("blue", "LLM: " + S.settings.model)}${S.settings.blind_technical ? pill("blue", "Blind technical evaluation") : ""}</div>
        <h1>${R?.title || S.tender?.filename || "Untitled tender"}</h1>
        <div class="muted">${R?.issuer || "Documents staged. Run the evaluation to extract the rubric."}</div></div>
        <div class="col no-print" style="align-items:flex-end">
          <div class="row wrap" style="justify-content:flex-end;gap:8px">
            <button class="btn blue" data-act="reset-run" title="Remove previous run data and start a new evaluation">${icon("trash")} Remove Run &amp; Start New</button>
            <a class="btn" href="#/report?tab=audit">${icon("hash")} View Audit Trail</a>
            ${ran ? html`<a class="btn primary" href="${T.apiBase}/api/sessions/${S.id}/export/report.md">${icon("download")} Download Report (.md)</a>` : html`<a class="btn primary" href="#/intake">${icon("play")} Run evaluation</a>`}
          </div>
          ${S.tender ? html`<span class="tiny muted mono">${icon("lock", "sm")} tender sha256 ${T.short(S.tender.sha256, 12)}</span>` : ""}</div></div>
        <div class="tiles stagger">
          <div class="tile"><div class="l">Selection method</div><div class="v">${R ? "QCBS " + Math.round(R.weights.technical * 100) + ":" + Math.round(R.weights.financial * 100) : "-"}</div><div class="s">${R ? R.financial_method.slice(0, 48) : ""}</div></div>
          <div class="tile"><div class="l">Min technical score</div><div class="v">${R ? R.min_technical_score : "-"} <span class="muted small">/ 100</span></div><div class="s">Strict cut-off</div></div>
          <div class="tile"><div class="l">Criteria extracted</div><div class="v">${R ? R.eligibility.length + " + " + R.technical.length : "-"}</div><div class="s">Eligibility + technical</div></div>
          <div class="tile"><div class="l">Session</div><div class="v mono" style="font-size:16px">${S.id}</div><div class="s">${T.dt(S.created_at)}</div></div></div></div>

      <div class="card rise" data-i="1" style="margin-top:16px"><div class="sec-h"><div class="grow"><h2>${icon("sparkles")} Evaluation Pipeline</h2></div>
        ${S.status === "running" ? pill("blue", "Running", "dot live") : S.status === "error" ? pill("red", "Error") : S.status === "complete" ? pill("green", "Pipeline complete") : pill("gray", "Not started")}</div>
        ${S.error ? html`<div class="alert bad" style="margin-bottom:10px">${icon("alert")}<div>${S.error}</div></div>` : ""}${stepper}</div>

      ${(() => {
        const clars = Object.values(S.clarifications || {});
        const pending = clars.filter((c) => !c.vendor_reply).length;
        const resolved = clars.filter((c) => c.vendor_reply).length;
        if (!clars.length) return "";
        return html`<div class="alert info rise" style="margin-top:16px">${icon("info", "sm")}<div><b>Clarification Loop:</b> ${pending ? html`<span style="color:var(--amber);font-weight:700">${pending} question(s) awaiting vendor reply</span>` : "All queries resolved."} ${resolved ? `(${resolved} criterion re-scored)` : ""} — <a href="#/compliance" style="text-decoration:underline">Open Compliance Matrix</a></div></div>`;
      })()}

      ${ran ? html`<div class="grid g4 stagger" style="margin:16px 0">
        <div class="card kpi"><div class="lab">Bids received<span class="ico">${icon("file")}</span></div><div class="big"><span data-count="${S.bids.length}">0</span><small>bidders</small></div><div class="sub">All documents hashed (SHA-256) on intake</div></div>
        <div class="card kpi"><div class="lab">Eligible bids<span class="ico">${icon("compliance")}</span></div><div class="big"><span data-count="${eligible}">0</span><small>passed E-criteria</small></div><div class="sub">${dq.length ? html`<span style="color:var(--red)">${dq.length} disqualified: ${dq.map((n) => n.split(" ")[0]).join(", ")}</span>` : "None disqualified"}</div></div>
        <div class="card kpi ${S.risk_flags.length ? "red" : ""}"><div class="lab">Integrity & risk flags<span class="ico" style="background:var(--red-soft);color:var(--red)">${icon("shield")}</span></div><div class="big"><span data-count="${S.risk_flags.length}">0</span><small>exceptions</small></div><div class="sub">${high} high · ${med} medium · ${S.risk_flags.length - high - med} low</div></div>
        <div class="card kpi"><div class="lab">Recommended award (L1/H1)<span class="ico">${icon("award")}</span></div><div class="big" style="font-size:21px;margin-top:14px">${win ? win.bidder.split(" ").slice(0, 2).join(" ") : "-"}</div><div class="sub">${win ? html`QCBS <b>${T.num(win.final_score, 2)}</b> / 100 · ` : ""}${S.approval ? S.approval.decision + " by " + S.approval.by : "Awaiting final sign-off"}</div></div></div>` : ""}
      ${snapshot}
      <div style="margin-top:22px">${agents}</div>
      ${ran ? html`<div class="card rise" style="margin-top:16px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">${icon("users", "lg")}<div class="grow"><b>${S.approval ? "Committee sign-off recorded" : "Committee sign-off pending"}</b><div class="small muted">${S.approval ? S.approval.decision + " by " + S.approval.by + " · seal " + T.short(S.approval.seal, 12) : S.blockers.length ? "Decisions required: recommended disqualification of " + S.blockers.join(", ") : "Review the ranking and record the committee decision."}</div></div>
        <a class="btn primary" href="#/ranking">${S.approval ? "View sign-off" : "Go to approval"} ${icon("chevron", "sm")}</a></div>` : ""}`;
  };
  T.mounts.dashboard = (root, S) => {
    root.querySelector("[data-act=demo]")?.addEventListener("click", () => T.loadDemo(true));
    root.querySelector("[data-act=reset-run]")?.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to remove the previous evaluation run data and start a new evaluation?")) return;
      try {
        if (S && S.id) {
          await T.api.del(`/api/sessions/${S.id}`);
        }
        T.state.session = null;
        T.intake = { tender: null, bids: [], settings: null };
        T.toast("Previous evaluation data removed.", "ok", 4000);
        location.hash = "#/intake";
      } catch (e) {
        T.toast(e.message, "err", 5000);
      }
    });
  };

  // ================================================================ INTAKE
  const fmtSize = (n) => (n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB");
  const nowLocal = () => { const d = new Date(Date.now() - new Date().getTimezoneOffset() * 60000); return d.toISOString().slice(0, 16); };
  T.intake = T.intake || { tender: null, bids: [], settings: null };

  T.pages.intake = (S) => {
    const I = T.intake, H = T.state.health;
    if (!I.settings) I.settings = { ...H.defaults, ...(S?.settings || {}) };
    const st = I.settings, staged = S && S.status === "created", running = S && S.status === "running";
    const canRun = !running && (staged || (I.tender && I.bids.length) || (S && S.rubric));
    const runLabel = I.tender && I.bids.length ? "Run Evaluation Committee" : S?.rubric ? "Re-run current evaluation" : "Run Evaluation Committee";

    const tenderCard = html`<div class="card rise" data-i="1"><div class="sec-h"><div class="grow"><h2>Tender Notice (NIT / RFP)</h2></div>${pill("blue", "1 file · mandatory")}</div>
      <p class="muted small" style="margin-bottom:12px">The master tender document: eligibility criteria, technical criteria, weights and selection method.</p>
      ${staged ? html`<div class="file"><div class="no">${icon("file", "sm")}</div><div class="grow"><b>${S.tender.filename}</b><div class="tiny muted mono">${fmtSize(S.tender.words * 6)} · ${S.tender.words} words · sha256 ${T.short(S.tender.sha256, 10)}</div></div>${pill("green", "Staged")}</div>`
        : I.tender ? html`<div class="file"><div class="no">${icon("file", "sm")}</div><div class="grow"><b>${I.tender.name}</b><div class="tiny muted">${fmtSize(I.tender.size)}</div></div><button class="btn sm" data-act="rm-tender">${icon("trash", "sm")}</button></div>`
        : html`<div class="drop" data-drop="tender"><div class="u">${icon("upload", "lg")}</div><b>Drag & drop the tender document</b><div class="small muted" style="margin:4px 0 12px">PDF, TXT or MD · up to 25 MB</div><button class="btn primary sm" data-act="pick-tender">Browse files</button></div>`}
      <input type="file" id="f-tender" accept=".pdf,.txt,.md" hidden></div>`;

    const bidList = staged ? S.bids.map((b, i) => html`<div class="file" style="animation-delay:${i * 70}ms"><div class="no">${String(i + 1).padStart(2, "0")}</div><div class="grow"><b>${b.name}</b><div class="tiny muted mono">${b.filename} · ${b.words} words · sha256 ${T.short(b.sha256, 8)} · submitted ${b.submitted_at}</div></div>${pill("green", "Ready")}</div>`)
      : I.bids.map((b, i) => html`<div class="file" style="animation-delay:${i * 70}ms"><div class="no">${String(i + 1).padStart(2, "0")}</div><div class="grow col" style="gap:6px">
          <input class="input" data-bid-name="${i}" value="${b.name}" aria-label="Bidder name"><div class="row wrap"><span class="tiny muted">${b.file.name} · ${fmtSize(b.file.size)}</span>
          <label class="tiny muted right">Submitted <input type="datetime-local" class="input" style="width:auto;padding:4px 6px" data-bid-time="${i}" value="${b.submitted}"></label></div></div>
          <button class="btn sm" data-rm-bid="${i}" title="Remove">${icon("trash", "sm")}</button></div>`);
    const bidsCard = html`<div class="card rise" data-i="2"><div class="sec-h"><div class="grow"><h2>Bidder Submission Dossiers</h2></div>${pill("blue", (staged ? S.bids.length : I.bids.length) + " bids staged")}</div>
      <p class="muted small" style="margin-bottom:12px">One file per bidder (technical + financial). The <b>submission time</b> decides which bid is treated as the original when text is copied between bids.</p>
      ${!staged ? html`<div class="drop" data-drop="bids" style="padding:16px;margin-bottom:12px"><b>Add bidder files</b> <span class="small muted">drag & drop or</span> <button class="btn primary sm" data-act="pick-bids">${icon("upload", "sm")} Add bidder dossier</button></div><input type="file" id="f-bids" accept=".pdf,.txt,.md" multiple hidden>` : ""}
      <div class="col" id="bid-list">${bidList.length ? bidList : html`<div class="muted small" style="padding:8px">No bids added yet.</div>`}</div></div>`;

    const settings = html`<div class="card rise" data-i="3"><div class="sec-h"><div class="grow"><h2>${icon("cpu")} Evaluation Hyperparameters & Guards</h2></div></div>
      <div class="sg">
        <div class="sbox"><h4>LLM reasoning model ${pill(H.mode === "groq" ? "green" : "red", H.mode === "groq" ? "Groq connected" : "Key required")}</h4>
          <select class="select" id="s-model">${H.models.map((m) => html`<option value="${m}" ${st.model === m ? "selected" : ""}>${m}${m.endsWith("120b") ? " (recommended)" : ""}</option>`)}</select>
          <div class="tiny muted" style="margin-top:6px">${H.mode === "groq" ? "Requests go to the Groq API with your key." : "No GROQ_API_KEY found: please add your key to .env to run evaluations."}</div></div>
        <div class="sbox"><h4>Reasoning effort <span class="small muted" id="eff-l">${st.reasoning_effort}</span></h4>
          <div class="seg" id="s-effort">${["low", "medium", "high"].map((e) => html`<button data-v="${e}" class="${st.reasoning_effort === e ? "on" : ""}">${e[0].toUpperCase() + e.slice(1)}</button>`)}</div>
          <div class="tiny muted" style="margin-top:6px">Higher effort = deeper reasoning per call, slower and costlier.</div></div>
        <div class="sbox"><h4>Price-outlier thresholds <span class="small muted">vs. median of qualified bids</span></h4>
          <div class="row"><div class="field grow"><label>Abnormally low below (%)</label><input class="input" type="number" min="1" max="99" id="s-low" value="${Math.round(st.low_price_ratio * 100)}"></div>
          <div class="field grow"><label>Excess premium above (%)</label><input class="input" type="number" min="101" max="500" id="s-high" value="${Math.round(st.high_price_ratio * 100)}"></div></div></div>
        <div class="sbox"><h4>Copy-paste similarity gate <b id="sim-l">${st.similarity_threshold.toFixed(2)}</b></h4>
          <input type="range" id="s-sim" min="0.1" max="0.9" step="0.01" value="${st.similarity_threshold}"><div class="tiny muted">Jaccard overlap of 5-word shingles in technical proposals.</div></div></div>
      <div class="row sbox" style="margin-top:16px"><button class="switch ${st.blind_technical ? "on" : ""}" id="s-blind" aria-label="Blind technical evaluation"></button>
        <div><b>Enforce blind technical evaluation</b><div class="small muted">Bidder names are replaced by Bidder-A, B, C… before the technical agent sees the text.</div></div></div></div>`;

    const intakeActions = html`
      ${S ? html`<button class="btn blue sm" data-act="reset-run">${icon("trash")} Remove Previous Run</button>` : ""}
      <button class="btn ghost" data-act="demo">${icon("sparkles")} Load demo data (Water Quality Monitoring tender)</button>
    `;

    return html`${T.head("New Evaluation Workflow", "Upload procurement documents, configure the reasoning parameters and convene the multi-agent committee.", intakeActions)}
      ${H.mode !== "groq" ? html`<div class="alert bad rise" style="margin-bottom:16px">${icon("alert")}<div><b>API Key Required.</b> No <span class="mono">GROQ_API_KEY</span> is configured. Add your Groq API key to <span class="mono">.env</span> and restart the server to run evaluations.</div></div>` : ""}
      <div class="grid g2">${tenderCard}${bidsCard}</div><div style="margin-top:16px">${settings}</div>
      <div class="card rise" data-i="4" style="margin-top:16px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">
        <div class="grow small muted">${icon("lock", "sm")} A tamper-evident audit record is generated from the moment you run.</div>
        ${staged || I.tender || I.bids.length ? html`<button class="btn" data-act="clear">Clear staged</button>` : ""}
        <button class="btn primary lg" data-act="run" ${canRun ? "" : "disabled"}>${icon("sparkles")} ${runLabel} (7 agents) ${icon("chevron", "sm")}</button></div>`;
  };

  T.mounts.intake = (root, S) => {
    const I = T.intake, st = I.settings, rerender = () => T.render(true);
    root.querySelector("[data-act=reset-run]")?.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to remove the previous evaluation run data and start a new evaluation?")) return;
      try {
        if (S && S.id) {
          await T.api.del(`/api/sessions/${S.id}`);
        }
        T.state.session = null;
        I.tender = null;
        I.bids = [];
        T.toast("Previous evaluation data removed.", "ok", 4000);
        T.render();
      } catch (e) {
        T.toast(e.message, "err", 5000);
      }
    });
    const setTender = (f) => { if (f) { I.tender = { name: f.name, size: f.size, file: f }; rerender(); } };
    const addBids = (files) => {
      [...files].forEach((f) => I.bids.push({ file: f, name: f.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim(), submitted: nowLocal() }));
      rerender();
    };
    root.querySelectorAll("[data-act=demo]").forEach((b) => b.addEventListener("click", () => T.loadDemo(false)));
    root.querySelector("[data-act=pick-tender]")?.addEventListener("click", () => root.querySelector("#f-tender").click());
    root.querySelector("#f-tender")?.addEventListener("change", (e) => setTender(e.target.files[0]));
    root.querySelector("[data-act=pick-bids]")?.addEventListener("click", () => root.querySelector("#f-bids").click());
    root.querySelector("#f-bids")?.addEventListener("change", (e) => addBids(e.target.files));
    root.querySelector("[data-act=rm-tender]")?.addEventListener("click", () => { I.tender = null; rerender(); });
    root.querySelectorAll("[data-drop]").forEach((z) => {
      ["dragenter", "dragover"].forEach((ev) => z.addEventListener(ev, (e) => { e.preventDefault(); z.classList.add("over"); }));
      ["dragleave", "drop"].forEach((ev) => z.addEventListener(ev, (e) => { e.preventDefault(); z.classList.remove("over"); }));
      z.addEventListener("drop", (e) => (z.dataset.drop === "tender" ? setTender(e.dataTransfer.files[0]) : addBids(e.dataTransfer.files)));
    });
    root.querySelectorAll("[data-rm-bid]").forEach((b) => b.addEventListener("click", () => {
      const row = b.closest(".file"); row.classList.add("leaving"); setTimeout(() => { I.bids.splice(+b.dataset.rmBid, 1); rerender(); }, 280);
    }));
    root.querySelectorAll("[data-bid-name]").forEach((i) => i.addEventListener("input", () => (I.bids[+i.dataset.bidName].name = i.value)));
    root.querySelectorAll("[data-bid-time]").forEach((i) => i.addEventListener("input", () => (I.bids[+i.dataset.bidTime].submitted = i.value)));
    root.querySelector("#s-model")?.addEventListener("change", (e) => (st.model = e.target.value));
    root.querySelectorAll("#s-effort button").forEach((b) => b.addEventListener("click", () => {
      st.reasoning_effort = b.dataset.v; root.querySelectorAll("#s-effort button").forEach((x) => x.classList.toggle("on", x === b)); root.querySelector("#eff-l").textContent = b.dataset.v;
    }));
    root.querySelector("#s-low")?.addEventListener("input", (e) => (st.low_price_ratio = (+e.target.value || 60) / 100));
    root.querySelector("#s-high")?.addEventListener("input", (e) => (st.high_price_ratio = (+e.target.value || 140) / 100));
    root.querySelector("#s-sim")?.addEventListener("input", (e) => { st.similarity_threshold = +e.target.value; root.querySelector("#sim-l").textContent = (+e.target.value).toFixed(2); });
    root.querySelector("#s-blind")?.addEventListener("click", (e) => { st.blind_technical = !st.blind_technical; e.currentTarget.classList.toggle("on", st.blind_technical); });
    root.querySelector("[data-act=clear]")?.addEventListener("click", () => { I.tender = null; I.bids = []; T.state.session = S && S.status === "created" ? null : S; T.render(true); T.refreshChrome(); });
    root.querySelector("[data-act=run]")?.addEventListener("click", async (e) => {
      const btn = e.currentTarget; btn.disabled = true;
      try {
        let sid = S && !(I.tender && I.bids.length) ? S.id : null;
        if (!sid) {
          const fd = new FormData(); fd.append("tender", I.tender.file);
          I.bids.forEach((b) => fd.append("bids", b.file));
          fd.append("meta", JSON.stringify(I.bids.map((b) => ({ name: b.name, submitted_at: b.submitted.replace("T", " ") }))));
          const created = await T.api.form("/api/sessions", fd); sid = created.id; T.state.session = created; I.tender = null; I.bids = [];
        }
        T.startRun(sid, st);
      } catch (err) { T.toast(err.message, "err", 6000); btn.disabled = false; }
    });
  };

  // ================================================================ RUBRIC
  T.pages.rubric = (S) => {
    const gate = T.needsRun(S); if (gate) return gate; const R = S.rubric;
    const cols = ["#1d4ed8", "#3b82f6", "#6b8dff", "#0f2f8a", "#93b4ff", "#7aa2f7", "#4a6fd8"]; let off = 0;
    const C = 2 * Math.PI * 54, segs = R.technical.map((t, i) => { const len = C * t.weight / 100, s = { off, len, c: cols[i % cols.length] }; off += len; return s; });
    return html`${T.head("Tender Evaluation Rubric", "Extracted from the tender document by the Tender Parser Agent. These criteria drive every downstream agent.",
      html`<a class="btn" href="${T.apiBase}/api/sessions/${S.id}/export/full.json">${icon("download")} Export JSON</a>`)}
      <div class="grid g4 stagger" style="margin-bottom:16px">
        <div class="tile"><div class="l">Evaluation scheme</div><div class="v">QCBS</div><div class="s">${R.financial_method.slice(0, 60)}</div></div>
        <div class="tile"><div class="l">Weightage ratio</div><div class="v">${Math.round(R.weights.technical * 100)}% Tech / ${Math.round(R.weights.financial * 100)}% Fin</div></div>
        <div class="tile"><div class="l">Minimum technical cut-off</div><div class="v">${R.min_technical_score} <span class="muted small">/ 100</span></div><div class="s">Strict disqualification below</div></div>
        <div class="tile"><div class="l">Mandatory eligibility</div><div class="v">100% pass</div><div class="s">All of ${R.eligibility.map((e) => e.id).join(", ")}</div></div></div>
      <div class="grid g-aside" style="margin-bottom:16px">
        <div class="card rise"><div class="sec-h"><h2>Technical criteria weight distribution</h2></div><div class="row wrap" style="gap:28px">
          <div class="dwrap"><svg class="donut" viewBox="0 0 150 150">${segs.map((s) => html`<circle cx="75" cy="75" r="54" stroke="${s.c}" stroke-dashoffset="${-s.off}" stroke-dasharray="0 ${C}" data-dash="${s.len} ${C - s.len}"/>`)}</svg><div class="c"><div>100<small>MAX TECH SCORE</small></div></div></div>
          <div class="grow col stagger" style="min-width:260px">${R.technical.map((t, i) => html`<div><div class="row small"><b>${t.id}</b><span class="grow">${t.criterion}</span><b>${T.num(t.weight)} pts</b></div><div class="bar-track" style="margin-top:4px"><div class="bar-fill" style="background:${cols[i % cols.length]}" data-w="${t.weight}"></div></div></div>`)}</div></div></div>
        <div class="card rise" data-i="1"><div class="sec-h"><h2>${icon("shield")} How the rules are applied</h2></div><div class="col small">
          <div class="alert info"><div><b>Stage 1: Mandatory eligibility.</b> Binary pass/fail on every criterion with quoted evidence. A single FAIL disqualifies the bidder before technical opening.</div></div>
          <div class="alert info"><div><b>Stage 2: Technical scoring.</b> Bids scoring below ${R.min_technical_score} are not qualified. Financial envelopes are opened only for technically qualified bidders.</div></div>
          <div class="alert info"><div><b>Stage 3: QCBS.</b> Financial score = lowest price ÷ bidder price × 100. Final = ${R.weights.technical.toFixed(2)}×Technical + ${R.weights.financial.toFixed(2)}×Financial.</div></div></div></div></div>
      <div class="card rise" style="margin-bottom:16px"><div class="sec-h"><h2>Envelope A: Mandatory Eligibility Criteria</h2>${pill("blue", R.eligibility.length + " criteria")}</div>
        <div class="scroll-x"><table class="t"><thead><tr><th>Code</th><th>Criterion</th><th>Evidence required</th><th>Rule</th></tr></thead><tbody class="stagger">${R.eligibility.map((e) => html`<tr><td><b>${e.id}</b></td><td>${e.criterion}</td><td class="muted">${e.evidence_required || "-"}</td><td>${pill("gray", "Pass / Fail")}</td></tr>`)}</tbody></table></div></div>
      <div class="card rise"><div class="sec-h"><h2>Envelope B: Technical Evaluation Rubric</h2>${pill("blue", R.technical.length + " criteria · 100 marks")}</div>
        <div class="scroll-x"><table class="t"><thead><tr><th>Code</th><th>Technical domain</th><th>Max marks</th><th style="width:30%">Weight</th></tr></thead><tbody class="stagger">${R.technical.map((t) => html`<tr><td><b>${t.id}</b></td><td>${t.criterion}</td><td><b>${T.num(t.weight)}</b></td><td><div class="bar-track"><div class="bar-fill" data-w="${t.weight * 100 / Math.max(...R.technical.map((x) => x.weight))}"></div></div></td></tr>`)}</tbody></table></div></div>`;
  };
})();

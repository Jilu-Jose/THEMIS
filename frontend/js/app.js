/* T.H.E.M.I.S app shell: router, chrome (nav/top bar), live run overlay (SSE), bootstrap */
(function () {
  const { html, icon, pill } = T;
  const NAV = [
    ["dashboard", "Dashboard", "dashboard"], ["intake", "New Evaluation", "upload"], ["rubric", "Tender Rubric", "rubric"],
    ["compliance", "Compliance Matrix", "compliance"], ["technical", "Technical Scoring", "chart"], ["financial", "Financial Analysis", "rupee"],
    ["risk", "Risk and Fraud", "alert"], ["chair", "Chair Decisions", "gavel"], ["ranking", "Final Ranking & Approval", "award"], ["report", "Report & Audit Log", "file"],
  ];
  const STAGES = [["parser", "Tender Parser"], ["compliance", "Compliance"], ["technical", "Technical (blind)"], ["financial", "Financial"], ["risk", "Risk & Fraud"], ["chair", "Chair"], ["scoring", "QCBS Scoring"], ["report", "Report"]];

  // ---------------------------------------------------------------- routing
  const parse = () => {
    const h = location.hash.replace(/^#\/?/, ""), [r, q] = h.split("?");
    T.state.query = Object.fromEntries(new URLSearchParams(q || ""));
    const route = NAV.some((n) => n[0] === r) ? r : "dashboard"; T.state.route = route; return route;
  };
  T.render = (soft) => {
    const route = parse(), S = T.state.session, page = document.getElementById("page");
    const y = window.scrollY;
    page.innerHTML = T.pages[route](S).s;
    if (!soft) { page.classList.remove("enter"); void page.offsetWidth; page.classList.add("enter"); window.scrollTo(0, 0); } else window.scrollTo(0, y);
    T.animate(page); T.mounts[route] && T.mounts[route](page, S); T.refreshChrome();
  };

  // ---------------------------------------------------------------- chrome
  T.refreshChrome = () => {
    const S = T.state.session, H = T.state.health, route = T.state.route;
    document.getElementById("nav").innerHTML = NAV.map(([id, label, ic]) => {
      const n = id === "risk" ? S?.risk_flags?.length : id === "chair" ? S?.blockers?.length : 0;
      return `<a href="#/${id}" class="${id === route ? "active" : ""}">${icon(ic).s}<span>${label}</span>${n ? `<span class="badge ${id === "chair" ? "amber" : ""}">${n}</span>` : ""}</a>`;
    }).join("");
    const A = S?.approval;
    const st = !S ? ["gray", "No evaluation"] : S.status === "running" ? ["blue", "Committee in session"] : S.status === "error" ? ["red", "Error"] : A ? (A.decision === "APPROVED" ? ["green", "Approved"] : ["red", "Rejected"]) : S.status === "complete" ? ["amber", "Awaiting sign-off"] : ["gray", "Documents staged"];
    const off = T.officer() || "Evaluation Officer", ini = off.split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase();
    document.getElementById("top").innerHTML = `<span class="tid"><small>Tender ID</small>${T.esc(S?.rubric?.tender_id || "-")}</span><span class="ttl">${T.esc(S?.rubric?.title || S?.tender?.filename || "No tender loaded")}</span>
      ${pill(st[0], st[1], "dot " + (S?.status === "running" ? "live" : "")).s}${pill(H?.mode === "groq" ? "blue" : "amber", H?.mode === "groq" ? "Groq · gpt-oss" : "Demo engine").s}
      <button class="officer" id="officer" title="Set your name for audit records"><div><b>${T.esc(off)}</b><span>Senior Evaluation Officer</span></div><div class="avatar">${T.esc(ini || "EO")}</div></button>`;
    document.getElementById("officer").onclick = () => { const n = prompt("Your name (recorded on rulings, notes and sign-off):", T.officer()); if (n !== null) { T.setOfficer(n.trim()); T.refreshChrome(); } };
    document.getElementById("side-foot").innerHTML = `<span>${icon("cpu", "sm").s} ${H?.mode === "groq" ? T.esc(S?.settings?.model || H.model) : "Offline demo engine"}</span><span>${icon("hash", "sm").s} Audit chain: SHA-256</span><span class="tiny">Session ${T.esc(S?.id || "-")} · v1.0</span>`;
  };

  // ---------------------------------------------------------------- demo loader
  T.loadDemo = async () => {
    try {
      T.state.session = await T.api.post("/api/sessions/demo"); T.intake = { tender: null, bids: [], settings: null };
      T.toast("Demo tender and 4 bids staged. Review settings, then run the committee.", "ok", 5000);
      location.hash.startsWith("#/intake") ? T.render() : (location.hash = "#/intake");
    } catch (e) { T.toast(e.message, "err", 6000); }
  };

  // ---------------------------------------------------------------- live run overlay
  const logText = (e) => {
    const d = e.detail || {}, a = e.action;
    const m = {
      llm_call: () => (d.engine ? "Offline engine call completed" : `Model call completed${d.tokens ? ` (${d.tokens} tokens)` : ""}`),
      llm_error: () => `LLM error (attempt ${d.attempt}): ${d.error}`,
      pipeline_started: () => `Pipeline started · ${d.bids.length} bids · ${d.model}`,
      rubric_extracted: () => `Rubric extracted: ${d.eligibility} eligibility + ${d.technical} technical criteria`,
      verdict: () => `${d.bidder}: ${d.verdict}`, scored: () => `${d.bidder}: technical ${d.raw_score}/100`,
      verified: () => `${d.bidder}: total recomputed ${T.rs(d.recomputed_total)}${d.flags ? ` · ${d.flags} issue(s)` : ""}`,
      flags_raised: () => `${d.count} risk flag(s): ${d.types.join(", ") || "none"}`, rulings_drafted: () => `${d.length} ruling(s) drafted`,
      ranked: () => "QCBS ranking computed", report_written: () => "Evaluation report written", pipeline_complete: () => "Pipeline complete. Awaiting committee sign-off.",
      pipeline_error: () => `Error: ${d.error}`, session_created: () => "Session created",
    }[a];
    return m ? m() : a;
  };

  T.startRun = async (sid, settings) => {
    let r;
    try { r = await T.api.post(`/api/sessions/${sid}/run`, { settings }); } catch (e) { return T.toast(e.message, "err", 6000); }
    T.attach(sid, r.from, r.mode, settings);
  };

  T.attach = (sid, from, mode, settings) => {
    const layer = document.getElementById("layer"), ov = document.createElement("div");
    ov.className = "overlay"; ov.id = "run-overlay";
    ov.innerHTML = `<div class="runcard"><div class="rhead"><div class="orb" id="r-orb"></div><div class="grow"><h2 id="r-title" style="font-size:21px">Convening the committee…</h2>
        <div class="small" style="opacity:.8" id="r-sub">${mode === "groq" ? "Calling " + T.esc(settings?.model || "gpt-oss") + " on Groq" : "Running on the offline demo engine (no API key)"}</div></div><span class="pill navy" style="background:rgba(255,255,255,.15)" id="r-pct">0%</span></div>
      <div class="rbody"><div class="rsteps">${STAGES.map(([id, l], i) => `<div class="rstep" data-s="${id}"><div class="rn">${i + 1}</div><div><div class="rt">${l}</div><div class="rs"></div></div></div>`).join("")}</div>
      <div class="term" id="r-term"><div class="ln"><span class="tg">system</span><span>Connecting to the evaluation stream<span class="caret"></span></span></div></div></div>
      <div class="rfoot"><div class="bar-track"><div class="bar-fill" id="r-bar" style="width:0"></div></div><button class="btn primary" id="r-close" hidden>Open dashboard ${icon("chevron", "sm").s}</button></div></div>`;
    layer.appendChild(ov);
    const term = ov.querySelector("#r-term"), bar = ov.querySelector("#r-bar"), pct = ov.querySelector("#r-pct");
    let last = -1, finished = false, done = 0;
    const close = async () => {
      T.state.session = await T.api.get(`/api/sessions/${sid}`); ov.classList.add("out");
      setTimeout(() => { ov.remove(); if (location.hash === "#/dashboard") T.render(); else location.hash = "#/dashboard"; }, 420);
    };
    const finish = (ok, msg) => {
      if (finished) return; finished = true;
      const orb = ov.querySelector("#r-orb"); orb.className = "orb " + (ok ? "done" : "err"); orb.innerHTML = ok ? `<svg class="chk" viewBox="0 0 24 24"><path d="M5 12l5 5 9-10"/></svg>` : icon("x").s;
      ov.querySelector("#r-title").textContent = ok ? "Evaluation complete" : "Evaluation failed";
      ov.querySelector("#r-sub").textContent = ok ? "All agents have reported. Opening the dashboard…" : msg;
      if (ok) { bar.style.width = "100%"; pct.textContent = "100%"; setTimeout(close, 1500); }
      else { const b = ov.querySelector("#r-close"); b.hidden = false; b.textContent = "Close"; b.onclick = () => { ov.remove(); T.api.get(`/api/sessions/${sid}`).then((s) => { T.state.session = s; T.render(); }); }; }
    };
    const handle = (e) => {
      if (e.i <= last) return; last = e.i;
      if (e.kind === "stage") {
        const el = ov.querySelector(`[data-s="${e.stage}"]`);
        if (el) {
          el.className = "rstep " + e.status; const rn = el.querySelector(".rn");
          if (e.status === "done") { rn.innerHTML = `<svg class="chk" viewBox="0 0 24 24"><path d="M5 12l5 5 9-10"/></svg>`; done++; el.querySelector(".rs").textContent = (e.summary || "") + (e.seconds ? ` · ${e.seconds.toFixed(1)}s` : ""); }
          else if (e.status === "error") { rn.innerHTML = icon("x", "sm").s; el.querySelector(".rs").textContent = e.summary || ""; }
          else if (e.status === "running") el.querySelector(".rs").textContent = "Working…";
        }
        const p = Math.round(done / STAGES.length * 100); bar.style.width = p + "%"; pct.textContent = p + "%";
      } else if (e.kind === "log") {
        const cls = /error/.test(e.action) ? "err" : /complete|ranked/.test(e.action) ? "ok" : "";
        term.querySelector(".caret")?.parentElement.parentElement.remove();
        const ln = document.createElement("div"); ln.className = "ln " + cls;
        ln.innerHTML = `<span class="tm">${new Date().toLocaleTimeString("en-IN", { hour12: false })}</span><span class="tg">${T.esc(e.agent)}</span><span>${T.esc(logText(e))}</span>`;
        term.appendChild(ln); while (term.children.length > 220) term.firstChild.remove(); term.scrollTop = term.scrollHeight;
      } else if (e.kind === "done") finish(true);
      else if (e.kind === "error") finish(false, e.message);
    };
    const poll = async () => {                                   // fallback if the event stream drops
      while (!finished) {
        await new Promise((r) => setTimeout(r, 1500));
        try { const s = await T.api.get(`/api/sessions/${sid}`); if (s.status === "complete") return finish(true); if (s.status === "error") return finish(false, s.error); } catch { /* keep trying */ }
      }
    };
    const es = new EventSource(`${T.apiBase}/api/sessions/${sid}/events?frm=${from}`);
    es.onmessage = (m) => { const e = JSON.parse(m.data); handle(e); if (e.kind === "done" || e.kind === "error") es.close(); };
    es.onerror = () => { if (!finished) { es.close(); poll(); } };
  };

  // ---------------------------------------------------------------- bootstrap
  async function boot() {
    T.icon && document.getElementById("brand-logo").insertAdjacentHTML("beforeend", T.icon("scale", "lg").s);
    try {
      T.state.health = await T.api.get("/api/health");
      T.state.session = await T.api.get("/api/sessions/latest");
    } catch (e) {
      document.getElementById("page").innerHTML = T.empty("Backend not reachable", e.message + " Start it with ./run.sh (or run.bat) and reload.").s; return;
    }
    window.addEventListener("hashchange", () => { T.drawer.close(true); T.render(); });
    if (!location.hash) location.hash = "#/dashboard"; else T.render();
    const S = T.state.session;
    if (S && S.status === "running") T.attach(S.id, 0, S.mode, S.settings);
  }
  boot();
})();

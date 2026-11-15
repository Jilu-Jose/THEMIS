/* T.H.E.M.I.S frontend utilities: safe HTML templating, icons, formatters, API, animations, toasts, drawer, markdown */
(function () {
  const T = (window.T = { pages: {}, state: { session: null, health: null, route: "dashboard" } });

  // ---------------------------------------------------------------- safe html templating
  class Raw { constructor(s) { this.s = s; } }
  T.esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  T.raw = (s) => new Raw(s);
  const val = (v) => (v instanceof Raw ? v.s : Array.isArray(v) ? v.map(val).join("") : v == null || v === false ? "" : T.esc(v));
  /** html`...` escapes every interpolation unless it is itself html`` / T.raw() output */
  T.html = (strs, ...vals) => new Raw(strs.reduce((o, s, i) => o + s + (i < vals.length ? val(vals[i]) : ""), ""));

  // ---------------------------------------------------------------- icons (stroke, 24px grid)
  const P = {
    scale: '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    dashboard: '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
    upload: '<path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.2"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/>',
    rubric: '<path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/>',
    compliance: '<path d="m9 11 3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    chart: '<path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/>',
    rupee: '<path d="M6 3h12"/><path d="M6 8h12"/><path d="m6 13 8.5 8"/><path d="M6 13h3"/><path d="M9 13c6.667 0 6.667-10 0-10"/>',
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    gavel: '<path d="m14 13-7.5 7.5a2.12 2.12 0 0 1-3-3L11 10"/><path d="m16 16 6-6"/><path d="m8 8 6-6"/><path d="m9 7 8 8"/><path d="m21 11-8-8"/>',
    award: '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
    file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    check: '<path d="M20 6 9 17l-5-5"/>', x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    lock: '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    eye: '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
    play: '<polygon points="6 3 20 12 6 21 6 3"/>',
    sparkles: '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    chevron: '<path d="m9 18 6-6-6-6"/>',
    trash: '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    printer: '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 9V3h12v6"/><rect width="12" height="8" x="6" y="14"/>',
    hash: '<path d="M4 9h16"/><path d="M4 15h16"/><path d="M10 3 8 21"/><path d="M16 3l-2 18"/>',
    cpu: '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  };
  T.icon = (n, cls = "") => T.raw(`<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${P[n] || ""}</svg>`);

  // ---------------------------------------------------------------- formatters
  T.inr = (n) => {
    if (n == null || isNaN(n)) return "-";
    let s = String(Math.round(n)); if (s.length <= 3) return s;
    let head = s.slice(0, -3), tail = s.slice(-3), parts = [];
    while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2); }
    if (head) parts.unshift(head);
    return parts.concat(tail).join(",");
  };
  T.rs = (n) => (n == null ? "-" : "₹" + T.inr(n));
  T.cr = (n) => (n == null ? "-" : "₹" + (n / 1e7).toFixed(2) + " Cr");
  T.lakh = (n) => (n == null ? "-" : "₹" + (n / 1e5).toFixed(1) + " L");
  T.num = (n, d = 1) => (n == null ? "-" : Number(n).toFixed(d).replace(/\.0+$/, ""));
  T.dt = (iso) => { try { return new Date(iso).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" }); } catch { return iso; } };
  T.tm = (iso) => { try { return new Date(iso).toLocaleTimeString("en-IN", { hour12: false }); } catch { return iso; } };
  T.short = (h, n = 10) => (h ? h.slice(0, n) + "…" + h.slice(-4) : "");
  T.pill = (kind, text, extra = "") => T.html`<span class="pill ${kind} ${extra}">${text}</span>`;

  // ---------------------------------------------------------------- API
  const base = (document.querySelector('meta[name="themis-api"]')?.content || "").replace(/\/$/, "");
  T.apiBase = base;
  async function call(method, url, body, isForm) {
    const opt = { method, headers: {} };
    if (body !== undefined) { if (isForm) opt.body = body; else { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); } }
    let r;
    try { r = await fetch(base + url, opt); } catch (e) { throw new Error("Cannot reach the T.H.E.M.I.S backend. Is it running?"); }
    if (!r.ok) {
      let msg = r.statusText;
      try { const j = await r.json(); msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch { /* ignore */ }
      throw new Error(msg);
    }
    return r.status === 204 ? null : r.json();
  }
  T.api = { get: (u) => call("GET", u), post: (u, b) => call("POST", u, b ?? {}), form: (u, f) => call("POST", u, f, true), del: (u) => call("DELETE", u) };

  // ---------------------------------------------------------------- toasts
  T.toast = (msg, kind = "info", ms = 3800) => {
    const el = document.createElement("div");
    el.className = "toast " + (kind === "ok" ? "ok" : kind === "err" ? "err" : "");
    el.innerHTML = `<span>${T.icon(kind === "err" ? "alert" : kind === "ok" ? "check" : "info").s}</span><span>${T.esc(msg)}</span>`;
    document.getElementById("toasts").appendChild(el);
    setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 320); }, ms);
  };

  // ---------------------------------------------------------------- animations
  T.ease = (t) => 1 - Math.pow(1 - t, 3);
  T.animate = (root) => {
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    root.querySelectorAll(".stagger").forEach((c) => [...c.children].forEach((el, i) => el.style.setProperty("--i", i)));
    root.querySelectorAll("[data-i]").forEach((el) => el.style.setProperty("--i", el.dataset.i));
    root.querySelectorAll("[data-count]").forEach((el) => {
      const to = parseFloat(el.dataset.count), dec = +(el.dataset.dec || 0), pre = el.dataset.pre || "", suf = el.dataset.suf || "";
      if (reduce || isNaN(to)) { el.textContent = pre + to.toFixed(dec) + suf; return; }
      const t0 = performance.now(), dur = 1000;
      const tick = (now) => {
        const p = Math.min(1, (now - t0) / dur);
        el.textContent = pre + (to * T.ease(p)).toFixed(dec) + suf;
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
    requestAnimationFrame(() => requestAnimationFrame(() => {
      root.querySelectorAll("[data-w]").forEach((el) => (el.style.width = el.dataset.w + "%"));
      root.querySelectorAll("[data-h]").forEach((el) => (el.style.height = el.dataset.h + "%"));
      root.querySelectorAll("[data-dash]").forEach((el) => el.setAttribute("stroke-dasharray", el.dataset.dash));
    }));
    root.querySelectorAll(".btn").forEach((b) => {
      if (b._rip) return; b._rip = true;
      b.addEventListener("pointerdown", (e) => {
        const r = b.getBoundingClientRect(), s = document.createElement("span"), d = Math.max(r.width, r.height);
        s.className = "rip"; s.style.cssText = `width:${d}px;height:${d}px;left:${e.clientX - r.left - d / 2}px;top:${e.clientY - r.top - d / 2}px`;
        b.appendChild(s); setTimeout(() => s.remove(), 650);
      });
    });
  };

  // ---------------------------------------------------------------- drawer
  T.drawer = {
    open(content, onMount) {
      T.drawer.close(true);
      const layer = document.getElementById("layer"), wrap = document.createElement("div");
      wrap.id = "drawer-wrap";
      wrap.innerHTML = `<div class="scrim"></div><aside class="drawer">${content.s}</aside>`;
      layer.appendChild(wrap);
      wrap.querySelector(".scrim").onclick = () => T.drawer.close();
      wrap.querySelectorAll("[data-close]").forEach((b) => (b.onclick = () => T.drawer.close()));
      T.animate(wrap); onMount && onMount(wrap);
    },
    close(instant) {
      const w = document.getElementById("drawer-wrap"); if (!w) return;
      if (instant) return w.remove();
      w.querySelector(".drawer").classList.add("closing"); w.querySelector(".scrim").style.animation = "fadeOut .3s forwards";
      setTimeout(() => w.remove(), 300);
    },
  };

  // ---------------------------------------------------------------- tiny markdown renderer (input is escaped first)
  T.md = (src) => {
    const inline = (s) => T.esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/(^|[\s(])_(.+?)_(?=[\s).,]|$)/g, "$1<i>$2</i>").replace(/`(.+?)`/g, "<code>$1</code>");
    const lines = (src || "").split("\n"), out = []; let i = 0;
    while (i < lines.length) {
      const l = lines[i];
      if (/^\s*$/.test(l)) { i++; continue; }
      let m;
      if ((m = l.match(/^(#{1,3})\s+(.*)$/))) { out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`); i++; continue; }
      if (/^\|.*\|\s*$/.test(l) && /^\|[\s:|-]+\|\s*$/.test(lines[i + 1] || "")) {
        const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
        const head = cells(l); i += 2; const rows = [];
        while (i < lines.length && /^\|.*\|\s*$/.test(lines[i])) rows.push(cells(lines[i++]));
        out.push(`<div class="scroll-x"><table><thead><tr>${head.map((h) => `<th>${inline(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`);
        continue;
      }
      if (/^\s*[-*]\s+/.test(l)) {
        const items = [];
        while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) { const lv = lines[i].match(/^\s*/)[0].length >= 2 ? 1 : 0; items.push({ lv, t: lines[i].replace(/^\s*[-*]\s+/, "") }); i++; }
        out.push("<ul>" + items.map((it) => `<li style="margin-left:${it.lv * 18}px">${inline(it.t)}</li>`).join("") + "</ul>"); continue;
      }
      if (/^---+\s*$/.test(l)) { out.push("<hr>"); i++; continue; }
      const para = [l]; i++;
      while (i < lines.length && !/^\s*$/.test(lines[i]) && !/^(#{1,3}\s|\||\s*[-*]\s)/.test(lines[i])) para.push(lines[i++]);
      out.push(`<p>${inline(para.join(" "))}</p>`);
    }
    return T.raw(out.join(""));
  };

  // ---------------------------------------------------------------- shared domain helpers
  T.S = () => T.state.session;
  T.label = (S, b) => (S.identities_revealed || !S.settings.blind_technical ? b : S.aliases[b] || b);
  T.statusPill = (code, label) => {
    const k = { QUALIFIED: "green", DISQUALIFIED_ELIGIBILITY: "red", DISQUALIFIED_COMMITTEE: "red", PENDING_DISQUALIFICATION: "amber", TECH_NOT_QUALIFIED: "gray" }[code] || "gray";
    return T.pill(k, label || code, "dot");
  };
  T.actionPill = (a) => T.pill({ NO_ACTION: "green", REQUEST_CLARIFICATION: "amber", PENALIZE_10: "amber", PENALIZE_25: "red", RECOMMEND_DISQUALIFY: "red" }[a] || "gray", (a || "-").replaceAll("_", " "));
  T.riskOf = (S, b) => {
    const ds = S.decisions.filter((d) => d.bidders.includes(b)); if (!ds.length) return { lvl: "None", cls: "gray", n: 0 };
    const w = { NO_ACTION: 1, REQUEST_CLARIFICATION: 2, PENALIZE_10: 3, PENALIZE_25: 4, RECOMMEND_DISQUALIFY: 5 };
    let top = "NO_ACTION"; ds.forEach((d) => { const h = d.human?.[b]; const a = h?.decision === "override" ? h.action : d.actions[b]; if (w[a] > w[top]) top = a; });
    const n = ds.length, lvl = w[top] >= 4 ? "High" : w[top] >= 2 ? "Medium" : "Low";
    return { lvl, n, cls: lvl === "High" ? "red" : lvl === "Medium" ? "amber" : "green" };
  };
  T.officer = () => { try { return localStorage.getItem("themis.officer") || ""; } catch { return ""; } };
  T.setOfficer = (n) => { try { localStorage.setItem("themis.officer", n); } catch { /* ignore */ } };
  T.empty = (title, text, btn) => T.html`<div class="card empty rise"><div class="orb2">${T.icon("scale", "lg")}</div><h2>${title}</h2><p>${text}</p>${btn || ""}</div>`;
  T.head = (title, sub, actions) => T.html`<div class="page-head rise"><div class="grow"><h1>${title}</h1><p>${sub}</p></div><div class="row wrap no-print">${actions || ""}</div></div>`;
  T.needsRun = (S) => (!S ? T.empty("No evaluation yet", "Load the demo tender or upload your own documents to convene the committee.", T.html`<a class="btn primary lg" href="#/intake">${T.icon("upload")} New evaluation</a>`)
    : !S.rubric ? T.empty(S.status === "running" ? "The committee is in session…" : "Evaluation not run yet", S.status === "running" ? "Results appear here as each agent finishes." : "Documents are staged. Start the evaluation to generate results.", T.html`<a class="btn primary lg" href="#/intake">${T.icon("play")} Go to intake</a>`) : null);
})();

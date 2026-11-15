"""Orchestrator: runs the committee stage by stage and streams progress through the session event log."""
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from . import config
from .agents import chair, compliance, financial, parser, report, risk, scoring, technical
from .llm import LLM
from .state import Session, store


def _timed(s: Session, sid: str, fn):
    """Run one stage: mark running, time it, mark done with the summary fn() returns."""
    s.set_stage(sid, "running", "Working...")
    t0 = time.time()
    summary = fn()
    s.set_stage(sid, "done", summary, time.time() - t0)


def run_pipeline(s: Session):
    try:
        with s.lock:
            s.status, s.error = "running", None
            s.reset_results()
            s.approval, s.human_actions = None, []
        s.emit("started")
        llm = LLM(s.mode, s.settings["model"], s.settings["reasoning_effort"], on_event=s.add_audit)
        s.add_audit("System", "pipeline_started", {
            "mode": s.mode, "model": s.settings["model"],
            "bids": list(s.bids), "tender_sha256": s.tender["sha256"], "settings": s.settings})
        names = list(s.bids)
        s.aliases = technical.make_aliases(names)
        pool = lambda: ThreadPoolExecutor(max_workers=4)

        # 1 ---- tender parser
        def do_parser():
            s.rubric = parser.run(llm, s.tender["text"])
            s.add_audit("TenderParser", "rubric_extracted", {"eligibility": len(s.rubric["eligibility"]),
                                                             "technical": len(s.rubric["technical"])})
            return f"{len(s.rubric['eligibility'])} eligibility · {len(s.rubric['technical'])} technical criteria"
        _timed(s, "parser", do_parser)

        # 2 ---- compliance
        def do_compliance():
            with pool() as ex:
                res = list(ex.map(lambda n: compliance.run(llm, s.rubric, n, s.bids[n]["text"]), names))
            s.compliance = {r["bidder"]: r for r in res}
            for r in res:
                s.add_audit("Compliance", "verdict", {"bidder": r["bidder"], "verdict": r["verdict"]})
            ok = sum(1 for r in res if r["verdict"] != "DISQUALIFIED")
            return f"{ok}/{len(res)} bids eligible"
        _timed(s, "compliance", do_compliance)
        in_play = [n for n in names if s.compliance[n]["verdict"] != "DISQUALIFIED"]

        # 3 ---- technical (blind)
        def do_technical():
            blind = bool(s.settings["blind_technical"])
            with pool() as ex:
                res = list(ex.map(lambda n: technical.run(llm, s.rubric, n, s.aliases[n], s.bids[n]["text"], blind), in_play))
            s.technical = {r["bidder"]: r for r in res}
            for r in res:
                s.add_audit("Technical", "scored", {"bidder": s.aliases[r["bidder"]] if blind else r["bidder"], "raw_score": r["raw_score"]})
            q = sum(1 for r in res if r["raw_score"] >= s.rubric["min_technical_score"])
            return f"{len(res)} scored {'blind' if blind else 'openly'} · {q} above cut-off"
        _timed(s, "technical", do_technical)
        fin_names = [n for n in in_play if s.technical[n]["raw_score"] >= s.rubric["min_technical_score"]]

        # 4 ---- financial (envelopes opened only for technically qualified bidders)
        def do_financial():
            with pool() as ex:
                res = list(ex.map(lambda n: financial.run(llm, n, s.bids[n]["text"]), fin_names))
            s.financial = {r["bidder"]: r for r in res}
            issues = sum(len(r["flags"]) for r in res)
            for r in res:
                s.add_audit("Financial", "verified", {"bidder": r["bidder"], "recomputed_total": r["recomputed_total"], "flags": len(r["flags"])})
            return f"{len(res)} price schedules re-computed · {issues} issue(s)"
        _timed(s, "financial", do_financial)

        # 5 ---- risk / fraud
        def do_risk():
            s.risk_flags = risk.run(llm, s.bids, in_play, s.financial, s.settings)
            s.add_audit("Risk", "flags_raised", {"count": len(s.risk_flags), "types": [f["type"] for f in s.risk_flags]})
            high = sum(1 for f in s.risk_flags if f["severity"] == "HIGH")
            return f"{len(s.risk_flags)} flag(s) · {high} high severity"
        _timed(s, "risk", do_risk)

        # 6 ---- chair
        def do_chair():
            s.decisions = chair.run(llm, s.risk_flags, s.compliance, s.technical)
            s.add_audit("Chair", "rulings_drafted", [{"type": d["flag_type"], "actions": d["actions"]} for d in s.decisions])
            return f"{len(s.decisions)} ruling(s) drafted"
        _timed(s, "chair", do_chair)

        # 7 ---- QCBS scoring
        def do_scoring():
            s.ranking = scoring.run(s.rubric, s.compliance, s.technical, s.financial, s.decisions)
            win = next((r for r in s.ranking if r["rank"] == 1), None)
            s.add_audit("Scoring", "ranked", [{"rank": r["rank"], "bidder": r["bidder"], "status": r["status"], "final": r["final_score"]} for r in s.ranking])
            return f"L1 recommendation: {win['bidder']} ({win['final_score']})" if win else "No qualified bidder"
        _timed(s, "scoring", do_scoring)

        # 8 ---- report
        def do_report():
            s.report_md = report.run(llm, s)
            s.report_stale = False
            s.add_audit("Report", "report_written", {"chars": len(s.report_md)})
            return "Evaluation report written"
        _timed(s, "report", do_report)

        s.agent_stats = llm.stats
        s.set_stage("approval", "pending", "Awaiting committee sign-off")
        with s.lock:
            s.status = "complete"
        s.add_audit("System", "pipeline_complete", {"blockers": scoring.blockers(s.decisions)})
        store.save(s)
        s.emit("done")
    except Exception as e:                                        # noqa: BLE001
        traceback.print_exc()
        with s.lock:
            s.status, s.error = "error", f"{type(e).__name__}: {e}"
            for st in s.stages:
                if st["status"] == "running":
                    st["status"], st["summary"] = "error", str(e)[:160]
        s.add_audit("System", "pipeline_error", {"error": s.error})
        s.emit("error", message=s.error)
        store.save(s)

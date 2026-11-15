#!/usr/bin/env python
"""
THEMIS Synthetic Benchmark — 5 tenders, 3-4 synthetic bids each, known winners and disqualifications.

Usage:
    python benchmark.py                  # runs full 5-tender benchmark with Groq
    python benchmark.py --tender 1       # runs only Tender 1
    python benchmark.py --output out.json

Reports:
  - Per-tender: top-ranked bid vs. known winner (match / mismatch)
  - Per-tender: each planted disqualification and whether the system caught it with clause citation
  - Summary: accuracy % for winner prediction and DQ detection
"""
import argparse
import json
import sys
import time
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.demo_data import build_demo, TENDER_TEXT as TENDER_1_TEXT
from app.benchmark_data import build_benchmark_data
from app.documents import sha256_bytes
from app.pipeline import run_pipeline
from app.state import Session, store


def create_tender_session(tender_text: str, bids_list: list) -> Session:
    """Create a Session object initialized with tender document and bids."""
    s = Session()
    raw_tender = tender_text.encode("utf-8")
    s.tender = {
        "filename": "tender_notice.md",
        "sha256": sha256_bytes(raw_tender),
        "words": len(tender_text.split()),
        "text": tender_text,
    }
    for b in bids_list:
        raw_bid = b["text"].encode("utf-8")
        s.bids[b["name"]] = {
            "filename": b.get("filename", f"{b['name']}.md"),
            "sha256": sha256_bytes(raw_bid),
            "words": len(b["text"].split()),
            "text": b["text"],
            "submitted_at": b.get("submitted_at", "2026-10-01 10:00"),
        }
    store.add(s)
    return s


def run_benchmark_tender(tender_name: str, tender_text: str, bids_list: list, known_winner: str, known_dq: list) -> dict:
    """Execute evaluation pipeline for one tender and report findings."""
    print("\n" + "=" * 70)
    print(f"EVALUATING: {tender_name}")
    print(f"Total Bidders ({len(bids_list)}): {', '.join(b['name'] for b in bids_list)}")
    print(f"Expected Winner   : {known_winner}")
    print(f"Expected DQ Target: {', '.join(known_dq) if known_dq else 'None'}")
    print("=" * 70)

    s = create_tender_session(tender_text, bids_list)
    start_time = time.time()
    run_pipeline(s)
    elapsed = round(time.time() - start_time, 2)

    if s.status == "error":
        print(f"  [!] PIPELINE FAILED: {s.error}")
        return {
            "tender": tender_name,
            "status": "error",
            "error": s.error,
            "elapsed_seconds": elapsed,
            "winner_match": False,
            "all_dq_caught": False,
        }

    # Find ranked #1 eligible bidder
    top_rank = next((r for r in s.ranking if r.get("rank") == 1), None)
    predicted_winner = top_rank["bidder"] if top_rank else None
    winner_matched = (predicted_winner == known_winner)

    # Check disqualifications
    dq_results = {}
    dq_details = {}
    for dq_name in known_dq:
        comp = s.compliance.get(dq_name, {})
        verdict = comp.get("verdict")
        caught = (verdict == "DISQUALIFIED")
        dq_results[dq_name] = caught
        # Gather failing criteria and cited reason
        failed_checks = [c for c in comp.get("checks", []) if c.get("status") == "FAIL"]
        dq_details[dq_name] = {
            "verdict": verdict,
            "failed_criteria": [f"{c['id']}: {c['reason']}" for c in failed_checks]
        }

    # Check for any unexpected false positive disqualifications
    all_dqs = [name for name, c in s.compliance.items() if c.get("verdict") == "DISQUALIFIED"]

    print(f"\n  [RESULTS FOR {tender_name}]")
    print(f"  Elapsed Time     : {elapsed}s")
    print(f"  Predicted Winner : {predicted_winner} (Technical: {top_rank.get('tech_raw', '-')} | Price: INR {top_rank.get('price', '-'):,})")
    print(f"  Expected Winner  : {known_winner}")
    print(f"  Winner Accuracy  : {'[PASS] MATCH' if winner_matched else '[FAIL] MISMATCH'}")

    print("\n  Compliance Scrutiny & Disqualification Audit:")
    for dq_name, caught in dq_results.items():
        info = dq_details[dq_name]
        status_sym = "[PASS] CAUGHT" if caught else "[FAIL] MISSED"
        print(f"    {status_sym} Expected DQ '{dq_name}' -> System Verdict: {info['verdict']}")
        for fc in info["failed_criteria"]:
            print(f"      - Clause Failure: {fc}")

    print(f"\n  All Bidder Verdicts:")
    for b_name in s.bids:
        c_verdict = s.compliance.get(b_name, {}).get("verdict", "UNKNOWN")
        r_entry = next((r for r in s.ranking if r.get("bidder") == b_name), None)
        r_rank = f"Rank #{r_entry['rank']}" if r_entry and r_entry.get("rank") else "Unranked/DQ"
        print(f"    * {b_name:<36} | {c_verdict:<18} | {r_rank}")

    return {
        "tender": tender_name,
        "status": "success",
        "elapsed_seconds": elapsed,
        "predicted_winner": predicted_winner,
        "known_winner": known_winner,
        "winner_match": winner_matched,
        "known_dq": known_dq,
        "dq_results": dq_results,
        "dq_details": dq_details,
        "all_disqualified": all_dqs,
        "all_dq_caught": all(dq_results.values()) if dq_results else True,
        "ranking": s.ranking,
    }


def main():
    parser = argparse.ArgumentParser(description="THEMIS 5-Tender Synthetic Evaluation Benchmark")
    parser.add_argument("--tender", type=int, default=0, help="Run single tender index (1 to 5), 0 for all")
    parser.add_argument("--output", type=str, default="", help="Path to write JSON benchmark report")
    args = parser.parse_args()

    # Load 5 tenders
    demo_tender, demo_bids = build_demo()
    benchmarks_2_to_5 = build_benchmark_data()

    tenders = [
        (
            "Tender 1: IoT Water Quality Monitoring (Punjab PHED)",
            demo_tender,
            demo_bids,
            "SecureFlow Technologies Pvt Ltd",
            ["HydroNova Systems Pvt Ltd"],
        )
    ]
    for i, (t_text, b_list, kw, kdq) in enumerate(benchmarks_2_to_5):
        names = [
            "Tender 2: Rural Road Construction (HP PWD)",
            "Tender 3: Citizen Services IT Portal (NIC)",
            "Tender 4: Medical Diagnostic Equipment (AIIMS)",
            "Tender 5: Rooftop Solar PV Systems (MNRE)",
        ]
        tenders.append((names[i], t_text, b_list, kw, kdq))

    if args.tender in range(1, 6):
        tenders = [tenders[args.tender - 1]]
    elif args.tender != 0:
        print(f"Invalid tender number: {args.tender}. Specify 1 to 5.")
        sys.exit(1)

    print("\n" + "#" * 70)
    print("STARTING THEMIS 5-TENDER SYNTHETIC BENCHMARK SUITE")
    print(f"Evaluating {len(tenders)} Tender(s) across multi-agent committee pipeline")
    print("#" * 70)

    results = []
    for t_name, t_text, b_list, kw, kdq in tenders:
        res = run_benchmark_tender(t_name, t_text, b_list, kw, kdq)
        results.append(res)

    # Summary calculations
    successful_runs = [r for r in results if r["status"] == "success"]
    total = len(successful_runs)
    winner_matches = sum(1 for r in successful_runs if r["winner_match"])
    total_dq_targets = sum(len(r["known_dq"]) for r in successful_runs)
    caught_dq_targets = sum(sum(1 for v in r["dq_results"].values() if v) for r in successful_runs)

    winner_pct = (winner_matches / total * 100) if total else 0
    dq_pct = (caught_dq_targets / total_dq_targets * 100) if total_dq_targets else 100

    print("\n" + "=" * 70)
    print("BENCHMARK EXECUTIVE SUMMARY")
    print("=" * 70)
    print(f"Tenders Evaluated         : {total}/{len(tenders)}")
    print(f"Top-Ranked Winner Accuracy: {winner_matches}/{total} ({winner_pct:.1f}%)")
    print(f"Non-Compliant DQ Detection: {caught_dq_targets}/{total_dq_targets} ({dq_pct:.1f}%)")
    print("-" * 70)

    for r in successful_runs:
        w_sym = "PASS" if r["winner_match"] else "FAIL"
        dq_sym = "PASS" if r["all_dq_caught"] else "FAIL"
        print(f"  * {r['tender']:<48} | Winner: [{w_sym}] | DQ Audit: [{dq_sym}]")

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(json.dumps({
            "summary": {
                "tenders_evaluated": total,
                "winner_accuracy_pct": round(winner_pct, 1),
                "winner_matches": winner_matches,
                "total_tenders": total,
                "dq_detection_pct": round(dq_pct, 1),
                "dq_caught": caught_dq_targets,
                "total_dq": total_dq_targets,
            },
            "results": results,
        }, indent=2, default=str), encoding="utf-8")
        print(f"\n[+] Detailed benchmark report saved to: {out_path.resolve()}")

    return 0 if (winner_pct == 100 and dq_pct == 100) else 1


if __name__ == "__main__":
    sys.exit(main())

"""
Bhujal — Command Line Interface
================================
Industry-grade CLI entry point for local hydro-climatic analysis,
safety veto verification, multi-agent evaluation, and server initiation.
"""

from __future__ import annotations

import argparse
import sys

from agent.orchestrator import LeadPlannerOrchestratorAgent
from agent.report_generator import create_report
from scoring import evaluate_site, get_all_villages, run_site_scenario


def cmd_list(args: argparse.Namespace) -> None:
    villages = get_all_villages()
    if getattr(args, "state", None):
        st_norm = args.state.strip().lower()
        villages = [v for v in villages if v.state.strip().lower() == st_norm]

    print(
        f"\nBhujal AOI: Priority Watersheds (Odisha, Madhya Pradesh, Jharkhand) — {len(villages)} Settlements"
    )
    print("-" * 88)
    print(
        f"{'ID':<13} {'Name':<16} {'District':<16} {'State':<18} {'Elev (m)':<10} {'Spring'}"
    )
    print("-" * 88)
    for v in villages:
        spring_str = "Yes" if v.has_spring else "No"
        elev_str = f"{v.elevation_m:.0f}" if v.elevation_m is not None else "N/A"
        print(
            f"{v.id:<13} {v.name:<16} {v.district:<16} {v.state:<18} {elev_str:<10} {spring_str}"
        )
    print("-" * 88)


def cmd_evaluate(args: argparse.Namespace) -> None:
    site = evaluate_site(args.site_id)
    if not site:
        print(f"Error: Site '{args.site_id}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"\nHydro-Climatic Evaluation: {site.village.name} ({site.village.id})")
    print(
        f"Block: {site.village.block} | District: {site.village.district} | State: {site.village.state}"
    )
    print("=" * 75)

    print("\n1. DETERMINISTIC SCORES:")
    for score in site.scores:
        print(
            f"  * {score.score_type.replace('_', ' ').title():<28}: {score.value:>5.1f}/100 [{score.score_class.value.upper()}]"
        )
        for d in score.drivers:
            print(
                f"      - {d.factor:<25}: weight {d.weight:.2f} -> contribution {d.contribution:>5.1f}"
            )

    print("\n2. GEOTECHNICAL SAFETY VETO:")
    status = site.safety.status.value if site.safety else "SAFE"
    print(f"  * Status: {status}")
    if site.safety and site.safety.rule_ids:
        print(f"  * Triggered Rules: {', '.join(site.safety.rule_ids)}")
        for r in site.safety.reasons:
            print(f"      - {r}")

    print("\n3. CIVIL INTERVENTIONS & INDICATIVE COSTS:")
    if site.recommendations:
        for rec in site.recommendations:
            cost_low = rec.cost_range_inr.get("low", 0)
            cost_high = rec.cost_range_inr.get("high", 0)
            print(
                f"  * {rec.intervention_name} (Suitability: {rec.suitability_score:.2f})"
            )
            print(
                f"      Cost Range: INR {cost_low:,.0f} - {cost_high:,.0f} | Labour: {rec.labour_days} MGNREGA person-days"
            )
    else:
        print("  * No civil structures cleared for construction.")
    print("=" * 75)


def cmd_simulate(args: argparse.Namespace) -> None:
    res = run_site_scenario(args.site_id, args.rainfall, args.intervention)
    if not res:
        print(f"Error: Site '{args.site_id}' not found.", file=sys.stderr)
        sys.exit(1)

    print(
        f"\nScenario Simulation for {args.site_id} (Rainfall: {args.rainfall:.2f}x Normal)"
    )
    print("-" * 75)
    for base, adj in zip(res.baseline_scores, res.adjusted_scores, strict=True):
        delta = adj.value - base.value
        print(
            f"  * {base.score_type:<24}: Baseline {base.value:>5.1f} -> Adjusted {adj.value:>5.1f} ({delta:>+5.1f} pts)"
        )
    print("-" * 75)


def cmd_report(args: argparse.Namespace) -> None:
    site_ids = [s.strip() for s in args.sites.split(",") if s.strip()]
    sites = [evaluate_site(sid) for sid in site_ids]
    valid_sites = [s for s in sites if s is not None]

    if not valid_sites:
        print("Error: No valid sites found to report on.", file=sys.stderr)
        sys.exit(1)

    orchestrator = LeadPlannerOrchestratorAgent()
    agent_res = orchestrator.execute({"sites": valid_sites})
    rpt = create_report(valid_sites, agent_res.summary, agent_res.narrative)
    print("\nAction Dossier Generated Successfully:")
    print(f"  * Report ID   : {rpt.report_id}")
    print(f"  * File Path   : data/reports/{rpt.report_id}.html")
    print(f"  * Sites Count : {rpt.site_count}")
    print(f"  * Summary     : {rpt.summary}\n")


def cmd_server(args: argparse.Namespace) -> None:
    import uvicorn

    print(f"Starting Bhujal FastAPI server on http://{args.host}:{args.port}...")
    uvicorn.run("backend.app:app", host=args.host, port=args.port, reload=args.reload)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bhujal",
        description="Bhujal Hydro-Climatic Decision Support System CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser(
        "list", help="List tracked villages in the Area of Interest"
    )
    p_list.add_argument(
        "--state",
        default=None,
        help="Filter settlements by state (e.g. Odisha, Madhya Pradesh, Jharkhand)",
    )
    p_list.set_defaults(func=cmd_list)

    # evaluate
    p_eval = subparsers.add_parser(
        "evaluate", help="Perform comprehensive evaluation of a site"
    )
    p_eval.add_argument("site_id", help="Site identifier (e.g., site_001)")
    p_eval.set_defaults(func=cmd_evaluate)

    # simulate
    p_sim = subparsers.add_parser("simulate", help="Run rainfall scenario simulation")
    p_sim.add_argument("site_id", help="Site identifier (e.g., site_001)")
    p_sim.add_argument(
        "--rainfall", type=float, default=1.0, help="Rainfall fraction (0.5 to 1.5)"
    )
    p_sim.add_argument(
        "--intervention",
        type=str,
        default=None,
        help="Intervention ID (e.g., check_dam)",
    )
    p_sim.set_defaults(func=cmd_simulate)

    # report
    p_rpt = subparsers.add_parser("report", help="Generate planning action dossier")
    p_rpt.add_argument(
        "--sites",
        default="site_001,site_002,site_003,site_004,site_005",
        help="Comma-separated site IDs",
    )
    p_rpt.set_defaults(func=cmd_report)

    # server
    p_srv = subparsers.add_parser("server", help="Launch FastAPI development server")
    p_srv.add_argument("--host", default="127.0.0.1", help="Bind host")
    p_srv.add_argument("--port", type=int, default=8000, help="Bind port")
    p_srv.add_argument(
        "--reload", action="store_true", help="Auto-reload on code change"
    )
    p_srv.set_defaults(func=cmd_server)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

"""
Bhujal — Command Line Interface
================================
Industry-grade CLI entry point for local hydro-climatic analysis,
safety veto verification, multi-agent evaluation, and server initiation.
"""

from __future__ import annotations

import argparse
import sys

from agent.dpr_generator import create_dpr_zip, generate_dpr_package
from agent.orchestrator import LeadPlannerOrchestratorAgent
from agent.participatory import ParticipatoryMonitoringAgent
from agent.report_generator import create_report
from scoring import (
    evaluate_site,
    generate_adaptation_pathway,
    generate_pathway_comparison,
    get_all_villages,
    run_site_scenario,
)


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


# ── Participatory Monitoring CLI ────────────────────────────────

def cmd_participatory_submit(args: argparse.Namespace) -> None:
    """Submit a community observation via text."""
    agent = ParticipatoryMonitoringAgent()
    result = agent.execute(
        {
            "text": args.text,
            "observer_id": args.observer_id,
            "observer_name": args.observer_name,
            "language_code": args.language,
        }
    )
    if result.get("success"):
        print("\n✓ Observation recorded successfully!")
        print(f"  Observation ID: {result['observation_id']}")
        print(f"  Site: {result['validated'].get('site_id', 'unknown')}")
        print(f"  Type: {result['validated'].get('observation_type', 'general')}")
        print(f"  Value: {result['validated'].get('value', 'N/A')} {result['validated'].get('unit', '')}")
        print(f"  Badge: {result['badge'].get('current_badge', 'Jal Mitra (Bronze)')}")
        print(f"  Message: {result['message']}")
    else:
        print(f"Error: {result.get('error', 'Processing failed')}", file=sys.stderr)
        sys.exit(1)


def cmd_participatory_leaderboard(args: argparse.Namespace) -> None:
    """Show community contributor leaderboard."""
    agent = ParticipatoryMonitoringAgent()
    leaderboard = agent.get_leaderboard(state=args.state, limit=args.limit)
    print(f"\n🏆 Jal Mitra Leaderboard (Top {args.limit})")
    if args.state:
        print(f"   State: {args.state}")
    print("-" * 80)
    print(f"{'Rank':<5} {'Name':<20} {'Village':<15} {'Contributions':<15} {'Badge'}")
    print("-" * 80)
    for entry in leaderboard:
        print(
            f"{entry['rank']:<5} {entry['observer_name']:<20} {entry['village']:<15} "
            f"{entry['contributions']:<15} {entry['badge']}"
        )
    print("-" * 80)


# ── Adaptation Pathways CLI ────────────────────────────────────

def cmd_pathways_generate(args: argparse.Namespace) -> None:
    """Generate adaptation pathway for a site."""
    pathway = generate_adaptation_pathway(
        args.site_id, args.scenario, args.base_rainfall
    )
    print(f"\n📈 Adaptation Pathway: {pathway.site_name} ({pathway.site_id})")
    print(f"   SSP Scenario: {pathway.ssp_scenario}")
    print(f"   Success Probability: {pathway.success_probability:.0%}")
    print(f"   Total Cost: ₹{pathway.total_cost_inr:,.0f} ({pathway.total_cost_inr/100000:.2f} Lakhs)")
    print(f"   Final Recharge: {pathway.final_recharge_score:.1f} | Stress: {pathway.final_stress_score:.1f} | Spring Risk: {pathway.final_spring_risk:.1f}")
    print("-" * 90)
    print(f"{'Period':<12} {'Rainfall':<10} {'Recharge':<10} {'Stress':<10} {'Spring':<10} {'Interventions':<30}")
    print("-" * 90)
    for step in pathway.steps:
        interventions = ", ".join(i["intervention_id"] for i in step.recommended_interventions) or "—"
        if step.decision_node:
            interventions += f" ⚠️ DECISION: {step.trigger_condition}"
        print(
            f"{step.period:<12} {step.rainfall_fraction:<10.2f} "
            f"{step.baseline_scores.get('recharge_score', 0):<10.1f} "
            f"{step.baseline_scores.get('heat_water_stress', 0):<10.1f} "
            f"{step.baseline_scores.get('spring_drying_index', 0):<10.1f} "
            f"{interventions:<30}"
        )
    print("-" * 90)


def cmd_pathways_compare(args: argparse.Namespace) -> None:
    """Compare pathways across SSP scenarios."""
    pathways = generate_pathway_comparison(args.site_id, args.scenarios.split(","))
    print(f"\n📊 Pathway Comparison: {args.site_id}")
    print("-" * 100)
    print(f"{'SSP Scenario':<15} {'Success %':<10} {'Total Cost (L)':<15} {'Final Recharge':<15} {'Final Stress':<15} {'Final Spring':<15}")
    print("-" * 100)
    for ssp, pathway in pathways.items():
        print(
            f"{ssp:<15} {pathway.success_probability:<10.0%} "
            f"{pathway.total_cost_inr/100000:<15.2f} "
            f"{pathway.final_recharge_score:<15.1f} "
            f"{pathway.final_stress_score:<15.1f} "
            f"{pathway.final_spring_risk:<15.1f}"
        )
    print("-" * 100)


# ── DPR Generator CLI ──────────────────────────────────────────

def cmd_dpr_generate(args: argparse.Namespace) -> None:
    """Generate DPR package for sites."""
    site_list = [s.strip() for s in args.sites.split(",") if s.strip()]
    if not site_list:
        print("Error: At least one site ID required.", file=sys.stderr)
        sys.exit(1)

    try:
        dpr = generate_dpr_package(site_list, args.name or None, args.pdf)
        zip_bytes = create_dpr_zip(dpr)

        output_path = args.output or f"{dpr.project_id}.zip"
        with open(output_path, "wb") as f:
            f.write(zip_bytes)

        print("\n📦 DPR Package Generated Successfully!")
        print(f"  Project ID: {dpr.project_id}")
        print(f"  Project Name: {dpr.project_name}")
        print(f"  Sites: {', '.join(s.village.name for s in dpr.sites)}")
        print(f"  Total Cost: ₹{dpr.manifest['total_cost_high_inr']:,.0f} ({dpr.manifest['total_cost_high_inr']/100000:.2f} Lakhs)")
        print(f"  Total Labour: {dpr.manifest['total_labour_days']:,} person-days")
        print(f"  Output: {output_path}")
        print(f"  Contents: DOCX, XLSX, KML{' + PDF' if dpr.pdf_bytes else ''}")

    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: DPR generation failed: {exc}", file=sys.stderr)
        sys.exit(1)


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

    # participatory
    p_part = subparsers.add_parser("participatory", help="Community monitoring commands")
    part_sub = p_part.add_subparsers(dest="part_command", required=True)

    p_part_submit = part_sub.add_parser("submit", help="Submit community observation")
    p_part_submit.add_argument("text", help="Observation text")
    p_part_submit.add_argument("--observer-id", required=True, help="Observer ID (phone/WhatsApp)")
    p_part_submit.add_argument("--observer-name", default="", help="Observer name")
    p_part_submit.add_argument("--language", default="en-IN", help="Language code (e.g., en-IN, hi-IN, or-IN)")
    p_part_submit.set_defaults(func=cmd_participatory_submit)

    p_part_lb = part_sub.add_parser("leaderboard", help="Show Jal Mitra leaderboard")
    p_part_lb.add_argument("--state", default=None, help="Filter by state")
    p_part_lb.add_argument("--limit", type=int, default=10, help="Number of entries")
    p_part_lb.set_defaults(func=cmd_participatory_leaderboard)

    # pathways
    p_path = subparsers.add_parser("pathways", help="Adaptation pathway commands")
    path_sub = p_path.add_subparsers(dest="path_command", required=True)

    p_path_gen = path_sub.add_parser("generate", help="Generate pathway for a site")
    p_path_gen.add_argument("site_id", help="Site identifier")
    p_path_gen.add_argument("--scenario", default="SSP2-4.5", help="SSP scenario (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5)")
    p_path_gen.add_argument("--base-rainfall", type=float, default=1.0, help="Baseline rainfall fraction")
    p_path_gen.set_defaults(func=cmd_pathways_generate)

    p_path_cmp = path_sub.add_parser("compare", help="Compare pathways across scenarios")
    p_path_cmp.add_argument("site_id", help="Site identifier")
    p_path_cmp.add_argument("--scenarios", default="SSP1-2.6,SSP2-4.5,SSP3-7.0,SSP5-8.5", help="Comma-separated SSP scenarios")
    p_path_cmp.set_defaults(func=cmd_pathways_compare)

    # dpr
    p_dpr = subparsers.add_parser("dpr", help="DPR generation commands")
    dpr_sub = p_dpr.add_subparsers(dest="dpr_command", required=True)

    p_dpr_gen = dpr_sub.add_parser("generate", help="Generate DPR package")
    p_dpr_gen.add_argument("--sites", required=True, help="Comma-separated site IDs")
    p_dpr_gen.add_argument("--name", default="", help="Project name")
    p_dpr_gen.add_argument("--output", default="", help="Output ZIP path")
    p_dpr_gen.add_argument("--pdf", action="store_true", help="Include PDF (requires weasyprint)")
    p_dpr_gen.set_defaults(func=cmd_dpr_generate)

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
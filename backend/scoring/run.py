"""
Bhujal — Scoring Execution Runner
==================================
Runs deterministic scoring and safety evaluations across all demo sites.
Executed via `make score` or `python -m scoring.run`.
"""

from __future__ import annotations

from scoring.engine import evaluate_site, get_all_villages


def main() -> None:
    villages = get_all_villages()
    print(
        f"\nExecuting deterministic scoring across {len(villages)} demonstration sites..."
    )
    print("=" * 80)
    print(
        f"{'Site ID':<10} {'Name':<16} {'Safety':<12} {'Recharge':<10} {'Stress':<10} {'Spring Drying'}"
    )
    print("-" * 80)

    for v in villages:
        site = evaluate_site(v.id)
        if not site:
            continue
        scores = {s.score_type: s.value for s in site.scores}
        safety = site.safety.status.value if site.safety else "SAFE"
        recharge = f"{scores.get('recharge_score', 0):.1f}"
        stress = f"{scores.get('heat_water_stress', 0):.1f}"
        spring = (
            f"{scores.get('spring_drying_index', 0):.1f}" if v.has_spring else "N/A"
        )

        print(
            f"{v.id:<10} {v.name:<16} {safety:<12} {recharge:<10} {stress:<10} {spring}"
        )

    print("=" * 80)
    print("Scoring run completed successfully.\n")


if __name__ == "__main__":
    main()

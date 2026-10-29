"""
Experiments: how often is the grounded direct mechanism strategyproof, and how
well does Theorem 5.4's odd-path condition predict it?

    python experiments.py                       # 1000 instances per attack probability
    python experiments.py --instances 2000 --seed 1

For every attack probability p, N random instances are drawn: 6-8 arguments, each
ordered pair (a, b) (self-attacks a->a included) is an attack with probability p,
and each argument is given to one of 3 agents uniformly at random (an agent may
end up with no arguments).  For each instance we record

  strategyproof        exhaustive check (Theorem 5.3 property)
  cond[...]            Theorem 5.4 condition, under four readings:
                         walk/path  x  distinct pairs only / alpha == beta allowed

and write everything to ``results/``.
"""

import argparse
import csv
import json
import os
import random
import time
from collections import Counter, defaultdict
from itertools import product

from argumentation import powerset
from strategic import (
    StrategicGame,
    _CachedMechanism,
    is_strategyproof,
    satisfies_theorem_5_4,
    utility,
)

AGENTS = 3
P_VALUES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
VARIANTS = {  # name -> kwargs for satisfies_theorem_5_4
    "walk_distinct": dict(mode="walk", include_same=False),
    "walk_same": dict(mode="walk", include_same=True),
    "path_distinct": dict(mode="path", include_same=False),
    "path_same": dict(mode="path", include_same=True),
    # the book's wording: types conflict-free (no self-attacks) AND no odd path between two arguments
    "book_path": dict(mode="path", include_same=False, require_conflict_free=True),
}
PRIMARY = "path_distinct"  # literal reading of the assignment: simple path between two distinct arguments


def random_game(rng, p, n_range=(6, 8), n_agents=AGENTS):
    n = rng.randint(*n_range)
    args = list(range(n))
    attacks = {(a, b) for a in args for b in args if rng.random() < p}
    owner = [rng.randrange(n_agents) for _ in args]
    return StrategicGame(attacks, [{a for a in args if owner[a] == k} for k in range(n_agents)])


# --------------------------------------------------------------------------- #
# Diagnostics: why is a Theorem-5.4-violating instance nevertheless strategyproof?
# --------------------------------------------------------------------------- #


def diagnose_violation(game, agent, alpha, beta):
    """Classify a violating pair (alpha, beta) of a strategyproof instance by
    comparing 'reveal everything' with 'hide alpha' against every opponent scenario.

      rescue_offset     : hiding alpha sometimes rescues beta (rejected -> accepted),
                          but the agent loses at least as much, so it never gains
      beta_hopeless     : beta is not accepted in ANY scenario, hidden alpha or not
                          (e.g. beta is self-attacking / always defeated by others)
      alpha_irrelevant  : beta's status is identical with and without alpha in every
                          scenario (the attack chain is cut or alpha is dead weight)
      hiding_hurts_beta : hiding alpha never rescues beta and sometimes un-accepts it
    """
    mech = _CachedMechanism(game.attacks)
    Ai = game.agent_arguments[agent]
    others = [j for j in range(game.n_agents) if j != agent]
    rescued = hurt = ever_in = False
    for combo in product(*(list(powerset(game.agent_arguments[j])) for j in others)):
        full = mech([*combo, Ai])
        hidden = mech([*combo, Ai - {alpha}])
        ever_in |= beta in full or beta in hidden
        if beta not in full and beta in hidden:
            rescued = True
            assert utility(game, agent, hidden) <= utility(game, agent, full)
        if beta in full and beta not in hidden:
            hurt = True
    if rescued:
        return "rescue_offset"
    if not ever_in:
        return "beta_hopeless"
    return "hiding_hurts_beta" if hurt else "alpha_irrelevant"


def describe(game):
    return {
        "attacks": sorted(game.attacks),
        "agents": [sorted(A) for A in game.agent_arguments],
    }


# --------------------------------------------------------------------------- #
# Main experiment
# --------------------------------------------------------------------------- #


def run(instances, seed, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(seed)
    rows = []
    notable = {v: {"cond_but_manipulable": [], "sp_but_cond_fails": []} for v in VARIANTS}
    reasons = {v: Counter() for v in VARIANTS}       # per instance: set of reasons over its violating pairs
    pair_reasons = {v: Counter() for v in VARIANTS}  # per violating (alpha, beta) pair
    started = time.time()

    for p in P_VALUES:
        for k in range(instances):
            game = random_game(rng, p)
            sp = bool(is_strategyproof(game, stop_at_first=True))
            row = {"id": len(rows), "p": p, "n_args": len(game.arguments), "strategyproof": sp}
            for name, kw in VARIANTS.items():
                cond = bool(satisfies_theorem_5_4(game, **kw))
                row[f"cond_{name}"] = cond
                if cond and not sp:
                    notable[name]["cond_but_manipulable"].append(
                        {"id": row["id"], "p": p, **describe(game)}
                    )
                if sp and not cond:
                    res = satisfies_theorem_5_4(game, **kw)
                    per_pair = [diagnose_violation(game, i, a, b) for i, a, b in res.violations]
                    pair_reasons[name].update(per_pair)
                    kinds = sorted(set(per_pair))
                    reasons[name]["+".join(kinds)] += 1
                    notable[name]["sp_but_cond_fails"].append(
                        {"id": row["id"], "p": p, "violations": res.violations,
                         "reasons": kinds, **describe(game)}
                    )
            rows.append(row)
        print(f"  p={p:g} done ({time.time() - started:.0f}s)", flush=True)

    # ---- raw data
    with open(os.path.join(out_dir, "instances.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # ---- summary
    summary = {"seed": seed, "instances_per_p": instances, "total": len(rows), "by_p": {}, "variants": {}}
    for p in P_VALUES:
        sub = [r for r in rows if r["p"] == p]
        summary["by_p"][p] = {
            "strategyproof": sum(r["strategyproof"] for r in sub) / len(sub),
            **{f"cond_{v}": sum(r[f"cond_{v}"] for r in sub) / len(sub) for v in VARIANTS},
        }
    for v in VARIANTS:
        tot = lambda f: sum(1 for r in rows if f(r))
        summary["variants"][v] = {
            "cond_holds": tot(lambda r: r[f"cond_{v}"]),
            "cond_holds_and_strategyproof": tot(lambda r: r[f"cond_{v}"] and r["strategyproof"]),
            "cond_holds_but_manipulable": tot(lambda r: r[f"cond_{v}"] and not r["strategyproof"]),
            "cond_fails_and_strategyproof": tot(lambda r: not r[f"cond_{v}"] and r["strategyproof"]),
            "cond_fails_and_manipulable": tot(lambda r: not r[f"cond_{v}"] and not r["strategyproof"]),
            "reasons_for_sp_but_cond_fails": dict(reasons[v]),
            "violating_pairs_by_reason": dict(pair_reasons[v]),
        }
    summary["strategyproof_total"] = sum(r["strategyproof"] for r in rows)

    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(out_dir, "notable_instances.json"), "w") as f:
        json.dump(notable, f, indent=1, default=list)
    return rows, summary, notable


def print_summary(summary):
    print(f"\n{summary['total']} instances, {summary['instances_per_p']} per p, seed {summary['seed']}")
    print("\nFraction strategyproof (and fraction satisfying the Thm 5.4 condition) by p")
    header = f"{'p':>5} {'strategyproof':>14} " + " ".join(f"{v:>14}" for v in VARIANTS)
    print(header)
    for p, d in summary["by_p"].items():
        print(f"{p:>5} {d['strategyproof']:>14.3f} " + " ".join(f"{d['cond_' + v]:>14.3f}" for v in VARIANTS))
    print("\nContingency (counts over all instances)")
    for v, d in summary["variants"].items():
        print(f"  [{v}] cond&SP={d['cond_holds_and_strategyproof']}  cond&manipulable={d['cond_holds_but_manipulable']}"
              f"  !cond&SP={d['cond_fails_and_strategyproof']}  !cond&manipulable={d['cond_fails_and_manipulable']}")
        if d["reasons_for_sp_but_cond_fails"]:
            print(f"      why SP though condition fails (per instance): {d['reasons_for_sp_but_cond_fails']}")
            print(f"      same, per violating pair:                      {d['violating_pairs_by_reason']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", type=int, default=1000, help="instances per attack probability p")
    ap.add_argument("--seed", type=int, default=2024)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    _, summary, _ = run(args.instances, args.seed, args.out)
    print_summary(summary)

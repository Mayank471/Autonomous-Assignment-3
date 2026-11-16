"""
Extra statistics for the report, computed by replaying the exact random instances of
``experiments.py`` (same seed, same generator, same order) -- no new randomness.

    python extra_stats.py        # writes results/extra_stats.json

  * grounded_empty_by_p     fraction of instances whose full-framework grounded extension is empty
  * self_attack_mean_by_p   mean number of self-attacking arguments
  * sp_by_n                 strategyproof fraction by number of arguments (from results/instances.csv)
  * gain_*                  size of the best manipulation on a 300-per-p subsample of the instances
                            (utility of the best response minus truthful utility, maximised over
                            agents and over the other agents' reports)
"""
import csv
import json
import random
from collections import Counter, defaultdict

from argumentation import grounded_extension
from experiments import P_VALUES, random_game
from strategic import is_strategyproof

SEED, PER_P, SUBSAMPLE = 2024, 3000, 300


def main():
    rng = random.Random(SEED)
    with open("results/instances.csv", newline="") as f:
        recorded = list(csv.DictReader(f))
    empty, selfatt, n_by_p = defaultdict(int), defaultdict(int), defaultdict(int)
    gains = defaultdict(Counter)      # p -> Counter of max gain (0 = strategyproof)
    gain_by_n = defaultdict(list)
    row = 0
    for p in P_VALUES:
        for k in range(PER_P):
            game = random_game(rng, p)
            rec = recorded[row]
            assert float(rec["p"]) == p and int(rec["n_args"]) == len(game.arguments), "replay mismatch"
            row += 1
            if not grounded_extension(game.framework()):
                empty[p] += 1
            selfatt[p] += sum((a, a) in game.attacks for a in game.arguments)
            n_by_p[p] += len(game.arguments)
            if k < SUBSAMPLE:
                res = is_strategyproof(game)
                g = max((c["best_utility"] - c["truthful_utility"] for c in res.counterexamples), default=0)
                assert (g == 0) == (rec["strategyproof"] == "True")
                gains[p][g] += 1
    sp_n = defaultdict(lambda: [0, 0])
    for rec in recorded:
        sp_n[int(rec["n_args"])][0] += rec["strategyproof"] == "True"
        sp_n[int(rec["n_args"])][1] += 1
    out = {
        "grounded_empty_by_p": {str(p): empty[p] / PER_P for p in P_VALUES},
        "self_attack_mean_by_p": {str(p): selfatt[p] / PER_P for p in P_VALUES},
        "sp_by_n": {str(n): {"strategyproof": a, "total": b, "fraction": a / b} for n, (a, b) in sorted(sp_n.items())},
        "gain_subsample_per_p": SUBSAMPLE,
        "gain_histogram_by_p": {str(p): dict(sorted(gains[p].items())) for p in P_VALUES},
    }
    with open("results/extra_stats.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

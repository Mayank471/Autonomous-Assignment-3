"""
Demonstration of the whole assignment.   python demo.py

Part 1 walks through every function of the argumentation engine on small
frameworks; Part 2 demonstrates the grounded direct mechanism, best responses,
the strategyproofness check, Theorem 5.4's condition (including cyclic graphs),
and finishes with a miniature version of the experiment (the full experiment is
``python experiments.py``).
"""

import random

from argumentation import (
    ArgumentationFramework as AF,
    acceptance_status,
    all_extensions,
    all_legal_labellings,
    characteristic_function,
    grounded_extension,
    is_admissible,
    is_complete,
    is_conflict_free,
    is_defended,
)
from book_examples import (
    AGENT_NAMES, example_5_10, example_5_11, figure_5_1, figure_5_2, figure_5_3,
)
from experiments import random_game
from strategic import (
    StrategicGame,
    best_responses,
    grounded_direct_mechanism,
    has_odd_simple_path,
    has_odd_walk,
    is_strategyproof,
    satisfies_theorem_5_4,
    utility,
)


def show(S):
    return "{" + ", ".join(sorted(map(str, S))) + "}"


def show_all(exts):
    return "[" + ", ".join(show(E) for E in exts) + "]" if exts else "[]  (none)"


def title(text):
    print("\n" + "=" * 78 + f"\n{text}\n" + "=" * 78)


# --------------------------------------------------------------------------- #
title("PART 1  -  the book's examples (Figures 5.1, 5.2, 5.3; Examples 5.5-5.9)")
for name, f in [("Figure 5.1", figure_5_1()), ("Figure 5.2", figure_5_2()), ("Figure 5.3", figure_5_3())]:
    ext = all_extensions(f)
    print(f"\n{name}: {f}")
    print(f"  grounded    : {show(ext['grounded'][0])}")
    for k in ("complete", "preferred", "stable", "semi-stable"):
        print(f"  {k:12}: {show_all(ext[k])}")
    print("  status      :", ", ".join(f"{a}: {acceptance_status(f, a)}" for a in sorted(f.arguments, key=str)))
f = figure_5_1()
print("\nFigure 5.1 grounded iteration  F(0) =", show(characteristic_function(f, set())),
      "  F^2(0) =", show(characteristic_function(f, characteristic_function(f, set()))))
print("Figure 5.2 legal labellings:")
for lab in all_legal_labellings(figure_5_2()):
    print("  ", {k: lab[k] for k in sorted(lab)})

# --------------------------------------------------------------------------- #
title("PART 1  -  items 1-5: the framework class and the basic notions")
af = AF.parse("a->b, b->c, c->d")
print("Framework:", af)
for S in [set(), {"a", "c"}, {"a", "b"}]:
    print(f"  conflict-free {show(S):10}: {is_conflict_free(af, S)}")
for a, S in [("c", {"a"}), ("c", set()), ("d", {"a"}), ("d", {"b"})]:
    print(f"  '{a}' defended by {show(S):6}: {is_defended(af, a, S)}")
for S in [set(), {"a"}, {"a", "c"}]:
    print(f"  F({show(S):8}) = {show(characteristic_function(af, S))}")
for S in [{"c"}, {"a"}, {"a", "c"}]:
    print(f"  {show(S):8} admissible: {str(is_admissible(af, S)):5}  complete: {is_complete(af, S)}")

# --------------------------------------------------------------------------- #
title("PART 1  -  item 6A-6C: grounded, complete, preferred, stable, semi-stable")
examples = {
    "Chain  a->b->c": "a->b, b->c",
    "Nixon diamond  a<->b": "a<->b",
    "Odd cycle  a->b->c->a": "a->b, b->c, c->a",
    "a<->b, b->c, c->c  (preferred != stable)": "a<->b, b->c, c->c",
    "Caminada: 3-cycle + mutual attack  (no stable, but semi-stable)": "a->b, b->c, c->a, c->d, d<->e",
}
for name, text in examples.items():
    f = AF.parse(text)
    ext = all_extensions(f)
    print(f"\n{name}\n  {f}")
    print(f"  grounded    : {show(ext['grounded'][0])}")
    for k in ("complete", "preferred", "stable", "semi-stable"):
        print(f"  {k:12}: {show_all(ext[k])}")

# --------------------------------------------------------------------------- #
title("PART 1  -  item 6D: all legal (in/out/undec) labellings")
f = AF.parse("a<->b, b->c, c->c")
print(f)
for lab in all_legal_labellings(f):
    print("  ", {k: lab[k] for k in sorted(lab)})

title("PART 1  -  item 6E: acceptance status (preferred semantics)")
f = AF.parse("a<->b, b->c, c->c, d")
print(f)
for a in sorted(f.arguments):
    print(f"  {a}: {acceptance_status(f, a)}")
print("  under stable semantics (only stable extension is {b, d}):")
for a in sorted(f.arguments):
    print(f"  {a}: {acceptance_status(f, a, 'stable')}")

# --------------------------------------------------------------------------- #
title("PART 2  -  the book's Examples 5.10 and 5.11")
g10, g11 = example_5_10(), example_5_11()
print("Example 5.10: x={1,4,5}, y={2}, z={3}, R={(1,2),(2,3),(3,4),(3,5)}")
o = grounded_direct_mechanism(g10.attacks, g10.agent_arguments)
print(f"  truthful outcome {show(o)};  utilities " +
      ", ".join(f"u_{AGENT_NAMES[i]} = {utility(g10, i, o)}" for i in range(3)) +
      "   (book misprint: it prints u_y(o,{3}) and u_z(o,{2}), the sets are swapped)")
o2 = grounded_direct_mechanism(g10.attacks, [{4, 5}, {2}, {3}])
print(f"  x withholds 1 -> outcome {show(o2)}, u_x = {utility(g10, 0, o2)}")
res = is_strategyproof(g10)
print(f"  strategyproof? {res.holds}; agents with a profitable deviation: {sorted({AGENT_NAMES[c['agent']] for c in res.counterexamples})}")
print(f"  Thm 5.4 condition (incl. conflict-free types): {satisfies_theorem_5_4(g10, require_conflict_free=True).holds}, "
      f"violations {satisfies_theorem_5_4(g10).violations}")
print("Example 5.11: add argument 6 to x and the defeat (6,3)")
o = grounded_direct_mechanism(g11.attacks, g11.agent_arguments)
print(f"  truthful outcome {show(o)};  u_x = {utility(g11, 0, o)}")
print(f"  strategyproof? {is_strategyproof(g11).holds}; Thm 5.4 condition: {satisfies_theorem_5_4(g11).holds} "
      f"(violations {satisfies_theorem_5_4(g11).violations}) -> sufficient, not necessary")
no6 = StrategicGame({(1, 2), (2, 3), (3, 4), (3, 5)}, [{1, 4, 5}, {2}, {3}])
no5 = StrategicGame({(1, 2), (2, 3), (3, 4), (6, 3)}, [{1, 4, 6}, {2}, {3}])
print(f"  without 6 strategyproof? {is_strategyproof(no6).holds};  without 5 strategyproof? {is_strategyproof(no5).holds}"
      "  -> the cancelling argument is 6 (the book's text says 5: erratum)")

# --------------------------------------------------------------------------- #
title("PART 2  -  the mechanism, best responses, strategyproofness")
attacks = {("al", "de"), ("de", "al"), ("al", "be")}
game = StrategicGame(attacks, [{"al", "be"}, {"de"}])
print("Agent 0 owns {al, be}; agent 1 owns {de}; attacks: al<->de, al->be")
for reports in [[{"al", "be"}, {"de"}], [{"be"}, {"de"}], [{"al"}, {"de"}], [{"al", "be"}, set()]]:
    out = grounded_direct_mechanism(attacks, reports)
    print(f"  reports {[show(r) for r in reports]!s:28} -> grounded {show(out)}")
br = best_responses(game, 0, {1: {"de"}})
print(f"\nBest responses of agent 0 against agent 1 revealing {{de}}: utility {br.utility}, "
      f"reports {[show(r) for r in br.reports]}")
res = is_strategyproof(game)
print(f"Strategyproof (truth dominant for every agent)? {res.holds}")
for c in res.counterexamples:
    print(f"   agent {c['agent']} vs {{ {', '.join(f'{j}: {show(r)}' for j, r in c['others_reports'].items())} }}: "
          f"truthful utility {c['truthful_utility']}, can reach {c['best_utility']} by revealing {[show(r) for r in c['best_reports']]}")
t = satisfies_theorem_5_4(game)
print(f"Theorem 5.4 condition holds? {t.holds}; violating (agent, alpha, beta): {t.violations}")

print("\nA strategyproof instance whose condition fails (hiding alpha just trades alpha for beta):")
g2 = StrategicGame({("al", "be")}, [{"al", "be"}, set(), set()])
print("  single agent with al->be:  strategyproof =", is_strategyproof(g2).holds,
      "  Theorem 5.4 condition =", satisfies_theorem_5_4(g2).holds)

print("\nA strategyproof instance whose condition holds (even path al->x->be through another agent):")
g3 = StrategicGame({("al", "x"), ("x", "be")}, [{"al", "be"}, {"x"}])
print("  strategyproof =", is_strategyproof(g3).holds, "  condition =", satisfies_theorem_5_4(g3).holds)

title("PART 2  -  item 4: odd-length paths in graphs with cycles")
cases = {
    "a->x, x->x, x->b (loop on x)": ({"a": {"x"}, "x": {"x", "b"}, "b": set()}, "a", "b"),
    "2-cycle a<->b, odd closed walk a~>a?": ({"a": {"b"}, "b": {"a"}}, "a", "a"),
    "3-cycle a->b->c->a, odd closed walk a~>a?": ({"a": {"b"}, "b": {"c"}, "c": {"a"}}, "a", "a"),
}
for name, (adj, s, d) in cases.items():
    print(f"  {name:44} odd walk: {str(has_odd_walk(adj, s, d)):5}  odd simple path: {has_odd_simple_path(adj, s, d)}")

# --------------------------------------------------------------------------- #
title("PART 2  -  miniature experiment (full run: python experiments.py)")
rng = random.Random(1)
print(f"{'p':>5} {'N':>5} {'strategyproof':>14} {'Thm5.4 holds':>13} {'holds&!SP':>10} {'SP&!holds':>10}")
for p in (0.1, 0.3, 0.5, 0.8):
    N = 150
    games = [random_game(rng, p) for _ in range(N)]
    sp = [bool(is_strategyproof(g, stop_at_first=True)) for g in games]
    cond = [bool(satisfies_theorem_5_4(g)) for g in games]
    print(f"{p:>5} {N:>5} {sum(sp) / N:>14.3f} {sum(cond) / N:>13.3f} "
          f"{sum(c and not s for c, s in zip(cond, sp)):>10} {sum(s and not c for c, s in zip(cond, sp)):>10}")

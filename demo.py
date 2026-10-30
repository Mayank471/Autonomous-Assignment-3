"""
Step-by-step demonstration of the whole assignment.

    python demo.py                  # run everything (about 1 minute)
    python demo.py --pause          # wait for Enter between steps (for a live presentation)
    python demo.py --instances 200  # smaller / faster experiment in step 17 (default 500 per p)

Every step is labelled with the assignment item it demonstrates.  Lines starting with
">>>" are the exact calls being executed (they are evaluated, not hard-coded), the
indented line below is the returned value.
"""

import argparse
import io
import random
import sys
import unittest

import argumentation as arg
from argumentation import ArgumentationFramework as AF
from book_examples import AGENT_NAMES, example_5_10, example_5_11, figure_5_1, figure_5_2, figure_5_3
from experiments import P_VALUES, diagnose_violation, random_game
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

PAUSE = False
STEP = 0


# --------------------------------------------------------------------------- #
# presentation helpers
# --------------------------------------------------------------------------- #


def fmt(v):
    """Readable rendering of the values the engine returns."""
    if isinstance(v, (set, frozenset)):
        return "{" + ", ".join(sorted(map(str, v))) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x) for x in v) + "]" if v else "[]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {fmt(x)}" for k, x in sorted(v.items(), key=lambda kv: str(kv[0]))) + "}"
    if isinstance(v, tuple):
        return "(" + ", ".join(fmt(x) for x in v) + ")"
    return str(v)


def part(text):
    print("\n" + "#" * 78 + f"\n#  {text}\n" + "#" * 78)


def step(item, title, note=""):
    """Start a numbered step; `item` says which assignment item it covers."""
    global STEP
    STEP += 1
    if PAUSE and STEP > 1:
        input("\n[press Enter for the next step] ")
    print(f"\n{'=' * 78}\nSTEP {STEP}  [{item}]  {title}\n{'=' * 78}")
    if note:
        print(note)


def ev(expr, env, shown=None):
    """Evaluate `expr`, print it as a call, print the result, return the result."""
    result = eval(expr, env)
    print(f">>> {shown or expr}\n      = {fmt(result)}")
    return result


def say(text):
    print(f"    -> {text}")


# --------------------------------------------------------------------------- #
# PART 1 - argumentation engine
# --------------------------------------------------------------------------- #


def part1():
    part("PART 1 - ARGUMENTATION ENGINE (all examples are taken from the book, Chapter 5)")

    f51, f52, f53 = figure_5_1(), figure_5_2(), figure_5_3()
    env = {**vars(arg), "af": f51, "S": None}

    step("Item 1", "The argumentation framework class",
         "Figure 5.1: alpha1 has two defeaters (2 and 4), which are defeated by 3 and 5 respectively.")
    print(">>> af = ArgumentationFramework({1,2,3,4,5}, {(3,2),(2,1),(5,4),(4,1)})")
    print(f"      = {f51}")
    ev("af.attackers_of(1)", env)
    ev("af.targets_of(3)", env)
    ev("af.attacked_by({3, 5})", env, "af.attacked_by({3, 5})        # S+ = everything attacked by the set")
    print(">>> ArgumentationFramework.parse('a->b, b->c')      # compact constructor")
    print(f"      = {AF.parse('a->b, b->c')}")

    step("Item 2", "Conflict-free test", "A set is conflict-free if no member attacks a member.")
    for S in ["set()", "{1, 3, 5}", "{3, 2}", "{2, 4}"]:
        ev(f"is_conflict_free(af, {S})", env)
    say("{3, 2} fails because 3 attacks 2; {2, 4} is fine (2 and 4 do not attack each other).")

    step("Item 3", "Can an argument be defended by S?",
         "S defends a when every attacker of a is itself attacked by a member of S.")
    ev("is_defended(af, 1, {3, 5})", env)
    ev("is_defended(af, 1, {3})", env)
    ev("is_defended(af, 1, set())", env)
    ev("is_defended(af, 3, set())", env)
    say("1 needs both 3 (kills 2) and 5 (kills 4); the unattacked arguments 3 and 5 are defended by the empty set.")

    step("Item 4", "Characteristic function F(S) = arguments defended by S")
    ev("characteristic_function(af, set())", env)
    ev("characteristic_function(af, {3, 5})", env)
    ev("characteristic_function(af, {1, 3, 5})", env)
    say("F(empty) = {3,5}, F({3,5}) = {1,3,5}, F({1,3,5}) = {1,3,5}: matches the book (p.184).")

    step("Item 5", "Admissible set and complete extension",
         "Admissible = conflict-free and defends all its members; complete = admissible and contains everything it defends.")
    for S in ["set()", "{3, 5}", "{1, 3, 5}", "{1}", "{2, 3}"]:
        a = eval(f"is_admissible(af, {S})", env)
        c = eval(f"is_complete(af, {S})", env)
        print(f">>> is_admissible(af, {S}), is_complete(af, {S})\n      = {a}, {c}")
    say("{3,5} is admissible but not complete (it defends 1 but does not contain it) - Example 5.6.")
    ev("admissible_sets(af)", env)
    say("exactly the admissible sets listed in Example 5.5.")

    step("Item 6A", "Grounded extension (least fixed point of F)")
    env["af"] = f51
    ev("grounded_extension(af)", env, "grounded_extension(af)           # Figure 5.1")
    S, k = set(), 0
    print("    iteration trace  F^k(empty):")
    while True:
        nxt = arg.characteristic_function(f51, S)
        k += 1
        print(f"      F^{k}(empty) = {fmt(nxt)}")
        if nxt == S:
            break
        S = nxt
    env["af"] = f53
    ev("grounded_extension(af)", env, "grounded_extension(af)           # Figure 5.3 (b->a, c->b, d->b, c<->d, e->d)")
    say("the book states {a, c, e} on p.188: e is unattacked, kills d, so c is reinstated, kills b, so a is defended.")

    step("Item 6B", "All complete extensions", "Figure 5.2: alpha1 <-> alpha2, alpha3 on its own.")
    env["af"] = f52
    print(f"    framework: {f52}")
    ev("complete_extensions(af)", env)
    say("three complete extensions {3}, {1,3}, {2,3} (Example 5.7).")

    step("Item 6C", "All extensions: grounded, preferred, stable, semi-stable")
    print("    Figure 5.2:")
    for name in ["grounded_extension", "preferred_extensions", "stable_extensions", "semi_stable_extensions"]:
        ev(f"{name}(af)", env)
    print("\n    A framework where the semantics differ:  a<->b, b->c, c->c")
    env["af"] = AF.parse("a<->b, b->c, c->c")
    ev("all_extensions(af)", env)
    say("preferred {a},{b}; only {b} is stable (it attacks a and c); semi-stable = {b}.")
    print("\n    A framework with no stable extension (odd cycle a->b->c->a):")
    env["af"] = AF.parse("a->b, b->c, c->a")
    ev("all_extensions(af)", env)

    step("Item 6D", "All legal in/out/undec labellings", "Figure 5.2 - the three labellings L^G, L1, L2 of the book (Fig. 5.2).")
    env["af"] = f52
    labs = arg.all_legal_labellings(f52)
    print(f"    {'argument':<10}" + "".join(f"labelling {i + 1:<4}" for i in range(len(labs))))
    for a in sorted(f52.arguments):
        print(f"    alpha{a:<5}  " + "".join(f"{lab[a]:<13}" for lab in labs))
    print("    in-sets:", ", ".join(fmt(arg.labelling_to_extension(lab)) for lab in labs), " (= the complete extensions)")
    ev("is_legal_labelling(af, {1: 'in', 2: 'in', 3: 'in'})", env)

    step("Item 6E", "Acceptance status of an argument (skeptical / credulous / rejected)")
    for name, f in [("Figure 5.2", f52), ("Figure 5.1", f51)]:
        print(f"    {name}  (preferred semantics):")
        for a in sorted(f.arguments):
            print(f"      argument {a}: {arg.acceptance_status(f, a)}")

    step("Test", "Run the full test-suite (book examples + random cross-checks)",
         "test_book_examples.py asserts every value the book states; test_engine.py cross-checks on 300 random AFs.")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite([loader.loadTestsFromName("test_book_examples"), loader.loadTestsFromName("test_engine")])
    buf = io.StringIO()
    res = unittest.TextTestRunner(stream=buf, verbosity=0).run(suite)
    print(f"    tests run: {res.testsRun}   failures: {len(res.failures)}   errors: {len(res.errors)}   "
          f"=> {'ALL PASS' if res.wasSuccessful() else 'FAILURES'}")


# --------------------------------------------------------------------------- #
# PART 2 - strategic argumentation
# --------------------------------------------------------------------------- #


def find_odd_simple_path(adj, src, dst):
    """Return one odd-length simple path src ~> dst (list of nodes) for display, or None."""

    def dfs(path):
        node = path[-1]
        for nxt in sorted(adj[node], key=str):
            if nxt == dst and len(path) % 2 == 1:      # len(path) edges so far + 1 is odd
                return path + [nxt]
            if nxt not in path and nxt != dst:
                found = dfs(path + [nxt])
                if found:
                    return found
        return None

    return dfs([src])


def part2():
    part("PART 2 - STRATEGIC ARGUMENTATION (grounded direct argumentation mechanism)")
    g10, g11 = example_5_10(), example_5_11()
    names = AGENT_NAMES

    step("Setup", "Book Example 5.10",
         "Three agents:  x owns {1,4,5},  y owns {2},  z owns {3}.   Defeats R = {(1,2), (2,3), (3,4), (3,5)}.\n"
         "Utility of an agent = number of ITS OWN arguments that end up accepted (acceptability maximiser).")
    print(f"    {g10}")

    step("Item 1", "The mechanism: grounded extension of the graph induced by the revealed arguments")
    env = {"grounded_direct_mechanism": grounded_direct_mechanism, "A": g10.attacks}
    o = ev("grounded_direct_mechanism(A, [{1,4,5}, {2}, {3}])", env, "grounded_direct_mechanism(R, [{1,4,5}, {2}, {3}])   # everybody truthful")
    for i in range(3):
        print(f"      u_{names[i]} = {utility(g10, i, o)}")
    say("outcome {1,3}: 1 wins, kills 2, so 3 is defended and kills 4 and 5.  u_x=1, u_y=0, u_z=1.")
    say("(book misprint: it prints u_y(o,{3})=1 and u_z(o,{2})=0 - the two argument sets are swapped.)")
    o = ev("grounded_direct_mechanism(A, [{4,5}, {2}, {3}])", env, "grounded_direct_mechanism(R, [{4,5}, {2}, {3}])   # x hides argument 1")
    print(f"      u_x = {utility(g10, 0, o)}")
    say("hiding 1 breaks the defeat chain 1->2->3->4,5: outcome {2,4,5}, so x now has 2 accepted arguments instead of 1.")

    step("Item 2", "Best responses: enumerate every subset x could reveal, others fixed")
    others = {1: frozenset({2}), 2: frozenset({3})}
    print("    other agents truthful: y reveals {2}, z reveals {3}.  All 2^3 = 8 reports of x and their utilities:")
    for rep in arg.powerset({1, 4, 5}):
        out = grounded_direct_mechanism(g10.attacks, [rep, others[1], others[2]])
        print(f"      x reveals {fmt(rep):<10} -> outcome {fmt(out):<12} u_x = {utility(g10, 0, out)}")
    br = best_responses(g10, 0, others)
    print(f">>> best_responses(game, x, {{y: {{2}}, z: {{3}}}})\n      = utility {br.utility}, reports {fmt(br.reports)}")
    say("x's unique best response is {4,5}: lying by omission pays.  Truthful {1,4,5} gives only 1.")
    for i in (1, 2):
        oth = {j: g10.agent_arguments[j] for j in range(3) if j != i}
        b = best_responses(g10, i, oth)
        print(f"    agent {names[i]} against truthful others: best utility {b.utility}, best reports {fmt(b.reports)}")
    say("for y and z the truthful report is among the best responses (book: it weakly dominates revealing nothing).")

    step("Item 3", "Theorem 5.3: is truth-telling the best response against EVERY combination of the others' subsets?")
    r = is_strategyproof(g10)
    print(f">>> is_strategyproof(Example 5.10)\n      = {r.holds}   ({len(r.counterexamples)} counterexamples)")
    c = r.counterexamples[0]
    print(f"    first counterexample: agent {names[c['agent']]}, others reveal "
          f"{ {names[j]: fmt(v) for j, v in c['others_reports'].items()} }, truthful utility {c['truthful_utility']}, "
          f"best achievable {c['best_utility']} by revealing {fmt(c['best_reports'])}")
    print(f"    agents with a profitable deviation: {sorted({names[c['agent']] for c in r.counterexamples})}")
    r11 = is_strategyproof(g11)
    print("\n    Book Example 5.11: add argument 6 (owned by x) and the defeat (6, 3):  x = {1,4,5,6}")
    o = grounded_direct_mechanism(g11.attacks, g11.agent_arguments)
    print(f">>> is_strategyproof(Example 5.11)\n      = {r11.holds}      (truthful outcome {fmt(o)}: x gets all 4 of its arguments accepted)")

    step("Item 4", "Theorem 5.4: does some agent hold alpha, beta with an odd-length directed path alpha ~> beta?",
         "If NO agent does, the mechanism is guaranteed strategyproof (sufficient condition).")
    adj = {a: set() for a in g10.arguments}
    for a, b in g10.attacks:
        adj[a].add(b)
    t = satisfies_theorem_5_4(g10)
    print(f">>> satisfies_theorem_5_4(Example 5.10)\n      = holds: {t.holds}, violations (agent, alpha, beta): "
          f"{[(names[i], a, b) for i, a, b in t.violations]}")
    for i, a, b in t.violations:
        p = find_odd_simple_path(adj, a, b)
        say(f"{names[i]} owns {a} and {b}; odd path {' -> '.join(map(str, p))} (length {len(p) - 1}).")
    say("so the condition cannot certify Example 5.10, and indeed it is manipulable.")
    t11 = satisfies_theorem_5_4(g11)
    print(f">>> satisfies_theorem_5_4(Example 5.11)\n      = holds: {t11.holds}, violations {[(names[i], a, b) for i, a, b in t11.violations]}")
    say("condition FAILS but the mechanism IS strategyproof (step above): the condition is sufficient, not necessary.")
    say("why: argument 6 defeats 3 whenever x reveals it, so 4 and 5 never depend on 1 - 6 'cancels' the indirect defeat.")

    print("\n    Handling cycles - parity search, so the check always terminates:")
    cases = [
        ("a->x, x->x (loop), x->b", {"a": {"x"}, "x": {"x", "b"}, "b": set()}, "a", "b"),
        ("2-cycle a<->b, odd closed path a~>a", {"a": {"b"}, "b": {"a"}}, "a", "a"),
        ("3-cycle a->b->c->a, odd closed path a~>a", {"a": {"b"}, "b": {"c"}, "c": {"a"}}, "a", "a"),
    ]
    print(f"      {'graph':<44}{'odd simple path':<18}odd walk (may repeat nodes)")
    for name, adjc, s, d in cases:
        print(f"      {name:<44}{str(has_odd_simple_path(adjc, s, d)):<18}{has_odd_walk(adjc, s, d)}")
    say("the loop example has an odd walk (a,x,x,b: length 3) but no odd simple path - the two readings are both implemented.")

    step("Misprints", "The two misprints of the book, verified by the code")
    no6 = StrategicGame({(1, 2), (2, 3), (3, 4), (3, 5)}, [{1, 4, 5}, {2}, {3}])
    no5 = StrategicGame({(1, 2), (2, 3), (3, 4), (6, 3)}, [{1, 4, 6}, {2}, {3}])
    print("    (1) Example 5.10 utilities: y owns {2} -> u_y = 0; z owns {3} -> u_z = 1 (the book swaps the argument sets).")
    print(f"    (2) Which argument cancels the indirect self-defeat in Example 5.11?")
    print(f"        remove 6: strategyproof? {is_strategyproof(no6).holds}   (x can gain again)")
    print(f"        remove 5: strategyproof? {is_strategyproof(no5).holds}    (still dominant)")
    say("so it is argument 6, not 5 (5 defeats nothing and cannot influence anyone).")


# --------------------------------------------------------------------------- #
# EXPERIMENTS
# --------------------------------------------------------------------------- #


def experiments(n_per_p, seed=2024):
    part("EXPERIMENTS - random instances (3 agents, 6-8 arguments, attack probability p)")
    step("Setup", "How the instances are generated and checked",
         f"For each p in {P_VALUES}: {n_per_p} random instances.  6, 7 or 8 arguments; every ordered pair (a,b)\n"
         "is an attack with probability p; each argument goes to one of 3 agents uniformly at random.\n"
         "For each instance: strategyproof? (exhaustive check, item 3)   Theorem 5.4 condition holds? (item 4)\n"
         "(full run of the report: python experiments.py -> 27000 instances, results/)")
    rng = random.Random(seed)
    rows, q3 = [], []
    for p in P_VALUES:
        for _ in range(n_per_p):
            game = random_game(rng, p)
            sp = bool(is_strategyproof(game, stop_at_first=True))
            cond = satisfies_theorem_5_4(game)
            rows.append((p, sp, cond.holds))
            if sp and not cond.holds:
                q3.append((game, cond.violations))
        print(f"      p={p} done", flush=True)

    step("Q1", "Fraction of instances that are strategyproof, for each p")
    print(f"    {'p':>4} {'instances':>10} {'strategyproof':>14} {'Thm 5.4 holds':>14}")
    for p in P_VALUES:
        sub = [r for r in rows if r[0] == p]
        print(f"    {p:>4} {len(sub):>10} {sum(r[1] for r in sub) / len(sub):>14.3f} {sum(r[2] for r in sub) / len(sub):>14.3f}")
    say("strategyproofness drops as the graph gets denser, then recovers at large p because with many self-attacks")
    say("almost nothing is accepted whatever is revealed, so there is nothing to gain by hiding.")

    step("Q2", "Instances where the Theorem 5.4 condition HOLDS but the mechanism is NOT strategyproof")
    holds = [r for r in rows if r[2]]
    bad = [r for r in holds if not r[1]]
    print(f"    condition holds in {len(holds)} of {len(rows)} instances;  of those, not strategyproof: {len(bad)}")
    say("none - exactly what the theorem promises (sufficient condition).  In the full 27,000-instance run: 0 as well,")
    say("under every reading of 'path' (simple path / walk, alpha=beta or not, and the book's wording).")

    step("Q3", "Instances that ARE strategyproof although the Theorem 5.4 condition FAILS")
    sp_all = sum(r[1] for r in rows)
    print(f"    strategyproof instances: {sp_all};  of those the condition fails in {len(q3)} "
          f"({100 * len(q3) / max(sp_all, 1):.1f}% of the strategyproof ones; {len(q3)} instances to note)")
    classes = {
        "rescue_offset": "hiding alpha DOES free beta, but the agent loses alpha (or another argument) at the same time: a swap, no net gain",
        "beta_hopeless": "beta can never be accepted whatever anyone reveals (it attacks itself, or an argument nobody can defeat attacks it), so nothing is to be gained",
        "alpha_irrelevant": "beta's status is the same with or without alpha (chain cut by others, or alpha is dead anyway)",
        "hiding_hurts_beta": "hiding alpha never frees beta and sometimes loses it: alpha's real effect on beta is supportive",
    }
    best = {}
    tally = {k: 0 for k in classes}
    for game, viols in q3:
        for i, a, b in viols[:6]:                      # the first few violating pairs are enough to classify
            cls = diagnose_violation(game, i, a, b)
            tally[cls] += 1
            key = (cls)
            if key not in best or len(game.attacks) < len(best[key][0].attacks):
                best[key] = (game, i, a, b)
    print("    why they are strategyproof (violating pairs classified by comparing 'reveal all' vs 'hide alpha'):")
    for k, v in tally.items():
        print(f"      {k:<18} {v:>5} pairs   {classes[k]}")
    print("\n    One small instance of each class, worked through:")
    for cls in classes:
        if cls not in best:
            continue
        game, i, a, b = best[cls]
        full = grounded_direct_mechanism(game.attacks, game.agent_arguments)
        hidden_reports = [set(A) for A in game.agent_arguments]
        hidden_reports[i] -= {a}
        hid = grounded_direct_mechanism(game.attacks, hidden_reports)
        print(f"\n    [{cls}]")
        print(f"      attacks: {sorted(game.attacks)}")
        print(f"      agents : " + "; ".join(f"agent {k} owns {fmt(A)}" for k, A in enumerate(game.agent_arguments)))
        print(f"      violating pair: agent {i} owns {a} and {b} (odd path {a} ~> {b})")
        print(f"      everyone truthful      -> outcome {fmt(full)}, agent {i} utility {utility(game, i, full)}")
        print(f"      agent {i} hides {a}        -> outcome {fmt(hid)}, agent {i} utility {utility(game, i, hid)}")
        say(classes[cls])
        assert is_strategyproof(game).holds


def summary():
    part("SUMMARY")
    print("  Part 1: all items 1-6E implemented and checked on the book's Figures 5.1-5.3.")
    print("  Part 2: mechanism, best responses, Theorem 5.3 check, Theorem 5.4 check (cycle-safe), book Examples 5.10/5.11.")
    print("  Experiments: Q1 table, Q2 = 0 counterexamples to Theorem 5.4, Q3 = many strategyproof instances where the")
    print("  condition fails, all explained by swaps, hopeless targets, irrelevant or supportive arguments.")
    print("  Full-scale numbers (27,000 instances) are in REPORT.md / report.pdf and results/.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pause", action="store_true", help="wait for Enter between steps")
    ap.add_argument("--instances", type=int, default=500, help="random instances per p in the experiment step")
    args = ap.parse_args()
    PAUSE = args.pause
    sys.stdout.reconfigure(encoding="utf-8")
    part1()
    part2()
    experiments(args.instances)
    summary()

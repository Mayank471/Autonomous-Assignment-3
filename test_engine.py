"""
Tests for the argumentation engine and the strategic mechanism.

Run with:   python -m unittest -v test_engine

Expected results for the textbook-style frameworks below were worked out by hand
from the definitions (see the comment above each example).  On top of that, the
property tests cross-check the engine against independent characterisations
(labellings, known inclusions between semantics, brute force) on random AFs.
"""

import random
import unittest
from itertools import product

from argumentation import (
    CREDULOUS,
    IN,
    OUT,
    REJECTED,
    SKEPTICAL,
    UNDEC,
    ArgumentationFramework as AF,
    acceptance_status,
    admissible_sets,
    all_extensions,
    all_legal_labellings,
    characteristic_function,
    complete_extensions,
    extension_to_labelling,
    grounded_extension,
    is_admissible,
    is_complete,
    is_conflict_free,
    is_defended,
    is_legal_labelling,
    labelling_to_extension,
    powerset,
    preferred_extensions,
    semi_stable_extensions,
    stable_extensions,
)
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


def fs(*xs):
    return frozenset(xs)


class TestBasicNotions(unittest.TestCase):
    # a -> b -> c -> d  (a chain)
    chain = AF.parse("a->b, b->c, c->d")

    def test_conflict_free(self):
        af = self.chain
        self.assertTrue(is_conflict_free(af, fs()))
        self.assertTrue(is_conflict_free(af, fs("a", "c")))
        self.assertFalse(is_conflict_free(af, fs("a", "b")))
        self.assertFalse(is_conflict_free(AF.parse("x->x"), fs("x")))  # self-attack

    def test_defended(self):
        af = self.chain
        self.assertTrue(is_defended(af, "a", fs()))          # unattacked
        self.assertFalse(is_defended(af, "b", fs()))         # attacked by a, S empty
        self.assertTrue(is_defended(af, "c", fs("a")))       # a attacks c's attacker b
        self.assertFalse(is_defended(af, "d", fs("a")))      # c is not counter-attacked
        self.assertTrue(is_defended(af, "d", fs("b")))       # b attacks c

    def test_characteristic_function(self):
        af = self.chain
        self.assertEqual(characteristic_function(af, fs()), fs("a"))
        self.assertEqual(characteristic_function(af, fs("a")), fs("a", "c"))
        self.assertEqual(characteristic_function(af, fs("a", "c")), fs("a", "c"))

    def test_admissible_and_complete(self):
        af = self.chain
        self.assertTrue(is_admissible(af, fs()))
        self.assertTrue(is_admissible(af, fs("a")))
        self.assertFalse(is_admissible(af, fs("c")))         # c is not defended
        self.assertTrue(is_admissible(af, fs("a", "c")))
        self.assertFalse(is_complete(af, fs()))              # F({}) = {a} not inside {}
        self.assertFalse(is_complete(af, fs("a")))           # also defends c
        self.assertTrue(is_complete(af, fs("a", "c")))

    def test_unknown_argument_rejected(self):
        with self.assertRaises(ValueError):
            is_conflict_free(self.chain, fs("zzz"))
        with self.assertRaises(ValueError):
            AF({"a"}, {("a", "b")})


class TestSemanticsOnClassicExamples(unittest.TestCase):
    """Canonical frameworks from the literature (Dung 1995, Caminada 2006)."""

    def check(self, af, grounded, complete, preferred, stable, semi):
        ext = all_extensions(af)
        self.assertEqual(ext["grounded"], [grounded])
        self.assertEqual(sorted(map(sorted, ext["complete"])), sorted(map(sorted, complete)))
        self.assertEqual(sorted(map(sorted, ext["preferred"])), sorted(map(sorted, preferred)))
        self.assertEqual(sorted(map(sorted, ext["stable"])), sorted(map(sorted, stable)))
        self.assertEqual(sorted(map(sorted, ext["semi-stable"])), sorted(map(sorted, semi)))

    def test_chain(self):
        # a -> b -> c : a wins, b loses, c reinstated
        self.check(AF.parse("a->b, b->c"), fs("a", "c"),
                   [fs("a", "c")], [fs("a", "c")], [fs("a", "c")], [fs("a", "c")])

    def test_mutual_attack(self):
        # Nixon diamond  a <-> b : two symmetric preferred/stable extensions
        af = AF.parse("a<->b")
        self.check(af, fs(), [fs(), fs("a"), fs("b")], [fs("a"), fs("b")],
                   [fs("a"), fs("b")], [fs("a"), fs("b")])
        self.assertEqual(acceptance_status(af, "a"), CREDULOUS)

    def test_odd_cycle(self):
        # a -> b -> c -> a : nothing can be defended; no stable extension
        af = AF.parse("a->b, b->c, c->a")
        self.check(af, fs(), [fs()], [fs()], [], [fs()])
        self.assertEqual(all_legal_labellings(af), [{"a": UNDEC, "b": UNDEC, "c": UNDEC}])

    def test_self_attack(self):
        # a -> a, a -> b  : b is attacked by a self-defeating argument but is not defended
        af = AF.parse("a->a, a->b")
        self.check(af, fs(), [fs()], [fs()], [], [fs()])

    def test_preferred_stable_semistable_differ(self):
        # a <-> b, b -> c, c -> c.
        # preferred {a},{b}; only {b} is stable (it attacks a and c); semi-stable = {b}.
        af = AF.parse("a<->b, b->c, c->c")
        self.check(af, fs(), [fs(), fs("a"), fs("b")], [fs("a"), fs("b")], [fs("b")], [fs("b")])

    def test_semistable_exists_without_stable(self):
        # Caminada's example: a three-cycle with a mutual-attack gadget hanging off it
        # (no stable extension but semi-stable extensions exist).
        af = AF.parse("a->b, b->c, c->a, c->d, d<->e")
        self.assertEqual(stable_extensions(af), [])
        self.assertTrue(semi_stable_extensions(af))
        # every semi-stable extension is preferred
        for S in semi_stable_extensions(af):
            self.assertIn(S, preferred_extensions(af))

    def test_acceptance_status(self):
        af = AF.parse("a<->b, b->c, c->c, d")
        self.assertEqual(acceptance_status(af, "d"), SKEPTICAL)
        self.assertEqual(acceptance_status(af, "a"), CREDULOUS)
        self.assertEqual(acceptance_status(af, "c"), REJECTED)
        # skeptical under stable: the only stable extension is {b, d}
        self.assertEqual(acceptance_status(af, "b", "stable"), SKEPTICAL)
        self.assertEqual(acceptance_status(af, "a", "stable"), REJECTED)

    def test_labellings(self):
        af = AF.parse("a<->b")
        labs = all_legal_labellings(af)
        self.assertEqual(len(labs), 3)
        self.assertIn({"a": IN, "b": OUT}, labs)
        self.assertIn({"a": OUT, "b": IN}, labs)
        self.assertIn({"a": UNDEC, "b": UNDEC}, labs)
        self.assertFalse(is_legal_labelling(af, {"a": IN, "b": IN}))
        self.assertFalse(is_legal_labelling(af, {"a": IN, "b": UNDEC}))


def random_af(rng, n=None, p=None):
    n = n or rng.randint(1, 7)
    p = p if p is not None else rng.choice([0.1, 0.2, 0.3, 0.5])
    args = [f"x{i}" for i in range(n)]
    return AF(args, {(a, b) for a in args for b in args if rng.random() < p})


class TestPropertiesOnRandomAFs(unittest.TestCase):
    def setUp(self):
        rng = random.Random(7)
        self.afs = [random_af(rng) for _ in range(300)]

    def test_complete_matches_brute_force(self):
        for af in self.afs:
            brute = [S for S in powerset(af.arguments) if is_complete(af, S)]
            self.assertEqual(
                sorted(map(sorted, complete_extensions(af))), sorted(map(sorted, brute))
            )

    def test_labellings_biject_with_complete_extensions(self):
        for af in self.afs:
            labs = all_legal_labellings(af)
            ins = sorted(sorted(labelling_to_extension(L)) for L in labs)
            self.assertEqual(ins, sorted(map(sorted, complete_extensions(af))))
            for S in complete_extensions(af):
                self.assertIn(extension_to_labelling(af, S), labs)

    def test_known_relationships(self):
        for af in self.afs:
            g = grounded_extension(af)
            comp, pref = complete_extensions(af), preferred_extensions(af)
            stab, semi = stable_extensions(af), semi_stable_extensions(af)
            self.assertIn(g, comp)
            self.assertTrue(all(g <= S for S in comp))        # grounded = least complete
            self.assertEqual(g, frozenset.intersection(*comp))
            self.assertTrue(pref)                              # preferred always exist
            self.assertTrue(semi)                              # semi-stable always exist
            self.assertTrue(set(stab) <= set(semi) <= set(pref) <= set(comp))
            if stab:
                self.assertEqual(set(stab), set(semi))
            # preferred == maximal complete == maximal admissible
            maxc = [S for S in comp if not any(S < T for T in comp)]
            self.assertEqual(set(pref), set(maxc))
            self.assertTrue(all(is_admissible(af, S) for S in admissible_sets(af)))

    def test_grounded_is_least_fixed_point(self):
        for af in self.afs:
            g = grounded_extension(af)
            self.assertEqual(characteristic_function(af, g), g)


class TestStrategicMechanism(unittest.TestCase):
    # alpha <-> delta, alpha -> beta; agent 0 owns {alpha, beta}, agent 1 owns {delta}.
    # Truthful: alpha, delta, beta all undecided (u0 = 0).  If agent 0 hides alpha, then
    # delta and beta are unattacked and accepted (u0 = 1)  =>  manipulable by hiding.
    attacks = {("al", "de"), ("de", "al"), ("al", "be")}
    game = StrategicGame(attacks, [{"al", "be"}, {"de"}])

    def test_mechanism(self):
        self.assertEqual(grounded_direct_mechanism(self.attacks, [{"al", "be"}, {"de"}]), fs())
        self.assertEqual(grounded_direct_mechanism(self.attacks, [{"be"}, {"de"}]), fs("be", "de"))
        # attacks with an unrevealed endpoint disappear
        self.assertEqual(grounded_direct_mechanism(self.attacks, [{"al", "be"}, set()]), fs("al"))

    def test_best_response(self):
        br = best_responses(self.game, 0, {1: fs("de")})
        self.assertEqual(br.utility, 1)
        self.assertEqual(br.reports, [fs("be")])
        # Against an agent that reveals nothing, agent 0 gets u=1 by revealing alpha (alpha wins,
        # beta loses) or by revealing only beta: both maximise, truthful is among them.
        br = best_responses(self.game, 0, {1: fs()})
        self.assertEqual(br.utility, 1)
        self.assertIn(fs("al", "be"), br.reports)
        self.assertEqual(utility(self.game, 0, fs("be", "de")), 1)

    def test_strategyproof_checker(self):
        res = is_strategyproof(self.game)
        self.assertFalse(res)
        self.assertEqual(res.counterexamples[0]["agent"], 0)
        self.assertEqual(res.counterexamples[0]["best_reports"], [fs("be")])
        # A disjoint attack between two agents' single arguments: nothing to gain by hiding.
        self.assertTrue(is_strategyproof(StrategicGame({("a", "b")}, [{"a"}, {"b"}])))
        # agent 0's argument defends its other argument against agent 1: hiding never helps
        g = StrategicGame({("c", "b"), ("a", "c")}, [{"a", "b"}, {"c"}])
        self.assertTrue(is_strategyproof(g))

    def test_theorem_5_4_condition(self):
        res = satisfies_theorem_5_4(self.game)
        self.assertFalse(res)
        self.assertEqual(res.violations, [(0, "al", "be")])
        # same agent, but only even-length path (a->x->b, x belongs to another agent)
        g = StrategicGame({("a", "x"), ("x", "b")}, [{"a", "b"}, {"x"}])
        self.assertTrue(satisfies_theorem_5_4(g))
        # length 3 path a->x->y->b is odd
        g = StrategicGame({("a", "x"), ("x", "y"), ("y", "b")}, [{"a", "b"}, {"x", "y"}])
        self.assertFalse(satisfies_theorem_5_4(g))

    def test_odd_paths_with_cycles(self):
        adj = {"a": {"x"}, "x": {"x", "b"}, "b": set()}
        # shortest a->b is 2 (even), but looping on x gives a walk of length 3 (odd)
        self.assertTrue(has_odd_walk(adj, "a", "b"))
        self.assertFalse(has_odd_simple_path(adj, "a", "b"))
        # a 2-cycle never produces an odd closed walk, a 3-cycle does
        two = {"a": {"b"}, "b": {"a"}}
        three = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
        self.assertFalse(has_odd_walk(two, "a", "a"))
        self.assertTrue(has_odd_walk(two, "a", "b"))
        self.assertTrue(has_odd_walk(three, "a", "a"))
        self.assertTrue(has_odd_simple_path(three, "a", "a"))
        # terminates on a self-loop
        self.assertTrue(has_odd_walk({"a": {"a"}}, "a", "a"))
        self.assertTrue(has_odd_simple_path({"a": {"a"}}, "a", "a"))

    def test_self_pairs_flag(self):
        g = StrategicGame({("a", "a")}, [{"a"}])
        self.assertTrue(satisfies_theorem_5_4(g))                      # distinct pairs only
        self.assertFalse(satisfies_theorem_5_4(g, include_same=True))  # indirect self-defeat

    def test_theorem_5_4_is_sufficient_on_random_games(self):
        """If the odd-path condition holds, truth-telling must be dominant."""
        rng = random.Random(11)
        checked = 0
        for _ in range(400):
            n = rng.randint(3, 6)
            args = list(range(n))
            attacks = {(a, b) for a in args for b in args if rng.random() < 0.25}
            owners = [rng.randrange(3) for _ in args]
            game = StrategicGame(attacks, [{a for a in args if owners[a] == k} for k in range(3)])
            if satisfies_theorem_5_4(game, include_same=True):
                checked += 1
                self.assertTrue(is_strategyproof(game), (attacks, owners))
        self.assertGreater(checked, 20)


if __name__ == "__main__":
    unittest.main()

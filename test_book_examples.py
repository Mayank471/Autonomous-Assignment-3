"""
Tests on the examples of the textbook chapter (see book_examples.py).

Run with:   python -m unittest -v test_book_examples

Every expected value below is stated in the book (page numbers refer to the
chapter's own numbering) except where a comment says it is derived.
"""

import random
import unittest

from argumentation import (
    CREDULOUS,
    IN,
    OUT,
    REJECTED,
    SKEPTICAL,
    UNDEC,
    acceptance_status,
    admissible_sets,
    all_extensions,
    all_legal_labellings,
    characteristic_function,
    complete_extensions,
    grounded_extension,
    is_admissible,
    is_complete,
    labelling_to_extension,
    powerset,
)
from book_examples import (
    EXAMPLE_5_10_ATTACKS,
    X,
    Y,
    Z,
    example_5_10,
    example_5_11,
    figure_5_1,
    figure_5_2,
    figure_5_3,
)
from strategic import (
    StrategicGame,
    best_responses,
    grounded_direct_mechanism,
    is_strategyproof,
    satisfies_theorem_5_4,
    utility,
)


def fs(*xs):
    return frozenset(xs)


class TestFigure51(unittest.TestCase):
    """Figure 5.1 (p.181): 1 has defeaters 2 and 4, defeated by 3 and 5 respectively."""

    af = figure_5_1()

    def test_defense(self):
        # "{3, 5} defends 1" (p.182)
        self.assertEqual(characteristic_function(self.af, fs(3, 5)), fs(1, 3, 5))

    def test_example_5_5_admissible(self):
        for S in [fs(), fs(3), fs(5), fs(3, 5), fs(1, 3, 5)]:
            self.assertTrue(is_admissible(self.af, S), S)
        self.assertEqual(
            admissible_sets(self.af), [fs(), fs(3), fs(5), fs(3, 5), fs(1, 3, 5)]
        )
        self.assertFalse(is_admissible(self.af, fs(1)))        # 1's defeaters are undefeated

    def test_example_5_6_complete(self):
        self.assertTrue(is_admissible(self.af, fs(3, 5)))
        self.assertFalse(is_complete(self.af, fs(3, 5)))        # defends 1 but lacks it
        self.assertEqual(characteristic_function(self.af, fs(3)), fs(3, 5))
        self.assertEqual(characteristic_function(self.af, fs(5)), fs(3, 5))
        self.assertEqual(characteristic_function(self.af, fs(1, 3, 5)), fs(1, 3, 5))
        self.assertEqual(complete_extensions(self.af), [fs(1, 3, 5)])  # the only complete extension

    def test_grounded_iteration(self):
        # F^1(0) = {3,5}; F^2(0) = {1,3,5}; F^3(0) = F^2(0)   (p.184)
        f1 = characteristic_function(self.af, fs())
        f2 = characteristic_function(self.af, f1)
        f3 = characteristic_function(self.af, f2)
        self.assertEqual((f1, f2, f3), (fs(3, 5), fs(1, 3, 5), fs(1, 3, 5)))
        self.assertEqual(grounded_extension(self.af), fs(1, 3, 5))

    def test_example_5_8_preferred(self):
        ext = all_extensions(self.af)
        self.assertEqual(ext["preferred"], [fs(1, 3, 5)])
        self.assertEqual(ext["stable"], [fs(1, 3, 5)])
        self.assertEqual(ext["semi-stable"], [fs(1, 3, 5)])

    def test_status(self):
        self.assertEqual(
            {a: acceptance_status(self.af, a) for a in range(1, 6)},
            {1: SKEPTICAL, 2: REJECTED, 3: SKEPTICAL, 4: REJECTED, 5: SKEPTICAL},
        )


class TestFigure52(unittest.TestCase):
    """Figure 5.2 (p.183): 1 <-> 2 and 3 on its own; three labellings."""

    af = figure_5_2()

    def test_example_5_7_complete(self):
        self.assertEqual(complete_extensions(self.af), [fs(3), fs(1, 3), fs(2, 3)])

    def test_labellings(self):
        labs = all_legal_labellings(self.af)
        self.assertEqual(len(labs), 3)
        self.assertIn({1: UNDEC, 2: UNDEC, 3: IN}, labs)      # L^G
        self.assertIn({1: IN, 2: OUT, 3: IN}, labs)           # L_1
        self.assertIn({1: OUT, 2: IN, 3: IN}, labs)           # L_2

    def test_grounded_and_preferred(self):
        self.assertEqual(grounded_extension(self.af), fs(3))                       # p.184
        self.assertEqual(all_extensions(self.af)["preferred"], [fs(1, 3), fs(2, 3)])  # Example 5.8

    def test_stable_and_semistable(self):
        ext = all_extensions(self.af)
        self.assertEqual(ext["stable"], [fs(1, 3), fs(2, 3)])
        self.assertEqual(ext["semi-stable"], [fs(1, 3), fs(2, 3)])

    def test_status(self):
        self.assertEqual(acceptance_status(self.af, 3), SKEPTICAL)
        self.assertEqual(acceptance_status(self.af, 1), CREDULOUS)
        self.assertEqual(acceptance_status(self.af, 2), CREDULOUS)

    def test_table_5_1(self):
        """Caminada's correspondence between labellings and extensions (Table 5.1)."""
        af = self.af
        labs = all_legal_labellings(af)
        ins = lambda L: labelling_to_extension(L)
        undec = lambda L: frozenset(a for a, l in L.items() if l == UNDEC)
        outs = lambda L: frozenset(a for a, l in L.items() if l == OUT)
        ext = all_extensions(af)
        self.assertEqual(sorted(map(sorted, map(ins, labs))), sorted(map(sorted, ext["complete"])))
        minimal_in = [L for L in labs if not any(ins(M) < ins(L) for M in labs)]
        self.assertEqual([ins(L) for L in minimal_in], ext["grounded"])
        maximal_in = [L for L in labs if not any(ins(L) < ins(M) for M in labs)]
        self.assertEqual(sorted(map(sorted, map(ins, maximal_in))), sorted(map(sorted, ext["preferred"])))
        minimal_undec = [L for L in labs if not any(undec(M) < undec(L) for M in labs)]
        self.assertEqual(sorted(map(sorted, map(ins, minimal_undec))), sorted(map(sorted, ext["semi-stable"])))
        no_undec = [L for L in labs if not undec(L)]
        self.assertEqual(sorted(map(sorted, map(ins, no_undec))), sorted(map(sorted, ext["stable"])))


class TestFigure53(unittest.TestCase):
    """Figure 5.3 (p.186): b->a, c->b, d->b, c<->d, e->d.  Grounded extension {a, c, e} (p.188)."""

    af = figure_5_3()

    def test_grounded(self):
        self.assertEqual(grounded_extension(self.af), fs("a", "c", "e"))

    def test_other_semantics_agree(self):
        # derived: d is out (attacked by e, unattacked), so there is a single complete labelling
        ext = all_extensions(self.af)
        for k in ("complete", "preferred", "stable", "semi-stable"):
            self.assertEqual(ext[k], [fs("a", "c", "e")], k)

    def test_status(self):
        self.assertEqual(
            {a: acceptance_status(self.af, a) for a in "abcde"},
            {"a": SKEPTICAL, "b": REJECTED, "c": SKEPTICAL, "d": REJECTED, "e": SKEPTICAL},
        )


class TestExample510(unittest.TestCase):
    """Example 5.10 / Figure 5.4 (p.199-200)."""

    game = example_5_10()

    def test_full_revelation(self):
        o = grounded_direct_mechanism(self.game.attacks, self.game.agent_arguments)
        self.assertEqual(o, fs(1, 3))                          # "the outcome o = {1, 3}"
        self.assertEqual(utility(self.game, X, o), 1)          # u_x(o, {1,4,5}) = 1
        # The book prints u_y(o,{3}) = 1 and u_z(o,{2}) = 0: the argument sets are swapped
        # (misprint).  Correct values: y owns {2} -> 0, z owns {3} -> 1.
        self.assertEqual(utility(self.game, Y, o), 0)
        self.assertEqual(utility(self.game, Z, o), 1)

    def test_x_gains_by_hiding_1(self):
        o = grounded_direct_mechanism(self.game.attacks, [{4, 5}, {2}, {3}])
        self.assertEqual(o, fs(2, 4, 5))                       # Figure 5.4(b)
        self.assertEqual(utility(self.game, X, o), 2)
        br = best_responses(self.game, X, {Y: fs(2), Z: fs(3)})
        self.assertEqual((br.utility, br.reports), (2, [fs(4, 5)]))

    def test_not_strategyproof_only_x_manipulates(self):
        res = is_strategyproof(self.game)
        self.assertFalse(res)
        # "for both y and z, revealing their true types weakly dominates revealing nothing"
        self.assertEqual({c["agent"] for c in res.counterexamples}, {X})

    def test_theorem_5_4_condition_fails_for_x(self):
        # A_x is conflict-free but 1 indirectly defeats 4 and 5 (paths 1->2->3->4, 1->2->3->5)
        res = satisfies_theorem_5_4(self.game, require_conflict_free=True)
        self.assertFalse(res)
        self.assertEqual(res.violations, [(X, 1, 4), (X, 1, 5)])


class TestExample511(unittest.TestCase):
    """Example 5.11 / Figure 5.5 (p.201): argument 6 and defeat (6, 3) added; A_x = {1,4,5,6}."""

    game = example_5_11()

    def test_full_revelation(self):
        o = grounded_direct_mechanism(self.game.attacks, self.game.agent_arguments)
        self.assertEqual(o, fs(1, 4, 5, 6))                    # x gets all its arguments accepted
        self.assertEqual(utility(self.game, X, o), 4)

    def test_truth_is_dominant_despite_indirect_defeats(self):
        self.assertTrue(is_strategyproof(self.game))           # strategyproof ...
        res = satisfies_theorem_5_4(self.game)
        self.assertFalse(res)                                  # ... yet the condition of Thm 5.4 fails
        self.assertEqual(res.violations, [(X, 1, 4), (X, 1, 5)])  # 1 ~> 4 and 1 ~> 5

    def test_the_cancelling_argument_is_6_not_5(self):
        """The book's discussion names argument 5 as the one cancelling the indirect
        self-defeat; it is 6 (the assignment's erratum).  Removing 6 makes x manipulable
        again, whereas removing 5 does not (6 alone is enough)."""
        without_6 = StrategicGame(EXAMPLE_5_10_ATTACKS, [{1, 4, 5}, {2}, {3}])
        self.assertFalse(is_strategyproof(without_6))
        without_5 = StrategicGame({(1, 2), (2, 3), (3, 4), (6, 3)}, [{1, 4, 6}, {2}, {3}])
        self.assertTrue(is_strategyproof(without_5))
        # 5 is defeated by 3 and defeats nothing, so it cannot affect anyone else's status.
        self.assertEqual(self.game.framework().targets_of(5), frozenset())


class TestTheorem53Formulation(unittest.TestCase):
    """Theorem 5.3 (p.200): strategyproof iff for every agent i, every S subset of A_i and
    every A_-i:  |A_i n E(<A_i u A_-i>)| >= |A_i n E(<(A_i \\ S) u A_-i>)|.
    Check our `is_strategyproof` against a literal transcription of that inequality."""

    @staticmethod
    def book_condition(game):
        for i, Ai in enumerate(game.agent_arguments):
            pool = game.arguments - Ai
            for A_minus_i in powerset(pool):
                full = len(Ai & grounded_direct_mechanism(game.attacks, [Ai, A_minus_i]))
                for S in powerset(Ai):
                    hidden = len(Ai & grounded_direct_mechanism(game.attacks, [Ai - S, A_minus_i]))
                    if full < hidden:
                        return False
        return True

    def test_equivalence_on_random_games(self):
        rng = random.Random(3)
        seen = {True: 0, False: 0}
        for _ in range(300):
            n = rng.randint(3, 7)
            attacks = {(a, b) for a in range(n) for b in range(n) if rng.random() < 0.2}
            owner = [rng.randrange(3) for _ in range(n)]
            game = StrategicGame(attacks, [{a for a in range(n) if owner[a] == k} for k in range(3)])
            expected = self.book_condition(game)
            seen[expected] += 1
            self.assertEqual(bool(is_strategyproof(game)), expected)
        self.assertTrue(seen[True] > 10 and seen[False] > 10)

    def test_book_examples(self):
        self.assertFalse(self.book_condition(example_5_10()))
        self.assertTrue(self.book_condition(example_5_11()))


if __name__ == "__main__":
    unittest.main()

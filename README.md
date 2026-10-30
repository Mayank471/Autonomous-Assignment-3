# Assignment 3 – Argumentation Engine & Strategic Argumentation

Pure Python 3 (tested on 3.13), **no third-party packages**.

## Files

| File | Contents |
|---|---|
| `argumentation.py` | Part 1: `ArgumentationFramework` class and all engine functions |
| `strategic.py` | Part 2: grounded direct mechanism, best responses, strategyproofness check (Thm 5.3), odd-path condition (Thm 5.4) |
| `experiments.py` | Random-instance experiment (writes to `results/`) |
| `book_examples.py` | The textbook's Figures 5.1-5.3 and Examples 5.10/5.11 as ready-made objects |
| `test_engine.py` | 24 unit/property tests (hand-derived frameworks, random cross-checks) |
| `test_book_examples.py` | 24 tests asserting every value the book states for its examples (and Theorem 5.3 as literally written) |
| `demo.py`, `demo_output.txt` | Step-by-step demonstration (21 numbered steps) and its captured output |
| `REPORT.md` | Report: design, experimental results, answers to the three questions |
| `report.tex`, `report.pdf` | The report as LaTeX source and compiled PDF |
| `results/` | `summary.json`, `instances.csv` (one row per instance), `notable_instances.json` (Q2/Q3 instance lists for every reading), `q3_strategyproof_but_condition_fails.csv` (Q3 list, headline reading), `run_log.txt` |

## How to run

```bash
python -m unittest -v test_engine test_book_examples   # all 48 tests (< 1 s)
python demo.py                           # step-by-step demonstration (about 15 s)
python demo.py --pause                   # same, waits for Enter between steps (live presentation)
python experiments.py                    # 9 values of p (0.1 to 0.9) x 3000 instances = 27 000 (about 3-4 min)
python experiments.py --instances 1000 --seed 7 --out results_small   # quicker / other seed
```

## Assignment items → code

### Part 1 (`argumentation.py`)

| # | Item | Function |
|---|---|---|
| 1 | AF class ⟨A, ⇀⟩ | `ArgumentationFramework(arguments, attacks)`; also `ArgumentationFramework.parse("a->b, b<->c, d")` |
| 2 | conflict-free | `is_conflict_free(af, S)` |
| 3 | argument defended by S | `is_defended(af, a, S)` |
| 4 | characteristic function F(S) | `characteristic_function(af, S)` |
| 5 | admissible / complete | `is_admissible(af, S)`, `is_complete(af, S)` |
| 6A | grounded | `grounded_extension(af)` (iterates F from ∅ to its least fixed point) |
| 6B | complete | `complete_extensions(af)` |
| 6C | preferred, stable, semi-stable | `preferred_extensions`, `stable_extensions`, `semi_stable_extensions`; `all_extensions(af)` returns all five semantics |
| 6D | legal labellings | `all_legal_labellings(af)` (checks all 3ⁿ labellings against Caminada's conditions); `is_legal_labelling`, `extension_to_labelling`, `labelling_to_extension` |
| 6E | acceptance status | `acceptance_status(af, a, semantics="preferred")` → *skeptically accepted* / *credulously accepted* / *rejected* |

Conventions: preferred = ⊆-maximal admissible sets; stable = conflict-free sets attacking everything outside;
semi-stable = complete extensions with ⊆-maximal range S ∪ S⁺. "Credulously accepted" means in some
but not all extensions (skeptical acceptance implies credulous acceptance). If a semantics has no
extension (stable only), the argument is reported as rejected.

### Part 2 (`strategic.py`)

| # | Item | Function |
|---|---|---|
| – | game description | `StrategicGame(attacks, agent_arguments)` (disjoint argument sets, one per agent) |
| 1 | the mechanism | `grounded_direct_mechanism(attacks, reports)` |
| 2 | best responses | `best_responses(game, agent, others_reports)` → `BestResponse(utility, reports)`; enumerates all 2^|Aᵢ| subsets |
| 3 | Theorem 5.3 property | `is_strategyproof(game)` (alias `check_theorem_5_3`): for every agent and every combination of subsets the others may reveal, is revealing all of Aᵢ a best response? Returns a result object (truthy if it holds) with all counterexamples |
| 4 | Theorem 5.4 condition | `satisfies_theorem_5_4(game, mode="path", include_same=False)`; helpers `has_odd_walk`, `has_odd_simple_path` |

Utility of agent *i* = number of its own arguments in the grounded extension of the framework induced
by the revealed arguments (attacks with an unrevealed endpoint are dropped).

**Odd paths in cyclic graphs.** A naive DFS can loop forever on cycles. `has_odd_walk` runs BFS over
(argument, parity) states, so it always terminates and also finds walks that reuse a node (e.g.
`a→x, x→x, x→b` has an odd walk of length 3 although the only simple path has length 2).
`has_odd_simple_path` restricts to simple paths. `satisfies_theorem_5_4` lets you pick either
reading (`mode`) and decide whether α = β (an odd closed path, i.e. indirect self-defeat) counts
(`include_same`). The experiments report all four combinations; the default (and headline) reading is the literal one: simple path, α ≠ β.

## Book examples (`multiagent-systems_compress.pdf`, Chapter 5)

`book_examples.py` encodes the book's frameworks exactly (Figures 5.1, 5.2, 5.3 and Examples 5.10 / 5.11) and
`test_book_examples.py` checks the book's stated results: admissible/complete/grounded/preferred sets of Figures 5.1-5.2,
the three labellings of Figure 5.2 and Table 5.1's labelling/extension correspondence, the grounded extension {a, c, e} of
Figure 5.3, the outcomes and utilities of Example 5.10 (x gains by hiding argument 1), and Example 5.11 (truth-telling dominant
although the odd-path condition fails). `demo.py` prints all of them.

The two misprints from the assignment are handled in the code/tests/report:

* Example 5.10: the book prints u_y(o,{3}) = 1 and u_z(o,{2}) = 0; the argument sets are swapped. The code gives
  u_y = 0 (y owns {2}) and u_z = 1 (z owns {3}).
* Discussion after Example 5.11: the argument that cancels the indirect self-defeat is 6, not 5 (test
  `test_the_cancelling_argument_is_6_not_5`).

The book's Theorem 5.4 additionally requires each agent's type to be conflict-free; this is available as
`satisfies_theorem_5_4(game, require_conflict_free=True)` and is reported as a fifth reading in the experiments.

## Demonstration (`python demo.py`, output saved in `demo_output.txt`)

Every step names the assignment item it demonstrates, prints the exact call that is executed (`>>>`) and its result.

| Steps | Assignment item | What is shown (book examples) |
|---|---|---|
| 1 | Part 1, item 1 | Build Figure 5.1 with the framework class; attackers, targets, S+ |
| 2-5 | items 2-5 | conflict-free, defended-by, characteristic function, admissible/complete (Examples 5.5, 5.6) |
| 6-10 | items 6A-6E | grounded iteration, complete, preferred/stable/semi-stable, labellings of Fig. 5.2, acceptance status |
| 11 | "test on the book" | runs all 48 tests (all pass) |
| 12-14 | Part 2, items 1-2 | Example 5.10: mechanism outcome and utilities, all 8 reports of x, best response {4,5} |
| 15 | item 3 | Theorem 5.3 check: Example 5.10 not strategyproof, Example 5.11 strategyproof |
| 16 | item 4 | Theorem 5.4 condition with the odd paths shown; cycle handling (loop, 2-cycle, 3-cycle) |
| 17 | misprints | utilities of y and z; argument 6 (not 5) cancels the indirect self-defeat |
| 18-21 | Experiments Q1-Q3 | random instances (500 per p in the demo; 3000 per p in the report), strategyproof fraction, Q2 = 0, Q3 reasons with worked instances |

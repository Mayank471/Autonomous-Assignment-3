# Assignment 3 – Report: Argumentation Engine and Strategic Argumentation

All numbers below come from `python experiments.py` (seed 2024, output in `results/`) and from
`python -m unittest test_engine test_book_examples`; nothing is estimated by hand except where stated.

## 1. Part 1 – The argumentation engine

`argumentation.py` implements every requested function with a direct reading of the definitions
(see README for the item → function table).

* **Framework class.** `ArgumentationFramework(arguments, attacks)` stores the frozen argument set and
  attack relation, validates that attacks only mention known arguments, and precomputes attackers/targets.
  Self-attacks are allowed. `parse("a->b, b<->c, d")` builds frameworks in one line.
* **Basic notions.** conflict-free (no attack inside S); *a* is defended by S iff every attacker of *a* is
  attacked by a member of S; F(S) = {a : S defends a}; S admissible iff conflict-free and S ⊆ F(S);
  S complete iff admissible and F(S) ⊆ S.
* **Grounded** = least fixed point of F, obtained by iterating F from ∅. **Complete** extensions are found by
  enumerating subsets (only supersets of the grounded extension without self-attackers need to be tried).
  **Preferred** = ⊆-maximal admissible sets; **stable** = conflict-free sets attacking everything outside;
  **semi-stable** = complete extensions with ⊆-maximal range S ∪ S⁺.
* **Labellings.** All 3ⁿ labellings are generated and filtered with Caminada's legality conditions
  (in ⇔ all attackers out; out ⇔ some attacker in; undec otherwise).
* **Acceptance status.** Under the chosen semantics (preferred by default): in every extension → skeptically
  accepted; in some but not all → credulously accepted; in none → rejected.

**Verification.** `test_engine.py` checks hand-derived results on the standard textbook frameworks (chain,
Nixon diamond `a↔b`, odd cycle, self-attack, `a↔b, b→c, c→c` where preferred ≠ stable, and Caminada's
three-cycle-plus-mutual-attack framework that has semi-stable but no stable extensions) and, on 300 random
frameworks, cross-checks the engine against independent facts: complete extensions equal brute force over all
subsets; legal labellings are in bijection with complete extensions; grounded = least complete = ⋂ complete;
stable ⊆ semi-stable ⊆ preferred ⊆ complete; stable ≠ ∅ ⇒ stable = semi-stable; preferred = maximal complete.

**Book examples (Chapter 5 of the course textbook; `book_examples.py`, `test_book_examples.py`).** The frameworks are
encoded exactly as drawn in the book, and every value the book states is asserted in a test:

| Book example | Framework | Results reproduced by the engine |
|---|---|---|
| Fig. 5.1, Ex. 5.5, 5.6, 5.8 | α3→α2→α1←α4←α5 | admissible sets ∅, {3}, {5}, {3,5}, {1,3,5}; {3,5} defends 1 but is not complete; F(∅) = {3,5}, F²(∅) = {1,3,5} = grounded; {1,3,5} is the only complete (and preferred, stable, semi-stable) extension; 1, 3, 5 skeptically accepted, 2, 4 rejected |
| Fig. 5.2, Ex. 5.7, 5.8 | α1 ↔ α2, α3 alone | complete {3}, {1,3}, {2,3}; grounded {3}; preferred {1,3}, {2,3}; the three labellings L^G (1, 2 undec), L1 (1 in, 2 out), L2 (2 in, 1 out); the labelling/extension correspondence of Table 5.1 (grounded = minimal in, preferred = maximal in, semi-stable = minimal undec, stable = no undec) verified; 3 skeptical, 1 and 2 credulous |
| Fig. 5.3, Ex. 5.9 | b→a, c→b, d→b, c↔d, e→d | grounded = {a, c, e} (as stated on p. 188); all other semantics coincide with it; a, c, e skeptical, b, d rejected |

(The graphs of Figures 5.1–5.3 were read off the book's drawings; the text only describes them in words.) The extra frameworks of
`test_engine.py` (chain, odd cycle, self-attack, a case with preferred ≠ stable, Caminada's semi-stable-without-stable example) were derived by hand, and
300 random frameworks are cross-checked against independent characterisations (complete = brute force over all subsets; legal
labellings ↔ complete extensions; grounded = least complete = ⋂ complete; stable ⊆ semi-stable ⊆ preferred ⊆ complete; preferred = maximal
complete). All 48 tests pass.

## 2. Part 2 – Grounded direct argumentation mechanism

`strategic.py`:

1. `grounded_direct_mechanism(attacks, reports)` – induce the framework on the union of the reports (attacks with
   an unrevealed end are dropped) and return its grounded extension. Agent *i*'s utility is |outcome ∩ Aᵢ|.
2. `best_responses(game, i, others_reports)` – enumerates all 2^|Aᵢ| subsets (including ∅) and returns every
   one achieving the maximal utility.
3. `is_strategyproof(game)` (Theorem 5.3 property) – for every agent and every combination of subsets that the
   other agents could reveal, checks that revealing all of Aᵢ attains the maximal utility; it returns all
   counterexamples (agent, others' reports, truthful utility, better reports). Mechanism outcomes are memoised
   on the union of the reports, which makes the full 3-agent check on 8 arguments take milliseconds.
4. `satisfies_theorem_5_4(game)` – no agent owns two arguments α, β with an odd-length directed path α ⇝ β in the full graph.
   The graph may have cycles, so paths are *simple* (no argument repeated; DFS with a visited set, `has_odd_simple_path`),
   which is the literal reading of "directed path" and is the headline reading. Because the assignment stresses cycles I also
   implemented the *walk* reading (`has_odd_walk`: BFS over (argument, parity) states, always terminates), in which a self-loop
   or cycle can flip parity: `a→x, x→x, x→b` has an odd walk of length 3 although its only simple path has length 2. A second
   switch decides whether α = β is allowed (an odd cycle through α, "indirect self-defeat"). **Default = simple path, α ≠ β**
   ("two arguments"); the other three readings are reported as side comparisons.

**The book's statements.** Theorem 5.3 (p. 200): the mechanism is strategyproof for acceptability maximisers iff for every agent *i*,
every S ⊆ Aᵢ and every A₋ᵢ, |Aᵢ ∩ E(Aᵢ ∪ A₋ᵢ)| ≥ |Aᵢ ∩ E((Aᵢ∖S) ∪ A₋ᵢ)|; `is_strategyproof` checks exactly this (the test suite
also transcribes the inequality literally and confirms the two agree on 300 random games). Theorem 5.4 (p. 200): if each agent's type is
conflict-free **and** contains no α₁, α₂ with α₁ ⇝ α₂ (odd-length path in the whole graph) then the mechanism is strategyproof. The
assignment words the condition as "no two arguments with an odd path"; the book additionally requires conflict-freeness, which between
distinct arguments is already an odd path of length 1 and otherwise only excludes self-attacks. `satisfies_theorem_5_4(...,
require_conflict_free=True)` implements the book's exact wording and is reported as a fifth reading in §3.

**The book's own examples.**

* *Example 5.10 / Fig. 5.4*: x = {1,4,5}, y = {2}, z = {3}, R = {(1,2), (2,3), (3,4), (3,5)}. Truthfully the outcome is {1, 3}; utilities
  u_x = 1, u_y = 0, u_z = 1. (**Misprint**: the book prints u_y(o,{3}) = 1 and u_z(o,{2}) = 0, i.e. with the two agents' argument sets
  exchanged; the values above are the correct ones and are what the code computes.) If x withholds argument 1 the outcome is {2, 4, 5}
  and u_x = 2, so the mechanism is not strategyproof; `best_responses` for x returns exactly {4, 5}. The checker finds profitable deviations
  for x only, matching the book's remark that for y and z truthful revelation weakly dominates revealing nothing. The Theorem 5.4 condition is
  violated by (x; 1, 4) and (x; 1, 5): 1→2→3→4 and 1→2→3→5 are odd paths of length 3.
* *Example 5.11 / Fig. 5.5*: add argument 6 (to x) and the defeat (6, 3). The truthful outcome is {1, 4, 5, 6}, so x gets all of its arguments
  accepted and the checker confirms truth-telling is dominant – although 1 ⇝ 4 and 1 ⇝ 5 still violate the Theorem 5.4 condition. This is the
  book's illustration that the condition is sufficient but not necessary. **Misprint**: the discussion afterwards says argument *5* cancels
  the negative effect of the indirect defeat; it is argument **6** (it defeats 3, which would otherwise defeat 4 and 5). The code confirms
  this: without 6 the instance is manipulable again (x gains by revealing {4, 5}), while with 6 but without 5 it is still strategyproof; and
  5 defeats nothing, so it cannot influence anyone else's status.

**A further manipulable example** (also in the tests and demo). Agent 0 owns {α, β}, agent 1 owns {δ}; attacks
α ↔ δ and α → β. Truthfully, α, δ and β are all undecided (grounded = ∅, utility 0). If agent 0 hides α,
δ and β are unattacked and both accepted: utility 1. So the mechanism is not strategyproof, and the condition
of Theorem 5.4 is violated by (α, β) (path of length 1). This is the "hiding an argument that makes trouble"
phenomenon: α is useless to its owner but blocks β.

## 3. Experiments

**Set-up.** For each attack probability p ∈ {0.1, 0.2, …, 0.9} I drew **3000 random instances, 27 000 in total**
(≥ 1000 required): 6, 7 or 8 arguments (uniform), every ordered pair (a, b) an attack with probability p (self-attacks a→a
are possible attacks and are included), every argument given to one of 3 agents uniformly (an agent may get none). For each
instance the strategyproofness check is exhaustive (3 agents × all subsets of own arguments × all subset combinations of the
others), and Theorem 5.4's condition is evaluated under several readings (simple path / walk × α ≠ β / α = β allowed) plus a fifth reading, the book's exact wording (simple path, α ≠ β, **and** types conflict-free). Run time
≈ 3 minutes. With 3000 samples per p, each fraction has a 95 % confidence half-width of at most ±0.018.

### 3.1 Fraction of strategyproof instances (question 1)

| p | strategyproof | Thm 5.4 holds (**simple path, α≠β**) | (simple path, α=β allowed) | (walk, α≠β) | (walk, α=β allowed) | (book: simple path, α≠β, conflict-free) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.1 | **0.744** | 0.241 | 0.120 | 0.221 | 0.120 | 0.121 |
| 0.2 | **0.374** | 0.053 | 0.012 | 0.033 | 0.012 | 0.012 |
| 0.3 | **0.170** | 0.012 | 0.002 | 0.004 | 0.002 | 0.002 |
| 0.4 | **0.108** | 0.002 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.5 | **0.089** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.6 | **0.113** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.7 | **0.166** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.8 | **0.284** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.9 | **0.528** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Overall 7725 of 27 000 instances (28.6 %) are strategyproof.

**Reading the curve.** Strategyproofness falls steeply from p = 0.1 to p ≈ 0.5 and then *rises* again. At low p the graph is
sparse, so few arguments of the same agent are connected and there is little to gain by hiding. As p grows, attack chains and
cycles connect an agent's arguments (more opportunities to profit from hiding), so the fraction drops. For large p the effect
reverses because a self-attack has probability p, so the fraction of self-attacking arguments is ≈ p. In a separate sample of
600 instances per p, the grounded extension of the full framework was empty in 94 % (p = 0.5), 98 % (p = 0.6) and ≈ 100 %
(p ≥ 0.7) of instances (mean |G|/n ≈ 0.01 at p = 0.5, ≈ 0 at p ≥ 0.8). When almost nothing can be accepted, utilities are mostly
0 for every report and there is little to manipulate. The Theorem 5.4 condition is far more demanding than strategyproofness: it needs
*every* pair of an agent's arguments to be free of odd paths, which is practically never true beyond p ≈ 0.3.

### 3.2 Condition holds but the mechanism is manipulable (question 2)

| reading of the condition | condition holds | …and strategyproof | …but **not** strategyproof |
|---|---:|---:|---:|
| **simple path, α ≠ β (headline)** | 928 | 928 | **0** |
| simple path, α = β allowed | 402 | 402 | **0** |
| walk, α ≠ β | 777 | 777 | **0** |
| walk, α = β allowed | 402 | 402 | **0** |
| book: simple path, α ≠ β, types conflict-free | 405 | 405 | **0** |

**There are no such instances** – in 27 000 instances and under every reading, whenever the odd-path condition holds (including the book's exact wording),
revealing everything is a best response against every combination of the others' reports. This is exactly what Theorem 5.4
claims (the condition is *sufficient*), so the experiment finds no counter-example to the theorem and also suggests that both
checkers are implemented consistently. (`test_engine.py` repeats the check on 400 other random games.) So there is no list of
instances to explain: `results/notable_instances.json` has an empty `cond_but_manipulable` list for every reading (the list the assignment asks me to "note" is therefore empty).

*Why it should be so (intuition, not a full proof).* The grounded labelling is an alternating "in/out" propagation along
attacks: an argument is out because an attacker is in, and in because all attackers are out. When agent *i* hides an argument α,
the labelling can change only downstream of α along attack paths. Hiding α can *help* the agent only by freeing some own
argument β that α was keeping out (or undecided), which needs an odd-length attack chain α ⇝ β (an in-labelled α kills the
arguments at odd distance). But then α itself is lost at the same moment, so the gain is paid for by the loss; and if α was not
accepted, hiding it cannot change things it was not already causing. Theorem 5.4 formalises this. The condition is not vacuous –
it holds in 928 of the instances.

The readings differ only in coverage: the simple-path condition holds in 151 more instances than the walk condition (those whose
only odd connection is a non-simple walk going round a self-loop or cycle); all 151 are strategyproof, as they must be.

### 3.3 Strategyproof although the condition fails (question 3)

| reading | condition fails & strategyproof | condition fails & manipulable |
|---|---:|---:|
| **simple path, α ≠ β (headline)** | **6797** | 19275 |
| simple path, α = β allowed | 7323 | 19275 |
| walk, α ≠ β | 6948 | 19275 |
| walk, α = β allowed | 7323 | 19275 |
| book: simple path, α ≠ β, types conflict-free | 7320 | 19275 |

So the condition is **not necessary**: with the headline reading, 6797 of the 26 072 instances that fail it (26.1 %) are
strategyproof, and only 928 of the 7725 strategyproof instances (12.0 %) satisfy it. All 6797 instances are stored in
`results/notable_instances.json` (`path_distinct → sp_but_cond_fails`, with attacks, each agent's argument set, the violating
(agent, α, β) triples and the diagnosed reason); the other readings are under their own keys. A flat, human-readable list of the headline instances is in
`results/q3_strategyproof_but_condition_fails.csv`.

To explain *why* each is strategyproof I compared, for every violating pair (α, β) and every combination of the others' reports,
"reveal everything" with "hide α". Every pair falls in one of these classes:

| class | meaning | instances containing it (non-exclusive) |
|---|---|---:|
| **rescue_offset** | hiding α does turn β from rejected to accepted, but the agent loses α (or something else) at the same time – a swap, no net gain | 2406 |
| **beta_hopeless** | β is accepted in *no* scenario at all (e.g. it attacks itself, or is attacked by something nobody can defeat) | 5286 |
| **alpha_irrelevant** | β's status is the same with and without α in every scenario (the chain is cut by others' arguments, or α is dead anyway) | 1714 |
| **hiding_hurts_beta** | hiding α never rescues β and sometimes loses it (α's actual effect on β is supportive: it defeats an attacker of β) | 453 |

By whole instance: 1166 (17.2 %) contain only `rescue_offset` pairs, 3313 (48.7 %) only `beta_hopeless` pairs, 2318 (34.1 %) are
mixtures. Low p is dominated by the swap effect (p = 0.1: 884 of 1509 are pure swaps), high p by hopeless β (p = 0.9: 1547 of
1583), as expected from the self-attack discussion in §3.1.

Concrete instances (arguments are numbered; I re-ran each one to confirm the numbers):

1. **Swap (`rescue_offset`), instance 0** – attacks {2→1}; agent 2 = {1, 2} (all other arguments unconnected). The pair (2, 1) has an odd path of
   length 1. Truthfully 2 is accepted and 1 rejected: utility 1. Hiding 2 makes 1 accepted and 2 absent: utility 1 again. Hiding is a
   tie, not an improvement, so revealing everything is still a best response. Instances 155, 226, 247 have the same structure.
2. **Hopeless β, instance 887** – attacks {0→0, 5→0}; agent 1 = {0, 5}; the violating pair is (5, 0): 5 attacks 0 directly,
   but 0 attacks itself and can never be accepted, whatever is revealed, so hiding 5 can only lose 5. Instances 1096, 1634, 2196 are similar.
3. **α irrelevant to β, instance 271** – attacks {0→2, 0→4, 1→2, 2→5, 5→1, 5→5}; agent 0 = {0, 1, 3}; the violating pair is (0, 1) with the odd
   path 0→2→5→1 (length 3). But 1 is attacked by the self-attacking 5, which can only be defeated through 2, and 2 is out when 0 is revealed and
   merely undecided when 0 is hidden, so 1 is not accepted either way. Revealing gives agent 0 {0, 3} (utility 2); hiding 0 gives only {3} (utility 1).
4. **Revealing α actually helps (`hiding_hurts_beta`), instance 1227** – attacks {1→5, 1→6, 2→1, 5→6, 6→3}; agents {0, 4, 5}, {2, 6}, {1, 3}. Agent 1's
   pair (2, 6): the path 2→1→5→6 is odd (length 3), but 1 also attacks 6 directly (even route). Revealing 2 defeats 1, which lets 5 in and
   kills 6, so agent 1 holds only {2}. Hiding 2 leaves 1 accepted and it defeats both 5 and 6: agent 1 holds nothing. Agent 2's pair (1, 3) is similar.
5. **The book's own instance of this phenomenon, Example 5.11** – x = {1,4,5,6} has indirect defeats 1 ⇝ 4 and 1 ⇝ 5 (paths 1→2→3→4, 1→2→3→5), so
   the condition fails, yet truth-telling is dominant. Diagnosis by the same procedure: class `alpha_irrelevant` for both pairs. The unattacked
   argument 6 (x's own) defeats 3 whenever it is revealed, so 3 is out regardless of 1 and 2, and 4 and 5 are accepted with or without 1. Hiding 1 only
   makes 2 accepted (outcome {2,4,5,6} instead of {1,4,5,6}) and costs x the argument 1 (utility 4 → 3). This is exactly the book's remark that
   the condition is sufficient but not necessary.

The general lesson: Theorem 5.4's condition looks only at *graph structure*, so it fires whenever an odd path exists, even when (i) the target
can never be accepted, (ii) the source is dead or its influence is cut, (iii) the source's actual effect on the target is supportive, or (iv) the
gain from hiding exactly cancels the loss of the hidden argument. The structure alone does not rule out these cases, so the condition is
sufficient but strictly stronger than necessary. With the walk readings a fifth cause appears: the odd parity comes only from going round a
self-loop (e.g. `4→0→6` plus `4→4`), which the simple-path reading does not flag.

## 4. Conclusions

* The engine implements all required notions and semantics and is validated against hand-derived results and against independent
  characterisations on random frameworks.
* The grounded direct mechanism is manipulable by hiding arguments in most random instances once the graph is not very sparse; the
  strategyproof fraction is 74.4 % at p = 0.1, falls to 8.9 % at p = 0.5 and recovers to 52.8 % at p = 0.9 (where almost everything is
  self-defeating).
* Theorem 5.4's odd-path condition was never satisfied by a manipulable instance (0 of 27 000, in every reading, including the book's wording), consistent with it being
  a sufficient condition. It is far from necessary: 26.1 % of the instances that fail it are strategyproof, because of swaps (loss = gain),
  unacceptable targets, dead or cut-off sources, and supportive routes.

## 5. Reproducing

```bash
python -m unittest -v test_engine test_book_examples
python demo.py                      # output saved as demo_output.txt
python experiments.py               # seed 2024, 3000 instances per p, writes results/
```

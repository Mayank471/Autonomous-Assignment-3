"""
Part 2 - Strategic argumentation: the grounded direct argumentation mechanism.

Setting.  A global argumentation framework <A, ->> has its arguments partitioned
among agents (A = A_1 u ... u A_n, pairwise disjoint).  Each agent i reports a
subset R_i of A_i.  The mechanism builds the framework induced by the union of
the reports and returns its grounded extension.  Agent i's utility is the number
of *its own* arguments in that outcome, u_i = |Grounded(R_1..R_n) n A_i|.

Items implemented here (numbering as in the assignment):

    1  grounded_direct_mechanism(attacks, reports)
    2  best_responses(game, i, others_reports)
    3  is_strategyproof(game)                -> "truth is a dominant strategy"
                                                (the property of Theorem 5.3)
    4  satisfies_theorem_5_4(game)           -> no agent holds alpha, beta with an
                                                odd-length directed path alpha ~> beta
"""

from collections import deque
from dataclasses import dataclass, field
from itertools import product

from argumentation import ArgumentationFramework, grounded_extension, powerset


# --------------------------------------------------------------------------- #
# The game description
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class StrategicGame:
    """A global attack relation plus the (disjoint) argument set of each agent."""

    attacks: frozenset
    agent_arguments: tuple  # tuple of frozensets, one per agent

    def __init__(self, attacks, agent_arguments):
        agent_arguments = tuple(frozenset(A) for A in agent_arguments)
        attacks = frozenset((a, b) for a, b in attacks)
        union = frozenset().union(*agent_arguments)
        if sum(len(A) for A in agent_arguments) != len(union):
            raise ValueError("agents' argument sets must be pairwise disjoint")
        for a, b in attacks:
            if a not in union or b not in union:
                raise ValueError(f"attack ({a!r}, {b!r}) mentions an unknown argument")
        object.__setattr__(self, "attacks", attacks)
        object.__setattr__(self, "agent_arguments", agent_arguments)

    @property
    def n_agents(self):
        return len(self.agent_arguments)

    @property
    def arguments(self):
        return frozenset().union(*self.agent_arguments)

    def framework(self):
        """The full (all arguments revealed) argumentation framework."""
        return ArgumentationFramework(self.arguments, self.attacks)


# --------------------------------------------------------------------------- #
# 1. The mechanism
# --------------------------------------------------------------------------- #


def grounded_direct_mechanism(attacks, reports):
    """Grounded extension of the framework induced by the revealed arguments.

    ``attacks``: the global attack relation (iterable of (attacker, target)).
    ``reports``: one revealed argument set per agent.
    Attacks with an unrevealed endpoint are dropped (the induced framework).
    """
    revealed = frozenset().union(*(frozenset(r) for r in reports))
    induced = {(a, b) for a, b in attacks if a in revealed and b in revealed}
    return grounded_extension(ArgumentationFramework(revealed, induced))


class _CachedMechanism:
    """Memoises the mechanism on the union of the reports (the outcome depends
    on nothing else), which makes exhaustive deviation checks cheap."""

    def __init__(self, attacks):
        self.attacks = attacks
        self._cache = {}

    def __call__(self, reports):
        revealed = frozenset().union(*reports)
        if revealed not in self._cache:
            self._cache[revealed] = grounded_direct_mechanism(self.attacks, [revealed])
        return self._cache[revealed]


def utility(game, agent, outcome):
    """Agent's utility: how many of its own arguments are accepted."""
    return len(game.agent_arguments[agent] & outcome)


# --------------------------------------------------------------------------- #
# 2. Best responses
# --------------------------------------------------------------------------- #


@dataclass
class BestResponse:
    agent: int
    utility: int  # the maximal achievable utility
    reports: list = field(default_factory=list)  # every report achieving it


def best_responses(game, agent, others_reports, _mechanism=None):
    """All reports of ``agent`` (subsets of its arguments, incl. the empty one)
    that maximise its utility, given fixed reports of the other agents.

    ``others_reports``: dict {other_agent_index: revealed set}.  The entry for
    ``agent`` itself, if present, is ignored.  Returns a ``BestResponse``.
    """
    mech = _mechanism or _CachedMechanism(game.attacks)
    fixed = [frozenset(r) for j, r in others_reports.items() if j != agent]
    best, argmax = -1, []
    for report in powerset(game.agent_arguments[agent]):
        u = utility(game, agent, mech(fixed + [report]))
        if u > best:
            best, argmax = u, [report]
        elif u == best:
            argmax.append(report)
    return BestResponse(agent, best, argmax)


# --------------------------------------------------------------------------- #
# 3. Strategyproofness (Theorem 5.3 property): truth-telling is a best response
# --------------------------------------------------------------------------- #


@dataclass
class StrategyproofnessResult:
    holds: bool
    counterexamples: list = field(default_factory=list)

    def __bool__(self):
        return self.holds


def is_strategyproof(game, stop_at_first=False):
    """Check that for every agent i, revealing all of A_i is a best response to
    *every* combination of reports (subsets) the other agents could make.

    A counterexample is a dict with the agent, the other agents' reports, the
    truthful utility, and the best-response reports/utility that beat it.
    """
    mech = _CachedMechanism(game.attacks)
    result = StrategyproofnessResult(True)
    n = game.n_agents
    for i in range(n):
        others = [j for j in range(n) if j != i]
        truthful = game.agent_arguments[i]
        for combo in product(*(list(powerset(game.agent_arguments[j])) for j in others)):
            others_reports = dict(zip(others, combo))
            br = best_responses(game, i, others_reports, mech)
            u_truth = utility(
                game, i, mech([*combo, truthful])
            )  # union-based, so order is irrelevant
            if u_truth < br.utility:
                result.holds = False
                result.counterexamples.append(
                    {
                        "agent": i,
                        "others_reports": others_reports,
                        "truthful_utility": u_truth,
                        "best_utility": br.utility,
                        "best_reports": br.reports,
                    }
                )
                if stop_at_first:
                    return result
    return result


check_theorem_5_3 = is_strategyproof  # alias using the assignment's wording


# --------------------------------------------------------------------------- #
# 4. Theorem 5.4: a sufficient condition for strategyproofness
# --------------------------------------------------------------------------- #


def _adjacency(attacks, arguments):
    adj = {a: set() for a in arguments}
    for a, b in attacks:
        adj[a].add(b)
    return adj


def has_odd_walk(adj, src, dst):
    """Is there a directed walk of odd length from src to dst?

    The graph may contain cycles, so a plain DFS could loop forever.  Instead we
    search the product graph whose states are (argument, parity of the number
    of edges used so far); the state space is finite, so BFS terminates.  Reaching
    (dst, 1) means an odd-length walk exists (for src == dst this needs at least
    one edge, i.e. an odd closed walk through src).
    """
    seen = {(src, 0)}
    queue = deque(seen)
    while queue:
        node, parity = queue.popleft()
        for nxt in adj[node]:
            state = (nxt, 1 - parity)
            if state not in seen:
                if state == (dst, 1):
                    return True
                seen.add(state)
                queue.append(state)
    return False


def has_odd_simple_path(adj, src, dst):
    """Same question restricted to *simple* paths (no repeated argument; for
    src == dst a simple odd cycle through src).  Exhaustive DFS with a visited
    set, so cycles cannot cause non-termination."""

    def dfs(node, length, visited):
        for nxt in adj[node]:
            if nxt == dst and (length + 1) % 2 == 1:
                return True
            if nxt not in visited and nxt != dst:
                if dfs(nxt, length + 1, visited | {nxt}):
                    return True
        return False

    return dfs(src, 0, frozenset({src}))


@dataclass
class Theorem54Result:
    holds: bool  # True iff NO agent owns alpha, beta with an odd path alpha ~> beta
    violations: list = field(default_factory=list)  # (agent, alpha, beta)

    def __bool__(self):
        return self.holds


def satisfies_theorem_5_4(game, mode="path", include_same=False, require_conflict_free=False):
    """Theorem 5.4's condition: no agent i holds arguments alpha, beta in A_i
    with an odd-length directed path from alpha to beta in the FULL graph.

    ``mode``: "walk"  - paths may revisit arguments (odd walk; parity-BFS)
              "path"  - simple paths only
    ``include_same``: also test alpha == beta (an odd closed path through alpha,
              e.g. a self-attack or an odd cycle: 'indirect self-defeat').
    ``require_conflict_free``: the book's statement of Theorem 5.4 also asks that
              each agent's type A_i be conflict-free.  Between two *distinct*
              arguments an attack is an odd path of length 1, so the only extra
              thing this switch adds is that no argument of A_i attacks itself;
              such arguments are reported as violations (i, alpha, alpha).

    ``holds`` is True when the condition is met (i.e. strategyproofness is
    guaranteed); ``violations`` lists every offending (agent, alpha, beta).
    """
    adj = _adjacency(game.attacks, game.arguments)
    test = has_odd_walk if mode == "walk" else has_odd_simple_path
    violations = []
    for i, Ai in enumerate(game.agent_arguments):
        if require_conflict_free:
            violations += [(i, a, a) for a in sorted(Ai, key=str) if (a, a) in game.attacks]
        for alpha in sorted(Ai, key=str):
            for beta in sorted(Ai, key=str):
                if alpha == beta and not include_same:
                    continue
                if test(adj, alpha, beta):
                    violations.append((i, alpha, beta))
    violations = list(dict.fromkeys(violations))  # a self-attack can be reported twice
    return Theorem54Result(not violations, violations)

"""
Part 1 - Argumentation engine for Dung-style abstract argumentation frameworks.

An argumentation framework (AF) is a pair <A, ->> where A is a finite set of
arguments and -> is a binary "attacks" relation on A.  Everything in this module
is a plain function that takes an ``ArgumentationFramework`` (plus, where
needed, a set ``S`` of arguments), so each assignment item maps to one function:

    1  ArgumentationFramework                       (the class)
    2  is_conflict_free(af, S)
    3  is_defended(af, a, S)
    4  characteristic_function(af, S)
    5  is_admissible(af, S), is_complete(af, S)
    6A grounded_extension(af)
    6B complete_extensions(af)
    6C preferred_extensions / stable_extensions / semi_stable_extensions
       (and all_extensions, which returns all of them at once)
    6D all_legal_labellings(af)
    6E acceptance_status(af, a)

Extension-based semantics are computed by exhaustive search over subsets of the
arguments, which is the clearest faithful reading of the definitions and is
perfectly adequate for the small frameworks used in the assignment (<= ~15
arguments).
"""

from itertools import chain, combinations, product

# --------------------------------------------------------------------------- #
# 1. The framework class
# --------------------------------------------------------------------------- #


class ArgumentationFramework:
    """A finite abstract argumentation framework <A, ->>.

    ``arguments`` is any iterable of hashable items, ``attacks`` an iterable of
    ``(attacker, target)`` pairs.  Self-attacks ``(a, a)`` are allowed.
    The object is immutable by convention (sets are frozen after construction).
    """

    def __init__(self, arguments, attacks=()):
        self.arguments = frozenset(arguments)
        self.attacks = frozenset((a, b) for a, b in attacks)
        for a, b in self.attacks:
            if a not in self.arguments or b not in self.arguments:
                raise ValueError(f"attack ({a!r}, {b!r}) mentions an unknown argument")
        self._attackers = {x: set() for x in self.arguments}
        self._targets = {x: set() for x in self.arguments}
        for a, b in self.attacks:
            self._attackers[b].add(a)
            self._targets[a].add(b)

    # -- construction helpers ------------------------------------------------
    @classmethod
    def parse(cls, text):
        """Build an AF from a compact string, e.g. ``"a->b, b->a, c"``.

        ``x->y`` is an attack; a bare token declares an argument with no
        attacks.  ``x<->y`` is shorthand for a mutual attack.
        """
        arguments, attacks = set(), set()
        for token in text.replace(";", ",").split(","):
            token = token.strip()
            if not token:
                continue
            if "<->" in token:
                x, y = (s.strip() for s in token.split("<->"))
                attacks |= {(x, y), (y, x)}
                arguments |= {x, y}
            elif "->" in token:
                x, y = (s.strip() for s in token.split("->"))
                attacks.add((x, y))
                arguments |= {x, y}
            else:
                arguments.add(token)
        return cls(arguments, attacks)

    # -- basic queries -------------------------------------------------------
    def attackers_of(self, a):
        """The set of arguments that attack ``a``."""
        return frozenset(self._attackers[a])

    def targets_of(self, a):
        """The set of arguments attacked by ``a``."""
        return frozenset(self._targets[a])

    def attacked_by(self, S):
        """S+ : every argument attacked by some member of ``S``."""
        out = set()
        for a in S:
            out |= self._targets[a]
        return frozenset(out)

    def induced(self, subset):
        """The sub-framework induced by ``subset`` (attacks inside it only)."""
        subset = frozenset(subset)
        if not subset <= self.arguments:
            raise ValueError("subset contains unknown arguments")
        return ArgumentationFramework(
            subset, {(a, b) for a, b in self.attacks if a in subset and b in subset}
        )

    def __repr__(self):
        atk = ", ".join(f"{a}->{b}" for a, b in sorted(self.attacks, key=str))
        return f"AF(args={sorted(self.arguments, key=str)}, attacks=[{atk}])"


def _check_subset(af, S):
    S = frozenset(S)
    if not S <= af.arguments:
        raise ValueError(f"{set(S - af.arguments)} are not arguments of the framework")
    return S


def powerset(items):
    """All subsets of ``items`` as frozensets (smallest first)."""
    items = list(items)
    return (
        frozenset(c)
        for c in chain.from_iterable(combinations(items, r) for r in range(len(items) + 1))
    )


def _maximal(sets):
    """The subset-maximal members of a collection of frozensets."""
    sets = list(sets)
    return [s for s in sets if not any(s < t for t in sets)]


def _sorted(exts):
    """Deterministic ordering for lists of extensions (for printing/testing)."""
    return sorted(exts, key=lambda s: (len(s), sorted(map(str, s))))


# --------------------------------------------------------------------------- #
# 2-5. Basic notions
# --------------------------------------------------------------------------- #


def is_conflict_free(af, S):
    """S is conflict-free iff no member of S attacks a member of S."""
    S = _check_subset(af, S)
    return not any(b in S for a in S for b in af.targets_of(a))


def is_defended(af, a, S):
    """Is ``a`` defended by (acceptable w.r.t.) ``S``?

    True iff every attacker b of a is itself attacked by some member of S.
    (An unattacked argument is defended by every set, including the empty set.)
    """
    S = _check_subset(af, S)
    return all(af.attackers_of(b) & S for b in af.attackers_of(a))


def characteristic_function(af, S):
    """F(S): the set of all arguments defended by S."""
    S = _check_subset(af, S)
    return frozenset(a for a in af.arguments if is_defended(af, a, S))


def is_admissible(af, S):
    """S is admissible iff it is conflict-free and defends all of its members."""
    S = _check_subset(af, S)
    return is_conflict_free(af, S) and S <= characteristic_function(af, S)


def is_complete(af, S):
    """S is a complete extension iff it is admissible and contains every
    argument it defends (i.e. S is a conflict-free fixed point of F)."""
    S = _check_subset(af, S)
    return is_admissible(af, S) and characteristic_function(af, S) <= S


# --------------------------------------------------------------------------- #
# 6A-6C. Extensions
# --------------------------------------------------------------------------- #


def grounded_extension(af):
    """The grounded extension: least fixed point of F, reached by iterating F
    from the empty set (F is monotone and the AF is finite)."""
    S = frozenset()
    while True:
        nxt = characteristic_function(af, S)
        if nxt == S:
            return S
        S = nxt


def admissible_sets(af):
    """All admissible sets (including the empty set)."""
    candidates = [a for a in af.arguments if a not in af.attackers_of(a)]
    return _sorted(S for S in powerset(candidates) if is_admissible(af, S))


def complete_extensions(af):
    """All complete extensions.

    Every complete extension contains the grounded extension and cannot contain
    a self-attacking argument, so only the remaining arguments are enumerated.
    """
    base = grounded_extension(af)
    free = [a for a in af.arguments if a not in base and a not in af.attackers_of(a)]
    found = []
    for extra in powerset(free):
        S = base | extra
        if is_complete(af, S):
            found.append(S)
    return _sorted(found)


def preferred_extensions(af):
    """Preferred extensions: the subset-maximal admissible sets."""
    return _sorted(_maximal(admissible_sets(af)))


def stable_extensions(af):
    """Stable extensions: conflict-free sets that attack every argument outside
    them.  (Every stable extension is complete, so we search those.)"""
    return _sorted(
        S for S in complete_extensions(af) if S | af.attacked_by(S) == af.arguments
    )


def semi_stable_extensions(af):
    """Semi-stable extensions: complete extensions whose range S u S+ is
    maximal (w.r.t. set inclusion) among all complete extensions."""
    complete = complete_extensions(af)
    rng = {S: S | af.attacked_by(S) for S in complete}
    return _sorted(S for S in complete if not any(rng[S] < rng[T] for T in complete))


def all_extensions(af):
    """Grounded, complete, preferred, stable and semi-stable extensions."""
    return {
        "grounded": [grounded_extension(af)],
        "complete": complete_extensions(af),
        "preferred": preferred_extensions(af),
        "stable": stable_extensions(af),
        "semi-stable": semi_stable_extensions(af),
    }


# --------------------------------------------------------------------------- #
# 6D. Labellings
# --------------------------------------------------------------------------- #

IN, OUT, UNDEC = "in", "out", "undec"


def is_legal_labelling(af, labelling):
    """Caminada's legality conditions for a total labelling ``{arg: label}``:

    * in    iff every attacker is out
    * out   iff some attacker is in
    * undec otherwise (no attacker is in, and some attacker is not out)
    """
    if set(labelling) != set(af.arguments):
        return False
    for a in af.arguments:
        attacker_labels = [labelling[b] for b in af.attackers_of(a)]
        all_out = all(l == OUT for l in attacker_labels)
        some_in = any(l == IN for l in attacker_labels)
        expected = IN if all_out else OUT if some_in else UNDEC
        if labelling[a] != expected:
            return False
    return True


def all_legal_labellings(af):
    """Every legal in/out/undec labelling, found by checking all 3^n labellings.

    Legal labellings are in 1-1 correspondence with complete extensions
    (the 'in' set); this function does not rely on that fact, the tests verify it.
    """
    args = sorted(af.arguments, key=str)
    found = []
    for combo in product((IN, OUT, UNDEC), repeat=len(args)):
        labelling = dict(zip(args, combo))
        if is_legal_labelling(af, labelling):
            found.append(labelling)
    return found


def labelling_to_extension(labelling):
    """The 'in' set of a labelling."""
    return frozenset(a for a, l in labelling.items() if l == IN)


def extension_to_labelling(af, S):
    """Labelling induced by a set S: in = S, out = S+, undec = the rest."""
    S = _check_subset(af, S)
    out = af.attacked_by(S)
    return {a: IN if a in S else OUT if a in out else UNDEC for a in af.arguments}


# --------------------------------------------------------------------------- #
# 6E. Acceptance status
# --------------------------------------------------------------------------- #

SKEPTICAL = "skeptically accepted"
CREDULOUS = "credulously accepted"
REJECTED = "rejected"

_SEMANTICS = {
    "grounded": lambda af: [grounded_extension(af)],
    "complete": complete_extensions,
    "preferred": preferred_extensions,
    "stable": stable_extensions,
    "semi-stable": semi_stable_extensions,
}


def acceptance_status(af, a, semantics="preferred"):
    """Status of argument ``a`` under the chosen semantics (default preferred).

    * skeptically accepted : a is in *every* extension
    * credulously accepted : a is in *some* but not every extension
    * rejected             : a is in no extension

    Convention: if the semantics yields no extension at all (possible for
    stable), nothing is accepted, so the status is ``rejected``.
    """
    if a not in af.arguments:
        raise ValueError(f"{a!r} is not an argument of the framework")
    extensions = _SEMANTICS[semantics](af)
    if not extensions:
        return REJECTED
    if all(a in E for E in extensions):
        return SKEPTICAL
    if any(a in E for E in extensions):
        return CREDULOUS
    return REJECTED

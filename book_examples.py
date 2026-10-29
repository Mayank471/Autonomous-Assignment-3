"""
The frameworks of Chapter 5 ("Argumentation", Rahwan) of the course textbook
*Multiagent Systems* (multiagent-systems_compress.pdf), encoded exactly as drawn /
stated in the book.  Arguments are named as in the book: alpha_k -> k (int),
and a..e (str) for Figure 5.3.

    Figure 5.1  (Examples 5.5, 5.6, 5.8)  alpha3->alpha2->alpha1<-alpha4<-alpha5
    Figure 5.2  (Examples 5.7, 5.8)       alpha1 <-> alpha2, alpha3 on its own
    Figure 5.3  (Example 5.9)             b->a, c->b, d->b, c<->d, e->d
    Example 5.10 / Figure 5.4             x={1,4,5}, y={2}, z={3},  R={(1,2),(2,3),(3,4),(3,5)}
    Example 5.11 / Figure 5.5             Example 5.10 plus argument 6 (agent x) and defeat (6,3)

Agent order in the games is (x, y, z) = (0, 1, 2).
"""

from argumentation import ArgumentationFramework
from strategic import StrategicGame

X, Y, Z = 0, 1, 2
AGENT_NAMES = {X: "x", Y: "y", Z: "z"}


def figure_5_1():
    return ArgumentationFramework({1, 2, 3, 4, 5}, {(3, 2), (5, 4), (2, 1), (4, 1)})


def figure_5_2():
    return ArgumentationFramework({1, 2, 3}, {(1, 2), (2, 1)})


def figure_5_3():
    return ArgumentationFramework(
        set("abcde"), {("b", "a"), ("c", "b"), ("d", "b"), ("c", "d"), ("d", "c"), ("e", "d")}
    )


EXAMPLE_5_10_ATTACKS = {(1, 2), (2, 3), (3, 4), (3, 5)}


def example_5_10():
    """Three agents with A_x = {1,4,5}, A_y = {2}, A_z = {3}."""
    return StrategicGame(EXAMPLE_5_10_ATTACKS, [{1, 4, 5}, {2}, {3}])


def example_5_11():
    """Example 5.10 plus argument 6 owned by x and the defeat (6, 3)."""
    return StrategicGame(EXAMPLE_5_10_ATTACKS | {(6, 3)}, [{1, 4, 5, 6}, {2}, {3}])

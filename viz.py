"""
Shared drawing helpers for the report figures (make_figures.py) and the interactive
demo (live_demo.py): a colour-blind-safe palette and an argument-graph renderer whose
node colours come from the engine's own grounded labelling.
"""
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, Patch

from argumentation import ArgumentationFramework, grounded_extension

# colour-blind-safe palette (Okabe-Ito)
BLUE, ORANGE, GREEN, RED, PURPLE, GREY, SKY = (
    "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#7a7a7a", "#56B4E9")
IN_C, OUT_C, UNDEC_C = "#8fd3b6", "#f2a490", "#e6e6e6"
OWNER_C = {0: BLUE, 1: ORANGE, 2: PURPLE}
FILL = {"in": IN_C, "out": OUT_C, "undec": UNDEC_C, None: "white"}

NODE_RADIUS = 0.17  # in data units
ARROW_SHRINK = 13   # points, so arrow heads stop at the node border


def draw_graph(ax, pos, attacks, label=None, owner=None, hidden=(), title=None, names=None,
               node_size=1.0, title_size=9.5, auto_shrink=False):
    """Draw an attack graph on ``ax``.

    pos      {argument: (x, y)}
    attacks  iterable of (attacker, target); attacks touching a hidden argument are not drawn
    label    {argument: "in" | "out" | "undec"} -> node fill (None = white)
    owner    {argument: agent index} -> ring colour (None = neutral ring)
    hidden   arguments drawn as dashed empty circles (not revealed)
    auto_shrink  measure the node radius on screen so arrow heads stop exactly at the border
                 (needed when nodes are drawn large; the fixed default suits the report figures)
    """
    ax.set_aspect("equal")
    ax.axis("off")
    ax.grid(False)
    xs, ys = zip(*pos.values())
    ax.set_xlim(min(xs) - 0.5, max(xs) + 0.5)
    ax.set_ylim(min(ys) - 0.5, max(ys) + 0.55)
    names = names or {}
    r = NODE_RADIUS * node_size
    shrink = ARROW_SHRINK * node_size
    if auto_shrink:
        ax.apply_aspect()
        radius_px = ax.transData.transform((r, 0))[0] - ax.transData.transform((0, 0))[0]
        shrink = radius_px * 72 / ax.figure.dpi + 1.5
    attacks = set(attacks)
    for a, b in sorted(attacks, key=str):
        if a in hidden or b in hidden:
            continue
        if a == b:
            x, y = pos[a]
            ax.add_patch(FancyArrowPatch((x - 0.09, y + r), (x + 0.09, y + r), connectionstyle="arc3,rad=-3.0",
                                         arrowstyle="-|>", mutation_scale=11, lw=1.3, color="#333333",
                                         shrinkA=0, shrinkB=0, zorder=1))
            continue
        rad = 0.3 if (b, a) in attacks else 0.0  # mutual attack: bend the two arrows apart
        ax.add_patch(FancyArrowPatch(pos[a], pos[b], connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
                                     mutation_scale=13, lw=1.5, color="#333333", shrinkA=shrink, shrinkB=shrink,
                                     zorder=1))
    for a, (x, y) in pos.items():
        if a in hidden:
            ax.add_patch(Circle((x, y), r, fc="white", ec="#999999", lw=1.2, ls=(0, (3, 2)), zorder=2))
            ax.text(x, y, names.get(a, str(a)), ha="center", va="center", fontsize=10, color="#999999", zorder=3)
            continue
        fc = FILL[label.get(a) if label else None]
        ec = OWNER_C[owner[a]] if owner else "#333333"
        ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=2.8 if owner else 1.4, zorder=2))
        ax.text(x, y, names.get(a, str(a)), ha="center", va="center", fontsize=10.5, fontweight="bold", zorder=3)
    if title:
        ax.set_title(title, fontsize=title_size, pad=2)


def labels_from_extension(af, extension):
    """in / out / undec labelling induced by an extension: out = attacked by the extension."""
    extension = set(extension)
    out = af.attacked_by(extension)
    return {a: ("in" if a in extension else "out" if a in out else "undec") for a in af.arguments}


def grounded_label(attacks, args):
    """Grounded labelling of the framework (args, attacks), computed by the engine."""
    af = ArgumentationFramework(set(args), set(attacks))
    return labels_from_extension(af, grounded_extension(af))


def revealed_label(attacks, revealed):
    """Grounded labelling of the framework induced by the revealed arguments."""
    induced = {(a, b) for a, b in attacks if a in revealed and b in revealed}
    return grounded_label(induced, revealed)


LABEL_LEGEND = [Patch(fc=IN_C, ec="#333", label="in (grounded)"), Patch(fc=OUT_C, ec="#333", label="out"),
                Patch(fc=UNDEC_C, ec="#333", label="undecided")]


def owner_legend(agent_names):
    return [Line2D([], [], marker="o", mfc="white", mec=OWNER_C[i], mew=2.4, ls="", ms=9, label=f"agent {n}")
            for i, n in enumerate(agent_names)]


HIDDEN_LEGEND = Line2D([], [], marker="o", mfc="white", mec="#999", mew=1.2, ls="", ms=9, label="hidden")


# Node layouts of the textbook examples, shared by the report figures and the live demo.
LAYOUTS = {
    "fig51": {3: (0, 0.6), 2: (1, 0.6), 1: (2, 0.3), 4: (1, 0), 5: (0, 0)},
    "fig52": {1: (0, 0.2), 2: (1.3, 0.2), 3: (0.65, -0.7)},
    "fig53": {"e": (0, 0), "d": (1, 0), "c": (2, 0), "b": (1.5, 1.0), "a": (2.5, 1.0)},
    "ex510": {1: (0, 0), 2: (1, 0), 3: (2, 0), 4: (3, 0.45), 5: (3, -0.45)},
    "ex511": {1: (0, 0), 2: (1, 0), 3: (2, 0), 4: (3, 0.45), 5: (3, -0.45), 6: (2, 1.0)},
}

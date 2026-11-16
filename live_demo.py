"""
Interactive visual demo of the argumentation engine and the grounded direct mechanism.

    python live_demo.py                    # open the window (start with the book's Example 5.10)
    python live_demo.py --preset fig53     # start on another example
    python live_demo.py --export frames    # no window: save a PNG sequence (backup for slides / no display)

In the window
    click an argument   reveal / hide it (hidden = dashed circle); everything is recomputed by the real engine
    Step  (n / ->)      walk through the grounded extension: F^0(empty) -> F^1 -> F^2 -> ... until the fixed point
    Play  (p)           same, automatically
    Best deviation (b)  let the first agent that can gain deviate to its best response (Example 5.10: x hides 1)
    Reveal all (a)      back to the truthful profile
    1 ... 6             switch example

Colours: green = in the grounded extension, red = out (attacked by it), grey = undecided, white = not decided yet
(step mode); the ring colour of a node is its owner (agent), a dashed circle is an argument its owner hides.
"""
import argparse
import os
import textwrap

import matplotlib

from argumentation import ArgumentationFramework, characteristic_function, complete_extensions, \
    grounded_extension, preferred_extensions, stable_extensions
from book_examples import example_5_10, example_5_11, figure_5_1, figure_5_2, figure_5_3
from strategic import (StrategicGame, _CachedMechanism, best_responses, is_strategyproof,
                       satisfies_theorem_5_4, utility)
from viz import BLUE, LAYOUTS, draw_graph, labels_from_extension, owner_legend

AGENT_NAMES = "xyz"
PLAY_INTERVAL_MS = 1100
WRAP = 58

# --------------------------------------------------------------------------- #
# Presets: frameworks (no owners) and games (owners = one argument set per agent)
# --------------------------------------------------------------------------- #

_MANIP = StrategicGame({(1, 3), (3, 1), (1, 2)}, [{1, 2}, {3}])

PRESETS = {
    "ex510": dict(
        short="Example 5.10",
        title="Example 5.10: the mechanism is manipulable", layout="ex510", game=example_5_10(),
        note="Click argument 1 to hide it: x's utility goes from 1 to 2. Then press 'Best deviation'."),
    "ex511": dict(
        short="Example 5.11",
        title="Example 5.11: truth-telling is dominant", layout="ex511", game=example_5_11(),
        note="The condition of Theorem 5.4 fails, yet nobody gains: hide 1 and x only loses (4 -> 3)."),
    "fig51": dict(
        short="Figure 5.1",
        title="Figure 5.1: a chain of defences", layout="fig51", framework=figure_5_1(),
        names={k: f"α{k}" for k in range(1, 6)},
        note="Press Step: F(empty) = {3,5}, then {1,3,5}. Hide 3 or 5 and watch 1 lose its defence."),
    "fig52": dict(
        short="Figure 5.2",
        title="Figure 5.2: a mutual attack", layout="fig52", framework=figure_5_2(),
        names={k: f"α{k}" for k in range(1, 4)},
        note="The grounded labelling leaves 1 and 2 undecided; the two preferred extensions pick one each."),
    "fig53": dict(
        short="Figure 5.3",
        title="Figure 5.3: c and d attack each other", layout="fig53", framework=figure_5_3(),
        note="e is unattacked, so it kills d, which frees c and then a. Hide e and everything stalls."),
    "alpha": dict(
        short="Hide α pays off",
        title="Hiding an argument pays off", layout=None, game=_MANIP, names={1: "α", 2: "β", 3: "δ"},
        pos={1: (0, 0), 2: (1.3, 0.55), 3: (1.3, -0.55)},
        note="Agent x owns alpha and beta. Truthfully all three are undecided (u=0). Hide alpha: u=1."),
}
ORDER = ["ex510", "ex511", "fig51", "fig52", "fig53", "alpha"]


def fmt(items, names):
    """{1, 3} for a collection of arguments, sorted, using display names."""
    shown = sorted((names.get(a, str(a)) for a in items), key=str)
    return "{" + ", ".join(shown) + "}" if shown else "∅"


class LiveDemo:
    def __init__(self, plt, preset="ex510"):
        self.plt = plt
        self.fig = plt.figure(figsize=(13.6, 7.4))
        try:
            self.fig.canvas.manager.set_window_title("Argumentation: live demo")
        except Exception:  # headless backends have no window manager
            pass
        self.ax_graph = self.fig.add_axes([0.02, 0.17, 0.60, 0.70])
        self.ax_info = self.fig.add_axes([0.635, 0.17, 0.355, 0.73])
        self.ax_info.axis("off")
        self.ax_legend = self.fig.add_axes([0.02, 0.125, 0.60, 0.04])
        self.ax_legend.axis("off")
        self.timer = None
        self._widgets = []
        self._build_controls()
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.load(preset)

    # ---------------------------------------------------------------- controls
    def _button(self, rect, label, callback, color="#e8eef7"):
        from matplotlib.widgets import Button
        ax = self.fig.add_axes(rect)
        btn = Button(ax, label, color=color, hovercolor="#cfdcf0")
        btn.on_clicked(lambda _e: callback())
        self._widgets.append(btn)
        return btn

    def _build_controls(self):
        n = len(ORDER)
        for i, key in enumerate(ORDER):
            self._button([0.02 + i * 0.158, 0.925, 0.150, 0.05], f"{i + 1}  {PRESETS[key]['short']}",
                         lambda k=key: self.load(k), color="#f3efe0")
        w = 0.15
        for i, (label, cb) in enumerate([("Step  (n)", self.step), ("Play / pause  (p)", self.toggle_play),
                                         ("Best deviation  (b)", self.best_deviation),
                                         ("Reveal all  (a)", self.reveal_all), ("Reset steps  (r)", self.reset_steps)]):
            self._button([0.02 + i * (w + 0.012), 0.065, w, 0.055], label, cb)
        self.fig.text(0.02, 0.025, "click an argument to reveal / hide it   |   keys: n step, p play, b best deviation, "
                      "a reveal all, r reset, 1-6 examples", fontsize=9, color="#555555")

    # ---------------------------------------------------------------- state
    def load(self, key):
        self.stop_play()
        self.key = key
        p = PRESETS[key]
        self.preset = p
        self.game = p.get("game")
        if self.game is not None:
            self.attacks = set(self.game.attacks)
            self.arguments = set(self.game.arguments)
            self.owner = {a: i for i, A in enumerate(self.game.agent_arguments) for a in A}
            self.verdict = self._whole_game_verdict()
        else:
            af = p["framework"]
            self.attacks, self.arguments, self.owner, self.verdict = set(af.attacks), set(af.arguments), None, None
        self.pos = p.get("pos") or LAYOUTS[p["layout"]]
        self.names = p.get("names", {})
        self.revealed = set(self.arguments)
        self.step_k = None
        self.message = ""
        self.render()

    def induced(self):
        return ArgumentationFramework(set(self.revealed), {(a, b) for a, b in self.attacks
                                                           if a in self.revealed and b in self.revealed})

    def grounded_frames(self):
        """F^0(empty), F^1(empty), ... up to the least fixed point, on the induced framework."""
        af = self.induced()
        frames = [frozenset()]
        while True:
            nxt = frozenset(characteristic_function(af, frames[-1]))
            if nxt == frames[-1]:
                return frames
            frames.append(nxt)

    def _whole_game_verdict(self):
        sp = is_strategyproof(self.game)
        cond = satisfies_theorem_5_4(self.game)
        return {"sp": sp.holds, "manipulators": sorted({c["agent"] for c in sp.counterexamples}),
                "cond": cond.holds, "violations": cond.violations}

    # ---------------------------------------------------------------- actions
    def toggle(self, a):
        self.revealed ^= {a}
        self.step_k = None
        self.message = f"{'revealed' if a in self.revealed else 'hid'} argument {self.names.get(a, a)}"
        self.render()

    def reveal_all(self):
        self.revealed = set(self.arguments)
        self.step_k = None
        self.message = "everything revealed (truthful profile)"
        self.render()

    def reset_steps(self):
        self.stop_play()
        self.step_k = None
        self.message = ""
        self.render()

    def step(self):
        frames = self.grounded_frames()
        self.step_k = 0 if self.step_k is None else min(self.step_k + 1, len(frames) - 1)
        if self.step_k == len(frames) - 1:
            self.stop_play()
        self.render()

    def toggle_play(self):
        if self.timer is not None:
            self.stop_play()
            return
        self.step_k = None
        self.timer = self.fig.canvas.new_timer(interval=PLAY_INTERVAL_MS)
        self.timer.add_callback(self.step)
        self.timer.start()
        self.step()

    def stop_play(self):
        if self.timer is not None:
            self.timer.stop()
            self.timer = None

    def best_deviation(self):
        """The first agent that can gain by deviating (given the others' current reports) deviates."""
        if self.game is None:
            self.message = "this example has no agents: pick Example 5.10, 5.11 or the last one"
            self.render()
            return
        self.step_k = None
        mech = _CachedMechanism(self.game.attacks)
        for i in range(self.game.n_agents):
            others = self._others(i)
            br = best_responses(self.game, i, others, mech)
            now = utility(self.game, i, mech([*others.values(), self._report(i)]))
            if br.utility > now:
                best = max(br.reports, key=lambda r: (len(r), sorted(map(str, r))))
                self.revealed = (self.revealed - self.game.agent_arguments[i]) | set(best)
                hidden = self.game.agent_arguments[i] - set(best)
                self.message = (f"agent {AGENT_NAMES[i]} deviates: hides {fmt(hidden, self.names)}, "
                                f"utility {now} -> {br.utility}")
                self.render()
                return
        self.message = "no agent can gain by deviating from the current profile"
        self.render()

    def _report(self, i):
        return frozenset(self.revealed & self.game.agent_arguments[i])

    def _others(self, i):
        return {j: self._report(j) for j in range(self.game.n_agents) if j != i}

    # ---------------------------------------------------------------- events
    def on_click(self, event):
        if event.inaxes is not self.ax_graph or event.xdata is None:
            return
        a, d = min(((a, (event.xdata - x) ** 2 + (event.ydata - y) ** 2) for a, (x, y) in self.pos.items()),
                   key=lambda t: t[1])
        if d <= 0.30 ** 2:
            self.toggle(a)

    def on_key(self, event):
        k = (event.key or "").lower()
        if k in ("n", "right", " "):
            self.step()
        elif k == "p":
            self.toggle_play()
        elif k == "b":
            self.best_deviation()
        elif k == "a":
            self.reveal_all()
        elif k == "r":
            self.reset_steps()
        elif k.isdigit() and 1 <= int(k) <= len(ORDER):
            self.load(ORDER[int(k) - 1])

    # ---------------------------------------------------------------- drawing
    def render(self):
        af = self.induced()
        grounded = grounded_extension(af)
        frames = self.grounded_frames()
        if self.step_k is None:
            label = labels_from_extension(af, grounded)
        else:
            shown = frames[self.step_k]
            label = labels_from_extension(af, shown)
            if self.step_k < len(frames) - 1:  # not final yet: undecided means "not decided yet"
                label = {a: (None if v == "undec" else v) for a, v in label.items()}
        self.ax_graph.clear()
        hidden = self.arguments - self.revealed
        draw_graph(self.ax_graph, self.pos, self.attacks, label=label, owner=self.owner, hidden=hidden,
                   names={a: self.names.get(a, str(a)) for a in self.pos}, node_size=1.5, title_size=13, auto_shrink=True,
                   title=self.preset["title"])
        self.ax_legend.clear()
        self.ax_legend.axis("off")
        if self.owner is not None:
            self.ax_legend.legend(handles=owner_legend(AGENT_NAMES[:self.game.n_agents]), loc="center",
                                  ncol=self.game.n_agents, frameon=False, fontsize=10)
        self._draw_info(af, grounded, frames)
        self.fig.canvas.draw_idle()

    def _info_lines(self, af, grounded, frames):
        nm = self.names
        L = []  # (text, style)
        L.append(("What you see", "h"))
        L.append((self.preset["note"], "m"))
        if self.message:
            L.append(("▶ " + self.message, "b"))
        L.append(("", "n"))
        if self.step_k is not None:
            k = self.step_k
            final = k == len(frames) - 1
            L.append((f"Grounded iteration, step {k} of {len(frames) - 1}", "h"))
            L.append((f"F^{k}(∅) = {fmt(frames[k], nm)}", "n"))
            if k > 0:
                L.append((f"newly defended: {fmt(frames[k] - frames[k - 1], nm)}", "n"))
            L.append(("fixed point reached: this is the grounded extension" if final
                      else "white = not decided yet; press Step again", "g" if final else "m"))
            L.append(("", "n"))
        L.append(("Outcome of the current reports", "h"))
        L.append((f"revealed: {fmt(self.revealed, nm)}", "n"))
        L.append((f"grounded extension: {fmt(grounded, nm)}", "n"))
        if self.game is None:
            for name, f in (("complete", complete_extensions), ("preferred", preferred_extensions),
                            ("stable", stable_extensions)):
                exts = f(af)
                L.append((f"{name}: " + (", ".join(fmt(e, nm) for e in exts) if exts else "none"), "n"))
        else:
            L += self._game_lines(grounded)
        return L

    def _game_lines(self, grounded):
        nm, g = self.names, self.game
        L = [("", "n"), ("Agents (utility = own accepted arguments)", "h")]
        mech = _CachedMechanism(g.attacks)
        for i in range(g.n_agents):
            others = self._others(i)
            u = utility(g, i, grounded)
            br = best_responses(g, i, others, mech)
            tag = AGENT_NAMES[i]
            if br.utility > u:
                best = max(br.reports, key=lambda r: (len(r), sorted(map(str, r))))
                L.append((f"{tag}: u = {u}, but can get {br.utility} by revealing {fmt(best, nm)}", "r"))
            else:
                L.append((f"{tag}: u = {u}  (best response given the others)", "g"))
        v = self.verdict
        L += [("", "n"), ("Whole game (all reports of all agents)", "h")]
        if v["sp"]:
            L.append(("Thm 5.3: strategyproof, truth is dominant", "g"))
        else:
            who = ", ".join(AGENT_NAMES[i] for i in v["manipulators"])
            L.append((f"Thm 5.3: NOT strategyproof (agent {who} can gain)", "r"))
        if v["cond"]:
            L.append(("Thm 5.4 condition: holds (no odd path inside an agent's set)", "g"))
        else:
            shown = ", ".join(f"({AGENT_NAMES[i]}; {nm.get(a, a)}, {nm.get(b, b)})" for i, a, b in v["violations"][:3])
            more = " ..." if len(v["violations"]) > 3 else ""
            L.append((f"Thm 5.4 condition: violated by {shown}{more}", "r" if not v["sp"] else "m"))
        if v["sp"] and not v["cond"]:
            L.append(("-> strategyproof although the condition fails: it is sufficient, not necessary", "m"))
        return L

    def _draw_info(self, af, grounded, frames):
        ax = self.ax_info
        ax.clear()
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        style = {"h": dict(fontweight="bold", fontsize=11.5, color="#222222"), "n": dict(color="#222222"),
                 "m": dict(color="#666666", style="italic"), "g": dict(color="#00704f"),
                 "r": dict(color="#b23c00"), "b": dict(color=BLUE, fontweight="bold")}
        y = 0.99
        for text, kind in self._info_lines(af, grounded, frames):
            if not text:
                y -= 0.022
                continue
            for line in textwrap.wrap(text, WRAP, subsequent_indent="   ") or [""]:
                ax.text(0.0, y, line, va="top", ha="left", fontsize=style[kind].get("fontsize", 10.5),
                        **{k: v for k, v in style[kind].items() if k != "fontsize"})
                y -= 0.043 if kind != "h" else 0.050


def export_frames(plt, out_dir):
    """Save the storyline of every example as PNGs (no window needed)."""
    os.makedirs(out_dir, exist_ok=True)
    demo = LiveDemo(plt)
    count = 0

    def snap(tag):
        nonlocal count
        count += 1
        demo.fig.savefig(os.path.join(out_dir, f"{demo.key}_{count:02d}_{tag}.png"), dpi=110)

    for key in ORDER:
        demo.load(key)
        count = 0
        snap("start")
        for _ in range(len(demo.grounded_frames())):
            demo.step()
            snap(f"step{demo.step_k}")
        demo.reveal_all()
        if demo.game is not None:
            demo.best_deviation()
            snap("best_deviation")
    print(f"frames written to {out_dir}/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", choices=ORDER, default="ex510")
    ap.add_argument("--export", metavar="DIR", help="write PNG frames to DIR instead of opening a window")
    args = ap.parse_args()
    if args.export:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if args.export:
        export_frames(plt, args.export)
        return
    demo = LiveDemo(plt, args.preset)  # keep a reference: widgets die with the object
    plt.show()
    del demo


if __name__ == "__main__":
    main()

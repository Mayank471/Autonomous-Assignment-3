"""
Generates every figure of the report into figures/ (vector PDF + PNG preview).

    python extra_stats.py     # once, writes results/extra_stats.json
    python make_figures.py

Data comes from results/summary.json, results/q3_strategyproof_but_condition_fails.csv,
results/extra_stats.json and from the engine itself (the argument-graph drawings are
labelled by the real grounded extension).
"""
import csv
import json
import math
import os
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from book_examples import EXAMPLE_5_10_ATTACKS, figure_5_1, figure_5_2, figure_5_3
from strategic import grounded_direct_mechanism
from viz import (BLUE, GREEN, GREY, HIDDEN_LEGEND, LABEL_LEGEND, ORANGE, PURPLE, RED, SKY, draw_graph,
                 LAYOUTS, grounded_label, owner_legend, revealed_label)

OUT = "figures"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10, "legend.fontsize": 9,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.alpha": 0.25, "figure.dpi": 150, "pdf.fonttype": 42,
})

with open("results/summary.json") as f:
    summary = json.load(f)
with open("results/extra_stats.json") as f:
    extra = json.load(f)
P = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
N_PER_P = summary["instances_per_p"]


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf", bbox_inches="tight")
    fig.savefig(f"{OUT}/{name}.png", bbox_inches="tight", dpi=170)
    plt.close(fig)
    print("wrote", name)


def wilson(k, n, z=1.96):
    """Wilson score interval for a binomial proportion."""
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


# --------------------------------------------------------------------------- #
# Argument-graph figures (drawing code lives in viz.py)
# --------------------------------------------------------------------------- #


def fig_book_frameworks():
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 2.7), gridspec_kw={"width_ratios": [1.6, 1.0, 1.35]})
    f1 = figure_5_1()
    pos1 = LAYOUTS["fig51"]
    draw_graph(axes[0], pos1, f1.attacks, grounded_label(f1.attacks, f1.arguments),
               title="Fig. 5.1  (Ex. 5.5, 5.6, 5.8)", names={k: rf"$\alpha_{k}$" for k in pos1})
    f2 = figure_5_2()
    pos2 = LAYOUTS["fig52"]
    draw_graph(axes[1], pos2, f2.attacks, grounded_label(f2.attacks, f2.arguments),
               title="Fig. 5.2  (Ex. 5.7, 5.8)", names={k: rf"$\alpha_{k}$" for k in pos2})
    f3 = figure_5_3()
    pos3 = LAYOUTS["fig53"]
    draw_graph(axes[2], pos3, f3.attacks, grounded_label(f3.attacks, f3.arguments), title="Fig. 5.3  (Ex. 5.9)")
    fig.legend(handles=LABEL_LEGEND, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout()
    save(fig, "fig_book_frameworks")


def fig_manipulation_examples():
    """Example 5.10 (manipulable) and Example 5.11 (truth-telling is dominant), truthful vs. x hides 1."""
    pos = LAYOUTS["ex510"]
    owner = {1: 0, 4: 0, 5: 0, 2: 1, 3: 2}
    att = EXAMPLE_5_10_ATTACKS
    pos2 = LAYOUTS["ex511"]
    owner2 = {**owner, 6: 0}
    att2 = att | {(6, 3)}
    cases = [
        (pos, owner, att, set(pos), set(), "Ex. 5.10: x reveals all of {1,4,5}"),
        (pos, owner, att, set(pos) - {1}, {1}, "Ex. 5.10: x hides 1"),
        (pos2, owner2, att2, set(pos2), set(), "Ex. 5.11: x reveals all of {1,4,5,6}"),
        (pos2, owner2, att2, set(pos2) - {1}, {1}, "Ex. 5.11: x hides 1"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(9.4, 5.0))
    for ax, (ps, ow, at, rev, hid, ttl) in zip(axes.flat, cases):
        out = grounded_direct_mechanism(at, [rev])
        u_x = sum(1 for a in out if ow[a] == 0)
        draw_graph(ax, ps, at, revealed_label(at, rev), ow, hidden=hid, names={k: str(k) for k in ps},
                   title=f"{ttl}\noutcome {sorted(out)},  $u_x$ = {u_x}")
    handles = LABEL_LEGEND + owner_legend("xyz") + [HIDDEN_LEGEND]
    fig.legend(handles=handles, loc="lower center", ncol=7, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout(h_pad=0.8)
    save(fig, "fig_manipulation_examples")


# --------------------------------------------------------------------------- #
# Experiment figures
# --------------------------------------------------------------------------- #


def fig_strategyproof_curve():
    sp = [summary["by_p"][str(p)]["strategyproof"] for p in P]
    cond = [summary["by_p"][str(p)]["cond_path_distinct"] for p in P]
    lo, hi = zip(*(wilson(round(s * N_PER_P), N_PER_P) for s in sp))
    fig, ax = plt.subplots(figsize=(6.6, 3.7))
    ax.fill_between(P, lo, hi, color=BLUE, alpha=0.18, lw=0, label="95% confidence band")
    ax.plot(P, sp, "-o", color=BLUE, lw=2, ms=5, label="mechanism is strategyproof")
    ax.plot(P, cond, "-s", color=RED, lw=2, ms=5, label="Theorem 5.4 condition holds")
    for p, s in zip(P, sp):
        falling = p <= 0.5  # place the label on the side the curve is moving away from
        ax.annotate(f"{s:.3f}", (p, s), textcoords="offset points", xytext=(6 if falling else -6, 6),
                    ha="left" if falling else "right", fontsize=8, color=BLUE)
    ax.set(xlabel="attack probability $p$", ylabel="fraction of instances", ylim=(0, 0.84), xlim=(0.05, 0.95))
    ax.set_xticks(P)
    ax.legend(loc="upper right")
    fig.tight_layout()
    save(fig, "fig_strategyproof_curve")


def fig_conditions_by_reading():
    names = {"path_distinct": ("simple path, $\\alpha\\neq\\beta$ (headline)", RED, "-", "s"),
             "walk_distinct": ("walk, $\\alpha\\neq\\beta$", ORANGE, "--", "^"),
             "path_same": ("simple path, $\\alpha=\\beta$ allowed\n(= walk, $\\alpha=\\beta$ allowed)", BLUE, "-", "o"),
             "book_path": ("book wording (conflict-free types)", GREEN, ":", "D")}
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    for k, (lab, c, ls, m) in names.items():
        ax.plot(P, [summary["by_p"][str(p)][f"cond_{k}"] for p in P], ls=ls, marker=m, color=c, lw=2, ms=5, label=lab)
    ax.set(xlabel="attack probability $p$", ylabel="fraction satisfying the condition",
           xlim=(0.05, 0.95), ylim=(0, 0.27))
    ax.set_xticks(P)
    ax.legend()
    fig.tight_layout()
    save(fig, "fig_conditions_by_reading")


def fig_contingency():
    v = summary["variants"]["path_distinct"]
    a, b, c, d = (v["cond_holds_and_strategyproof"], v["cond_holds_but_manipulable"],
                  v["cond_fails_and_strategyproof"], v["cond_fails_and_manipulable"])
    tot = a + b + c + d
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.4), gridspec_kw={"width_ratios": [1.05, 1.0]})
    cells = [[a, b], [c, d]]
    colors = [[GREEN, RED], [SKY, "#bbbbbb"]]
    ax1.set_xlim(-0.55, 2)
    ax1.set_ylim(0, 2.35)
    ax1.axis("off")
    ax1.grid(False)
    for r in range(2):
        for k in range(2):
            ax1.add_patch(plt.Rectangle((k, 1 - r), 1, 1, fc=colors[r][k], ec="white", lw=3,
                                        alpha=0.85 if cells[r][k] else 0.25))
            ax1.text(k + 0.5, 1 - r + 0.57, f"{cells[r][k]:,}", ha="center", va="center", fontsize=15, fontweight="bold")
            ax1.text(k + 0.5, 1 - r + 0.30, f"{cells[r][k] / tot:.1%}", ha="center", va="center", fontsize=9)
    ax1.text(0.5, 2.1, "strategyproof", ha="center", fontsize=9.5, fontweight="bold")
    ax1.text(1.5, 2.1, "manipulable", ha="center", fontsize=9.5, fontweight="bold")
    ax1.text(-0.05, 1.5, "condition\nholds", ha="right", va="center", fontsize=9.5, fontweight="bold")
    ax1.text(-0.05, 0.5, "condition\nfails", ha="right", va="center", fontsize=9.5, fontweight="bold")
    ax1.set_title("27 000 instances (headline reading)", fontsize=10)
    bars = [("strategyproof\n(7,725)", a / (a + c), c / (a + c)), ("manipulable\n(19,275)", 0.0, 1.0)]
    for i, (lab, h, f) in enumerate(bars):
        ax2.barh(i, h, color=GREEN, height=0.55)
        ax2.barh(i, f, left=h, color="#cfcfcf", height=0.55)
        if h > 0.02:
            ax2.text(h / 2, i, f"holds\n{h:.1%}", ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
        ax2.text(h + f / 2, i, f"condition fails  {f:.1%}", ha="center", va="center", fontsize=9)
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels([x[0] for x in bars])
    ax2.set_xlim(0, 1)
    ax2.set_xlabel("share of the group")
    ax2.invert_yaxis()
    ax2.set_title("Sufficient, but not necessary", fontsize=10)
    ax2.grid(axis="y", alpha=0)
    fig.tight_layout()
    save(fig, "fig_contingency")


def fig_why_condition_fails():
    reasons = ["rescue_offset", "beta_hopeless", "alpha_irrelevant", "hiding_hurts_beta"]
    cols = [BLUE, ORANGE, GREEN, PURPLE]
    v = summary["variants"]["path_distinct"]
    pairs = [v["violating_pairs_by_reason"].get(r, 0) for r in reasons]
    inst = [sum(n for k, n in v["reasons_for_sp_but_cond_fails"].items() if r in k.split("+")) for r in reasons]
    only = Counter()
    for k, n in v["reasons_for_sp_but_cond_fails"].items():
        parts = k.split("+")
        only["mixture" if len(parts) > 1 else parts[0]] += n
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.7), gridspec_kw={"width_ratios": [1, 1, 0.9]})
    ticks = ["rescue\noffset", "$\\beta$\nhopeless", "$\\alpha$\nirrelevant", "hiding\nhurts $\\beta$"]
    for ax, vals, ttl in ((axes[0], inst, "instances containing the class\n(classes overlap)"),
                          (axes[1], pairs, "violating $(\\alpha,\\beta)$ pairs\n(one class per pair)")):
        ax.bar(range(4), vals, color=cols)
        for i, val in enumerate(vals):
            ax.text(i, val, f"{val:,}", ha="center", va="bottom", fontsize=8.5)
        ax.set_xticks(range(4))
        ax.set_xticklabels(ticks, fontsize=8.5)
        ax.set_title(ttl, fontsize=9.5)
        ax.set_ylim(0, max(vals) * 1.13)
    ax = axes[2]
    parts = [("only rescue offset", only["rescue_offset"], BLUE), ("only $\\beta$ hopeless", only["beta_hopeless"], ORANGE),
             ("only $\\alpha$ irrelevant", only["alpha_irrelevant"], GREEN),
             ("only hiding hurts $\\beta$", only["hiding_hurts_beta"], PURPLE),
             ("mixture of classes", only["mixture"], "#999999")]
    tot = sum(p[1] for p in parts)
    wedges, _ = ax.pie([p[1] for p in parts], colors=[p[2] for p in parts], startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.42, ec="white", lw=1.5))
    ax.set_title(f"the {tot:,} instances by class mix", fontsize=9.5)
    ax.legend(wedges, [f"{p[0]}  {p[1] / tot:.1%}" for p in parts], loc="upper center", bbox_to_anchor=(0.5, 0.02),
              fontsize=8, frameon=False)
    ax.grid(False)
    fig.tight_layout()
    save(fig, "fig_why_condition_fails")


def fig_mix_by_p():
    """For each p: composition of the strategyproof-but-condition-fails instances by class."""
    with open("results/q3_strategyproof_but_condition_fails.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    cats = ["rescue_offset", "beta_hopeless", "alpha_irrelevant", "hiding_hurts_beta", "mixture"]
    cols = [BLUE, ORANGE, GREEN, PURPLE, "#999999"]
    tab = {p: Counter() for p in P}
    for r in rows:
        ks = r["reasons"].split("+")
        tab[float(r["p"])]["mixture" if len(ks) > 1 else ks[0]] += 1
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.4, 3.5), gridspec_kw={"width_ratios": [1.5, 1]})
    bottom = [0] * len(P)
    for c, col in zip(cats, cols):
        vals = [tab[p][c] / max(1, sum(tab[p].values())) for p in P]
        ax.bar([str(p) for p in P], vals, bottom=bottom, color=col, label=c.replace("_", " "), width=0.72)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set(xlabel="attack probability $p$", ylabel="share of the instances", ylim=(0, 1))
    ax.legend(fontsize=8, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
    ax.set_title("Reason class of strategyproof instances that fail the condition", fontsize=9.5)
    counts = [sum(tab[p].values()) for p in P]
    ax2.bar([str(p) for p in P], counts, color=SKY)
    for i, n in enumerate(counts):
        ax2.text(i, n, str(n), ha="center", va="bottom", fontsize=8)
    ax2.set(xlabel="attack probability $p$", ylabel="number of instances")
    ax2.set_title(f"How many there are (total {sum(counts):,})", fontsize=9.5)
    fig.tight_layout(w_pad=7)
    save(fig, "fig_mix_by_p")


def fig_grounded_empty():
    emp = [extra["grounded_empty_by_p"][str(p)] for p in P]
    sp = [summary["by_p"][str(p)]["strategyproof"] for p in P]
    sa = [extra["self_attack_mean_by_p"][str(p)] for p in P]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.2, 3.5))
    ax.plot(P, sp, "-o", color=BLUE, lw=2, label="strategyproof fraction")
    ax.plot(P, emp, "-s", color=GREY, lw=2, label="truthful grounded extension is empty")
    ax.set(xlabel="attack probability $p$", ylabel="fraction of instances", ylim=(0, 1.05), xlim=(0.05, 0.95))
    ax.set_xticks(P)
    ax.legend(loc="center left", fontsize=8.5)
    ax.set_title("Empty grounded extensions take over for large $p$", fontsize=10)
    ax2.bar([str(p) for p in P], sa, color=ORANGE)
    for i, v in enumerate(sa):
        ax2.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    ax2.set(xlabel="attack probability $p$", ylabel="self-attacking arguments per instance")
    ax2.set_title("Mean number of self-attackers", fontsize=10)
    fig.tight_layout()
    save(fig, "fig_grounded_empty")


def fig_gain_and_size():
    h = extra["gain_histogram_by_p"]
    tot = extra["gain_subsample_per_p"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.4, 3.5), gridspec_kw={"width_ratios": [1.6, 1]})
    bottom = [0] * len(P)
    for g, col, lab in ((0, "#d9d9d9", "strategyproof (no gain)"), (1, SKY, "best manipulation gains 1"),
                        (2, ORANGE, "gains 2"), (3, RED, "gains 3")):
        vals = [h[str(p)].get(str(g), 0) / tot for p in P]
        ax.bar([str(p) for p in P], vals, bottom=bottom, color=col, label=lab, width=0.72)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set(xlabel="attack probability $p$", ylabel="share of instances", ylim=(0, 1))
    ax.legend(fontsize=8, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
    ax.set_title(f"Largest gain from hiding ({tot} instances per $p$)", fontsize=10)
    sn = extra["sp_by_n"]
    ns = sorted(sn, key=int)
    vals = [sn[n]["fraction"] for n in ns]
    ax2.bar([f"{n} args" for n in ns], vals, color=BLUE, width=0.55)
    for i, v in enumerate(vals):
        ax2.text(i, v, f"{v:.1%}", ha="center", va="bottom", fontsize=9)
    ax2.set(ylabel="strategyproof fraction (all 27 000)", ylim=(0, 0.5))
    ax2.set_title("More arguments, more room to manipulate", fontsize=10)
    fig.tight_layout(w_pad=7)
    save(fig, "fig_gain_and_size")


if __name__ == "__main__":
    fig_book_frameworks()
    fig_manipulation_examples()
    fig_strategyproof_curve()
    fig_conditions_by_reading()
    fig_contingency()
    fig_why_condition_fails()
    fig_mix_by_p()
    fig_grounded_empty()
    fig_gain_and_size()

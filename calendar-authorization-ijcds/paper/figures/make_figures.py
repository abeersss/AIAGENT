"""Figures for the IJCDS manuscript, drawn only from result files.
Usage: python paper/figures/make_figures.py [results_dir]  (default: ../../study/results)
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

RES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "study", "results")
OUT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 8,
                     "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7})
INK, GREY, BLUE = "#222222", "#8a8a8a", "#1f5fbf"
COL = {"unsafe_commit": "#b2182b", "correct_block": "#5a5a5a", "benign_abort": "#e0a030",
       "safe_commit": "#2b7bba", "scripted": "#9ecae1"}


# ------------------------------------------------------------------ Figure 1: architecture
def box(ax, x, y, w, h, t, fc="white", ec=INK, lw=0.9, fs=7.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.04",
                                fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs,
            weight="bold" if bold else "normal", color=INK)


def arr(ax, p, q, c=INK, ls="-", lw=0.9):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8, color=c, lw=lw, ls=ls,
                                 shrinkA=1, shrinkB=1))


fig, ax = plt.subplots(figsize=(7.0, 2.6))
ax.set_xlim(0, 20)
ax.set_ylim(0, 7.2)
ax.axis("off")
FS = 6.4
box(ax, 0.1, 4.5, 3.2, 1.1, "Recorded agent\ntool calls (replay)", fs=FS)
box(ax, 0.1, 2.6, 3.2, 1.1, "Trusted approval\nfixture", fs=FS)
box(ax, 0.1, 0.7, 3.2, 1.1, "Schedule controller\n(other users)", fs=FS)
ax.add_patch(FancyBboxPatch((4.3, 0.35), 9.4, 5.9, boxstyle="round,pad=0.01,rounding_size=0.08",
                            fc="#eef3fb", ec=BLUE, lw=1.1))
ax.text(9.0, 5.95, "Tool gateway (only path to calendar writes)", ha="center", fontsize=FS + 0.4,
        color=BLUE, weight="bold")
ax.add_patch(FancyBboxPatch((4.6, 0.6), 8.8, 4.95, boxstyle="round,pad=0.01,rounding_size=0.06",
                            fc="white", ec=INK, lw=0.8, ls="--"))
ax.text(9.0, 5.2, "one SQLite transaction (BEGIN IMMEDIATE)", ha="center", fontsize=FS, style="italic")
steps = ["(1) approval (user, action, event) active?",
         "(2) binding holds? none | version | fields",
         "(3) patch write: set start and end only",
         "(4) log row: seq, before/after image"]
for k, t in enumerate(steps):
    y = 3.95 - k * 1.05
    box(ax, 4.9, y, 8.2, 0.78, t, fs=FS)
    if k:
        arr(ax, (9.0, y + 1.05), (9.0, y + 0.78))
box(ax, 14.7, 3.7, 5.2, 1.6, "Event store\nevents(id, version, data)\napprovals, log", fs=FS)
box(ax, 14.7, 0.7, 5.2, 1.6, "Independent safety rule\n(reads the raw log only)", fs=FS)
arr(ax, (3.3, 5.05), (4.9, 4.35))
arr(ax, (13.1, 0.99), (14.7, 4.1))
arr(ax, (17.3, 3.7), (17.3, 2.3))
# grants / edits / revocations: separate connections, routed above the gateway
for y in (3.15, 1.25):
    ax.plot([3.3, 3.75, 3.75], [y, y, 6.75], color=GREY, lw=0.8, ls="--")
ax.plot([3.75, 17.3], [6.75, 6.75], color=GREY, lw=0.8, ls="--")
arr(ax, (17.3, 6.75), (17.3, 5.3), c=GREY, ls="--")
ax.text(10.5, 6.88, "grants, concurrent edits and revocations commit on separate connections",
        ha="center", fontsize=FS - 0.3, color=GREY)
fig.savefig(f"{OUT}/fig1_architecture.pdf", bbox_inches="tight")
fig.savefig(f"{OUT}/fig1_architecture.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ Figure 2: primary outcomes
reg = json.load(open(f"{RES}/pilot/audit/regenerated_tables.json"))
changes = [("U", "Unrelated\n(description)"), ("A", "Attendee\nadded"), ("T", "Event\nmoved"),
           ("R", "Revocation\nbefore write")]
binds = [("NB", "No binding"), ("WE", "Whole event"), ("FS", "Field scoped")]
fig, axes = plt.subplots(1, 4, figsize=(7.0, 2.0), sharey=True)
for ax, (ck, cl) in zip(axes, changes):
    for i, (bk, bl) in enumerate(binds):
        d = reg[f"{bk}:{ck}"]
        segs = [("safe_commit", d.get("first_eligible:safe_commit", 0)),
                ("benign_abort", d.get("first_eligible:benign_abort", 0)),
                ("correct_block", d.get("first_eligible:correct_block", 0)),
                ("unsafe_commit", d.get("first_eligible:unsafe_commit", 0))]
        bottom = 0
        for k, v in segs:
            if v:
                ax.bar(i, v, bottom=bottom, color=COL[k], width=0.65, edgecolor="white", lw=0.4)
                ax.text(i, bottom + v / 2, str(v), ha="center", va="center", fontsize=6.5,
                        color="white" if k != "benign_abort" else INK)
                bottom += v
    ax.set_xticks(range(3))
    ax.set_xticklabels([b[1].replace(" ", "\n") for b in binds], fontsize=6.5)
    ax.set_title(cl, fontsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
axes[0].set_ylabel("Traces (first eligible attempt)")
axes[0].set_ylim(0, 340)
handles = [plt.Rectangle((0, 0), 1, 1, color=COL[k]) for k in ("safe_commit", "benign_abort", "correct_block", "unsafe_commit")]
fig.legend(handles, ["Immediate safe commit", "Safe update initially blocked", "Correct denial", "Unsafe commit"],
           loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.08))
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(f"{OUT}/fig2_outcomes.pdf", bbox_inches="tight")
fig.savefig(f"{OUT}/fig2_outcomes.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ Figure 3: race stress test
o = json.load(open(f"{RES}/pilot/ordering_results.json"))["stress"]
fig, ax = plt.subplots(figsize=(3.45, 1.55))
rows = [("A2_committime_diffscope", "Field scoped,\natomic"), ("T1_precheck_fieldscope", "Field scoped,\nchecked before write")]
for i, (k, lab) in enumerate(rows):
    d = o[k]
    left = 0
    for key, col in (("safe_commits", COL["safe_commit"]), ("correct_blocks", COL["correct_block"]),
                     ("unsafe_commits", COL["unsafe_commit"])):
        v = d[key]
        if v:
            ax.barh(i, v, left=left, color=col, height=0.55, edgecolor="white", lw=0.4)
            ax.text(left + v / 2, i, str(v), ha="center", va="center", fontsize=6.5, color="white")
            left += v
ax.set_yticks(range(2))
ax.set_yticklabels([r[1] for r in rows], fontsize=6.8)
ax.invert_yaxis()
ax.set_xlim(0, 500)
ax.set_xlabel(f"Two-thread races (n = {o['A2_committime_diffscope']['n']} per gateway)")
ax.spines[["top", "right"]].set_visible(False)
handles = [plt.Rectangle((0, 0), 1, 1, color=COL[k]) for k in ("safe_commit", "correct_block", "unsafe_commit")]
ax.legend(handles, ["Write committed first", "Revocation first: denied", "Revocation first: committed"],
          loc="upper center", bbox_to_anchor=(0.45, -0.42), ncol=3, frameon=False, fontsize=6.2)
fig.savefig(f"{OUT}/fig3_races.pdf", bbox_inches="tight")
fig.savefig(f"{OUT}/fig3_races.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("figures written")

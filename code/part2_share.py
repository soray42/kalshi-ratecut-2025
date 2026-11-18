"""Part 2: average response to a one-standard-deviation jobs surprise across all reports, by minute.

Reads results/part2_event_study/<run>/beta.csv and surprises.csv (run code/part2_event_study.py first).
(a) change in the implied policy rate, bp (count market at -25 bp per cut); (b) share of the three-hour response
reached by each minute, b(h)/b(180), with 90% bootstrap bands over reports.

    python code/part2_share.py          # active sample -> figures/part2_share.png
    python code/part2_share.py all      # every report  -> figures/part2_share_all.png
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUE, RED, GREY = "#0F4D92", "#B64342", "#888888"
SCALE = {"decision_next": 1.0, "cuts_ye": -25.0}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "legend.frameon": False})


def main(run="active"):
    es = os.path.join(ROOT, "results", "part2_event_study")
    os.makedirs(os.path.join(ROOT, "figures"), exist_ok=True)
    beta = pd.read_csv(os.path.join(es, run, "beta.csv"))
    sd = pd.read_csv(os.path.join(es, "all", "surprises.csv")).surprise.std(ddof=0)  # s.d. over all reports
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.3))
    for comp, col, lab in [("decision_next", BLUE, "next-meeting market"), ("cuts_ye", RED, "count market (-25 bp per cut)")]:
        g = beta[beta.composite == comp].sort_values("h")
        k = SCALE[comp] * sd
        a.plot(g.h, g.b * k, color=col, lw=1.4, label=lab)
        a.fill_between(g.h, np.minimum(g.lo90 * k, g.hi90 * k), np.maximum(g.lo90 * k, g.hi90 * k), color=col, alpha=0.15, lw=0)
        b.plot(g.h, g.share, color=col, lw=1.4, label=lab.split(" (")[0])
        b.fill_between(g.h, g.share_lo90, g.share_hi90, color=col, alpha=0.12, lw=0)
    a.axhline(0, color=GREY, lw=0.5)
    a.set_title(f"(a) change in implied policy rate, bp (1 s.d. = {sd:.0f}k jobs)", fontsize=8.5, loc="left")
    a.legend(loc="lower right", fontsize=7)
    b.axhline(1, color=GREY, lw=0.5, ls=":"); b.axhline(0, color=GREY, lw=0.5)
    b.set_ylim(-0.2, 1.3)
    b.set_title("(b) share of the three-hour response", fontsize=8.5, loc="left")
    b.legend(loc="lower right", fontsize=7)
    for ax in (a, b):
        ax.set_xlim(0, 180); ax.set_xticks([0, 15, 30, 60, 90, 120, 180]); ax.set_xlabel("minutes after the release")
    fig.tight_layout(w_pad=2.0)
    name = "part2_share.png" if run == "active" else f"part2_share_{run}.png"
    fig.savefig(os.path.join(ROOT, "figures", name), dpi=200)


if __name__ == "__main__":
    main(*sys.argv[1:])

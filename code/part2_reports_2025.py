"""Part 2: each 2025 jobs report, minute by minute, for the 2025 count market and the next-meeting market.

Reads results/part2_event_study/all/{levels,surprises}.csv (run code/part2_event_study.py first).
Writes results/part2_reports_2025.csv, figures/part2_reports_2025.png (one panel per report) and
figures/part2_aug1.png (the 1 August 2025 report).
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ES = os.path.join(ROOT, "results", "part2_event_study", "all")
YEAR = "2025"
BLUE, RED, GREY = "#0F4D92", "#B64342", "#888888"
SCALE = {"decision_next": 1.0, "cuts_ye": -25.0}  # bp of policy rate; count market at -25 bp per cut
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "legend.frameon": False})


def load():
    lv = pd.read_csv(os.path.join(ES, "levels.csv"), dtype={"release_date": str})
    lv = lv[(lv.release_type == "NFP") & lv.release_date.str.startswith(YEAR)].copy()
    lv["bp"] = lv.dlevel * lv.composite.map(SCALE)
    return lv


def table(lv):
    sur = pd.read_csv(os.path.join(ES, "surprises.csv"), dtype={"release_date": str}).set_index("release_date")
    w = lv[lv.h.isin([15, 60, 180])].pivot_table(index="release_date", columns=["composite", "h"], values="bp")
    w.columns = [f"{'next_meeting' if c == 'decision_next' else 'count_market'}_{h}min_bp" for c, h in w.columns]
    market = lv[lv.composite == "decision_next"].groupby("release_date").market.first().rename("next_meeting_market")
    out = sur[["published", "kalshi_expectation_1h_before", "surprise"]].join(market, how="right").join(w)
    for c in ("next_meeting", "count_market"):
        out[f"{c}_share_15min"] = out[f"{c}_15min_bp"] / out[f"{c}_180min_bp"]
    out.round(3).to_csv(os.path.join(ROOT, "results", "part2_reports_2025.csv"))
    return out


def panel(ax, g, title):
    for comp, c, lab in [("decision_next", BLUE, "next-meeting market"), ("cuts_ye", RED, "2025 count market (x -25 bp)")]:
        s = g[(g.composite == comp) & (g.h >= -30)].sort_values("h")
        ax.plot(s.h, s.bp, color=c, lw=1.2, label=lab)
    ax.axvline(0, color=GREY, lw=0.6); ax.axhline(0, color=GREY, lw=0.5)
    ax.set_xlim(-30, 180); ax.set_xticks([0, 15, 60, 120, 180])
    ax.set_title(title, fontsize=8, loc="left")


def main():
    os.makedirs(os.path.join(ROOT, "figures"), exist_ok=True)
    lv = load()
    out = table(lv)
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    panel(ax, lv[lv.release_date == "2025-08-01"], "")
    ax.set_xlabel("minutes after the 1 August 2025 jobs report"); ax.set_ylabel("implied policy-rate change, bp")
    ax.legend(loc="lower left", fontsize=7.5)
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, "figures", "part2_aug1.png"), dpi=200); plt.close(fig)

    evs = sorted(lv.release_date.unique())
    fig, axs = plt.subplots(3, 4, figsize=(9.0, 6.0))
    for ax, ev in zip(axs.flat, evs):
        s = out.loc[ev, "surprise"]
        panel(ax, lv[lv.release_date == ev], f"{ev}  surprise {s:+.0f}k" if pd.notna(s) else f"{ev}  no surprise")
    for ax in axs.flat[len(evs):]:
        ax.axis("off")
    axs.flat[0].legend(loc="upper left", fontsize=6.5)
    fig.supxlabel("minutes after the release", fontsize=8.5)
    fig.supylabel("implied policy-rate change, bp", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, "figures", "part2_reports_2025.png"), dpi=200); plt.close(fig)
    print(out.round(2).to_string())


if __name__ == "__main__":
    main()

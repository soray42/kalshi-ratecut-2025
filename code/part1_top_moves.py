"""Part 1: the ten largest one-day moves in the implied number of 2025 cuts, and the news behind each.

A move is the change in the implied number of cuts from one US Eastern end of day to the next (2025 only).
The news for each day was collected by hand from articles published that day (NEWS below).

    python code/part1_top_moves.py   -> results/part1_top_moves.csv, figures/part1_top_moves.png
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
from part1_implied import ROOT, CUT_DAYS, daily, style, LINE, MUTED, ACCENT, FG

N_MOVES = 10

# date -> (what happened, outlet, article title, url); each article was published that day
NEWS = {
    "2025-01-10": ("December payrolls +256k against about 160k expected; unemployment 4.1%", "CNBC",
                   "U.S. payrolls grew by 256,000 in December, much more than expected; unemployment rate falls to 4.1%",
                   "https://www.cnbc.com/2025/01/10/jobs-report-december-2024.html"),
    "2025-02-12": ("January CPI +0.5% on the month, 3.0% on the year, above forecasts", "CNBC (via NBC4 Washington)",
                   "CNBC Daily Open: Hotter-than-expected inflation stokes U.S. policy concerns",
                   "https://nbcwashington.com/news/business/money-report/daily-open-hotter-than-expected-inflation-stokes-u-s-policy-concerns/3843620/"),
    "2025-03-04": ("25% tariffs on Canada and Mexico take effect, China raised to 20% "
                   "(no article found linking it to rate-cut pricing)", "AP (via GV Wire)",
                   "Wall Street's Losing Streak Deepens as Trump's Tariffs Kick In",
                   "https://gvwire.com/2025/03/04/wall-streets-losing-streak-deepens-as-trumps-tariffs-kick-in/"),
    "2025-04-03": ("Stocks plunge and Treasury yields fall after the 2 April tariff announcement", "AP (via WHYY)",
                   "Dow drops 1,600 as US stocks lead worldwide sell-off after Trump's tariffs cause a COVID-like shock",
                   "https://whyy.org/articles/dow-trump-stocks-fall-tariffs/"),
    "2025-04-09": ("Most reciprocal tariffs paused for 90 days", "CNBC",
                   "10-year Treasury yield falls from highs after auction eases concerns about demand for U.S. debt",
                   "https://www.cnbc.com/2025/04/09/us-treasury-yields-investors-weigh-new-reciprocal-tariffs-.html"),
    "2025-05-12": ("US and China agree to cut tariffs for 90 days; traders push back Fed cuts", "Reuters (via Kitco)",
                   "U.S.-China tariff delay gives Fed fresh reason to sit tight on rates",
                   "https://www.kitco.com/news/off-the-wire/2025-05-12/us-china-tariff-delay-gives-fed-fresh-reason-sit-tight-rates"),
    "2025-06-11": ("May CPI +0.1% on the month, softer than expected", "Reuters (via Kitco)",
                   "Stocks up, Treasury yields down on cooler inflation, US-China deal",
                   "https://www.kitco.com/news/off-the-wire/2025-06-11/stocks-treasury-yields-down-cooler-inflation-us-china-deal"),
    "2025-06-18": ("Fed holds; projections keep two 2025 cuts but seven officials now see none "
                   "(CNBC: futures pricing unchanged after the meeting)", "CNBC",
                   "Fed holds key rate steady, still sees two more cuts this year",
                   "https://www.cnbc.com/2025/06/18/fed-rate-decision-june-2025-.html"),
    "2025-08-01": ("July payrolls +73k; May and June revised down by 258k combined", "CNBC",
                   "U.S. added just 73,000 jobs in July and numbers for prior months were revised much lower",
                   "https://www.cnbc.com/2025/08/01/jobs-report-july-2025.html"),
    "2025-11-21": ("New York Fed President Williams sees room for a near-term cut", "CNBC",
                   "Treasury yields slide after Williams suggests Fed could cut again in December",
                   "https://www.cnbc.com/2025/11/21/us-treasury-yields-edge-lower-as-fed-rate-cut-bets-fall.html"),
}


def main():
    d = daily().loc["2025-01-01":"2025-12-31"]
    rel = pd.read_csv(os.path.join(ROOT, "data", "minute", "releases.csv"))
    ch = d.implied_cuts.diff()
    top = sorted(ch.abs().sort_values(ascending=False).head(N_MOVES).index)
    pk = [f"p{k}" for k in range(15)]
    rows = []
    for i, day in enumerate(top, 1):
        prev = d.index[d.index.get_loc(day) - 1]
        dp = (d.loc[day, pk] - d.loc[prev, pk]) * 100
        k = dp.abs().idxmax()
        key = f"{day:%Y-%m-%d}"
        event, outlet, title, url = NEWS.get(key, ("", "", "", ""))
        rows.append({"n": i, "date_et": key, "weekday": f"{day:%a}",
                     "implied_cuts_before": round(d.loc[prev, "implied_cuts"], 2),
                     "implied_cuts_after": round(d.loc[day, "implied_cuts"], 2), "change": round(ch[day], 2),
                     "largest_contract_move": f"exactly {k[1:]}: {d.loc[prev, k] * 100:.0f}% -> {d.loc[day, k] * 100:.0f}%",
                     "volume": int(d.loc[day, "volume"]), "trades": int(d.loc[day, "trades"]),
                     "scheduled_release": "+".join(rel[rel.date == key].type) or "none",
                     "what_happened": event, "outlet": outlet, "title": title, "url": url})
    out = pd.DataFrame(rows)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    out.to_csv(os.path.join(ROOT, "results", "part1_top_moves.csv"), index=False)

    style()
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    ax.plot(d.index, d.implied_cuts, color=LINE, lw=1.1)
    ax.axhline(3, color=MUTED, lw=0.7, ls="--")
    for t in CUT_DAYS:
        ax.axvline(pd.Timestamp(t), color=MUTED, lw=0.6, alpha=0.6)
    for r in rows:
        day = pd.Timestamp(r["date_et"])
        y = d.loc[day, "implied_cuts"]
        ax.plot(day, y, "o", color=ACCENT, ms=4.5, zorder=3)
        ax.annotate(str(r["n"]), (day, y), xytext=(4, 5 if r["change"] > 0 else -11), textcoords="offset points",
                    fontsize=7.5, color=ACCENT, fontweight="bold")
    ax.set_ylabel("expected cuts")
    ax.set_xlim(pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-31"))
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b"))
    ax.set_title("Implied E[N] over 2025  ·  ten largest one-day moves, numbered in date order", fontsize=8,
                 loc="left", color=FG)
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "figures", "part1_top_moves.png"), dpi=220)
    print(out.drop(columns=["title", "url"]).to_string(index=False))


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "figures"), exist_ok=True)
    main()

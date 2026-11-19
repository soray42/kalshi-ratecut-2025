"""Part 1: liquidity of the count market in 2025 (open interest, spreads, where the trading was).

Monthly: volume and trades (trade tape), open interest at month end (sum over contracts), median daily bid-ask spread
of the 1-4 cut contracts. By contract: share of lifetime volume, and share of 2025 hourly quotes with a bid of
2 cents or more (a contract bid at 1 cent or not at all has no real buyer).

    python code/part1_liquidity.py   -> results/part1_liquidity.csv, results/part1_liquidity_by_contract.csv,
                                        figures/part1_liquidity.png
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
from part1_implied import (ROOT, TZ, MIN_BID, daily, quotes, trades, style, BAR, BAR_HI, ACCENT, FG, MUTED)

CUT_MONTHS = ["2025-09", "2025-10", "2025-12"]


def main():
    d = daily().loc["2025-01-01":"2025-12-31"]
    m = d.groupby(d.index.strftime("%Y-%m")).agg(
        volume=("volume", "sum"), trades=("trades", "sum"), open_interest_end=("open_interest", "last"),
        median_spread_main_cents=("spread_main_cents", "median"))
    m.index.name = "month"
    res = os.path.join(ROOT, "results")
    m.round(2).to_csv(os.path.join(res, "part1_liquidity.csv"))

    tr = trades()
    q = quotes()
    q = q[q.t.dt.tz_convert(TZ).dt.year == 2025]
    k = pd.DataFrame({"volume": tr.groupby("k").count_fp.sum()})
    k["volume_share"] = k.volume / k.volume.sum()
    k["share_quotes_bid_2c_plus"] = q.assign(real=q.yes_bid_close >= MIN_BID).groupby("k").real.mean()
    k.index = [f"exactly {i}" if i < 14 else "14 or more" for i in k.index]
    k.index.name = "contract"
    k.round(3).to_csv(os.path.join(res, "part1_liquidity_by_contract.csv"))

    style()
    fig = plt.figure(figsize=(7.2, 4.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.65, wspace=0.18)
    a = fig.add_subplot(gs[0, :])
    cols = [BAR_HI if i in CUT_MONTHS else BAR for i in m.index]
    a.bar(range(12), m.open_interest_end / 1e6, color=cols, width=0.7)
    a.set_xticks(range(12), [pd.Timestamp(i).strftime("%b") for i in m.index])
    a.set_ylabel("m contracts")
    a.grid(axis="x", visible=False)
    a.set_title("Open interest at month end  ·  FOMC cut months highlighted", fontsize=8, loc="left", color=FG)
    labels = [str(i) for i in range(14)] + ["14+"]
    for ax, col, title in [(fig.add_subplot(gs[1, 0]), "volume_share", "Share of lifetime volume, by contract"),
                           (fig.add_subplot(gs[1, 1]), "share_quotes_bid_2c_plus",
                            "Share of 2025 hourly quotes with a bid of 2¢ or more")]:
        ax.bar(range(15), k[col] * 100, color=[BAR_HI if i == 3 else BAR for i in range(15)], width=0.7)
        ax.set_xticks(range(15), labels, fontsize=5.8)
        ax.grid(axis="x", visible=False)
        ax.set_xlabel("exact cuts k", color=MUTED)
        ax.set_ylabel("%")
        ax.set_title(title, fontsize=8, loc="left", color=FG)
    fig.savefig(os.path.join(ROOT, "figures", "part1_liquidity.png"), dpi=220, bbox_inches="tight")

    print(m.round(2).to_string())
    print(k.round(3).to_string())
    print(f"peak open interest {d.open_interest.max():,.0f} on {d.open_interest.idxmax():%Y-%m-%d}; "
          f"median daily spread of the 1-4 cut contracts {d.spread_main_cents.median():.1f} cents; "
          f"volume share of 0-4 cuts {k.volume_share.iloc[:5].sum():.1%}")


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "figures"), exist_ok=True)
    main()

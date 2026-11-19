"""Part 1: implied distribution over the number of 2025 cuts, by hour and by US Eastern day.

Mid quote of each contract; a bid of 1 cent or less (or no bid) counts as zero; each contract keeps its last quote
until a new one is posted; hours where any 1-4 cut contract is quoted wider than 5 cents are dropped; the fifteen
values are rescaled to sum to one; "14 or more" counts as 14. A day's value is its last hour (US Eastern).

    python code/part1_implied.py   -> data/derived/cutcount25_hourly.csv, data/derived/cutcount25_daily.csv

The other part1 scripts import hourly(), daily() and the figure style from here.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
EVENT = "KXRATECUTCOUNT-25DEC31"
TZ = "America/New_York"
MIN_BID = 0.02
MAX_SPREAD = 0.05
CUT_DAYS = ["2025-09-17", "2025-10-29", "2025-12-10"]

# dark style, to match the check-in template
BG, FG, MUTED, GRID = "#0c0c0c", "#d8d2c6", "#8a857c", "#262421"
LINE, BAR, BAR_HI, ACCENT = "#ece6da", "#3b3631", "#b9b1a3", "#d4a35a"


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8, "figure.facecolor": BG, "axes.facecolor": BG,
        "savefig.facecolor": BG, "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED,
        "ytick.color": MUTED, "text.color": FG, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True, "legend.frameon": False})


def count_of(ticker):
    return min(int(ticker.rsplit("-T", 1)[1]), 14)  # T15 is "14 or more"


def quotes():
    h = pd.read_csv(os.path.join(RAW, "hourly.csv"))
    h = h[h.event_ticker == EVENT].copy()
    h["t"] = pd.to_datetime(h.end_ts, unit="s", utc=True)
    h["k"] = h.ticker.map(count_of)
    h["mid"] = np.where(h.yes_bid_close >= MIN_BID, (h.yes_bid_close + h.yes_ask_close) / 2, 0.0)
    h["spread"] = h.yes_ask_close - h.yes_bid_close
    return h


def hourly(h=None):
    """Probabilities p0..p14 and implied_cuts at the end of each hour (UTC index)."""
    h = quotes() if h is None else h
    P = h.pivot_table(index="t", columns="k", values="mid").resample("1h").last().ffill()
    S = h.pivot_table(index="t", columns="k", values="spread").resample("1h").last().ffill()
    P = P[S[[1, 2, 3, 4]].max(axis=1) <= MAX_SPREAD]
    P = P.div(P.sum(axis=1), axis=0)
    P.columns = [f"p{k}" for k in P.columns]
    P["implied_cuts"] = sum(P[f"p{k}"] * k for k in range(15))
    return P, S


def daily():
    """End-of-day values on the US Eastern calendar, with spread, open interest, volume and trades."""
    h = quotes()
    P, S = hourly(h)
    loc = P.tz_convert(TZ)
    d = loc.groupby(loc.index.date).last()
    d.index = pd.to_datetime(d.index)
    main = S[[1, 2, 3, 4]].mean(axis=1).tz_convert(TZ)
    d["spread_main_cents"] = main.groupby(main.index.date).median().reindex(d.index.date).values * 100
    oi = h.pivot_table(index="t", columns="k", values="open_interest").ffill().sum(axis=1).tz_convert(TZ)
    d["open_interest"] = oi.groupby(oi.index.date).last().reindex(d.index.date).values
    tr = trades()
    g = tr.groupby(tr.t.dt.tz_convert(TZ).dt.date)
    d["volume"] = g.count_fp.sum().reindex(d.index.date).fillna(0).values
    d["trades"] = g.size().reindex(d.index.date).fillna(0).astype(int).values
    d.index.name = "date_et"
    return d


def trades():
    tr = pd.read_csv(os.path.join(RAW, "trades_cutcount25.csv"))
    tr["t"] = pd.to_datetime(tr.created_time, utc=True, format="ISO8601")
    tr["k"] = tr.ticker.map(count_of)
    return tr


def main():
    out = os.path.join(ROOT, "data", "derived")
    os.makedirs(out, exist_ok=True)
    P, _ = hourly()
    P.index.name = "hour_end_utc"
    P.to_csv(os.path.join(out, "cutcount25_hourly.csv"), float_format="%.5f")
    daily().to_csv(os.path.join(out, "cutcount25_daily.csv"), float_format="%.5f")


if __name__ == "__main__":
    main()

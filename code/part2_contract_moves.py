"""Part 2: contract-level moves around each release, and at the same clock time one day earlier and later.

For every contract that settles more than 20 days after the release (count markets, Fed-meeting markets):
A = mean of the last 5 mids in the 30 minutes before, B = mean mid 120-180 minutes after, R = B - A (cents);
tau90 = first minute at which the mid is 90% of the way from A to B and stays there for the next 3 observations
(computed when |R| >= 1 cent). shift = 0 at the release, -1440 / 1440 for the day before / after (no release).

    python code/part2_contract_moves.py    -> results/part2_contract_moves.csv, summary printed
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN = os.path.join(ROOT, "data", "minute")
HORIZON_DAYS = 20
SERIES = ("KXRATECUTCOUNT", "KXFEDDECISION")


def one(path, t0):
    d = pd.read_csv(path)
    d = d[d.bid.notna() & d.ask.notna()]
    if len(d) < 30:
        return None
    rel = (d.ts.to_numpy() - t0) / 60.0
    mid = ((d.bid + d.ask) / 2).to_numpy()
    spread = (d.ask - d.bid).to_numpy()
    pre, post, term = (rel >= -30) & (rel < 0), (rel >= 0) & (rel <= 180), rel >= 120
    if pre.sum() < 3 or post.sum() < 10 or (post & term).sum() < 2:
        return None
    A, B = mid[pre][-5:].mean(), mid[post & term].mean()
    R = B - A
    tau = np.nan
    if abs(R) >= 1.0:
        v, r = mid[post], rel[post]
        for i in range(len(v)):
            if abs(v[i] - A) >= 0.9 * abs(R):
                nxt = v[i + 1:i + 4]
                if len(nxt) < 3 or all(abs(x - A) >= 0.9 * abs(R) for x in nxt):
                    tau = r[i]
                    break
    return {"R": R, "tau90": tau, "half_spread": float(np.median(spread[post])) / 2}


def main():
    c = pd.read_csv(os.path.join(MIN, "contracts.csv"))
    c = c[c.series.isin(SERIES) & (c.role == "forward")]
    c["t0"] = pd.to_datetime(c.release_utc, utc=True)
    c = c[pd.to_datetime(c.close_time, utc=True, format="ISO8601") > c.t0 + pd.Timedelta(days=HORIZON_DAYS)]
    rows = []
    for r in c.itertuples():
        path = os.path.join(MIN, "candles", f"{r.release_date}__{r.ticker}.csv")
        if not os.path.exists(path):
            continue
        for shift in (0, -1440, 1440):
            x = one(path, int(r.t0.timestamp()) + shift * 60)
            if x:
                rows.append({"release_date": r.release_date, "release_type": r.release_type, "series": r.series,
                             "ticker": r.ticker, "shift": shift, **x})
    d = pd.DataFrame(rows)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    d.to_csv(os.path.join(ROOT, "results", "part2_contract_moves.csv"), index=False)
    for thr in (1, 5):
        s = d[d.R.abs() >= thr].groupby(["shift"]).agg(moves=("tau90", "size"), releases=("release_date", "nunique"),
                                                         tau90_median=("tau90", "median"))
        print(f"|R| >= {thr} cents\n{s.round(1).to_string()}\n")


if __name__ == "__main__":
    main()

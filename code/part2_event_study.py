"""Part 2 event study: minute-by-minute response of the count market and the next-meeting market to jobs reports.

For each release in data/minute/releases.csv:
  - each contract's one-minute mid quote goes on a grid of minutes -60..180 around the release; a quote stands
    until the next candle, for at most LOOKBACK minutes;
  - each market becomes an implied distribution and its mean: threshold ladders are made non-increasing (isotonic
    fit) and differenced into bins; bucket contracts are rescaled to sum to one;
  - decision_next is the Fed-meeting market that settles first after the release (expected change, bp);
    cuts_ye is the count market for the current year (implied number of cuts).
For each jobs report, the surprise is the published payrolls number minus the implied mean of Kalshi's payrolls
market one hour before the release (in thousands). Across reports, the change at minute h is regressed on the
surprise; bands come from resampling reports (bootstrap).

    python code/part2_event_study.py                                 -> results/part2_event_study/all/
    python code/part2_event_study.py --min-obs 0.5                   -> .../active/
    python code/part2_event_study.py --lookback 60                   -> .../lookback60/
    python code/part2_event_study.py --placebo -1440 --lookback 60   -> .../placebo_day_before/
    python code/part2_event_study.py --placebo 1440 --lookback 60    -> .../placebo_day_after/

Outputs per run: levels.csv (implied values by minute), surprises.csv, beta.csv (all minutes), table.csv
(selected minutes, leave-one-report-out ranges), paired.csv (the two markets on the same reports).
"""
import argparse, os, re, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)  # all-NaN means on thin ladders

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN = os.path.join(ROOT, "data", "minute")
PRE, T2 = 60, 180
MAX_SPREAD = 20.0   # a contract is used only if its median pre-release spread is at most this (cents)
H_TABLE = [1, 2, 5, 10, 15, 30, 60, 90, 120, 180]
BUCKET = {"C26": -50.0, "C25": -25.0, "H0": 0.0, "H25": 25.0, "H26": 50.0}  # Fed-meeting outcomes, bp
COMPOSITES = {"decision_next": "KXFEDDECISION", "cuts_ye": "KXRATECUTCOUNT"}
PAYROLLS = "KXPAYROLLS"
REPS, SEED = 2000, 0
GRID = np.arange(-PRE, T2 + 1)


# ---------------------------------------------------------------- contracts and quotes
def strike_of(r):
    """(market, kind, strike) of one contract; kind is greater | bucket | None."""
    if r.series == "KXFEDDECISION":
        suf = r.ticker.split("-")[-1]
        return r.event_ticker, ("bucket" if suf in BUCKET else None), BUCKET.get(suf)
    st, fl, cp = r.strike_type, r.floor_strike, r.cap_strike
    if st == "":  # a few records lack strike terms: read the threshold from the ticker (e.g. -T150000)
        m = re.fullmatch(r"T?(-?\d+(?:\.\d+)?)", r.ticker.split("-")[-1])
        return r.event_ticker, ("greater" if m else None), (float(m.group(1)) if m else None)
    if st in ("greater", "greater_or_equal") and fl != "":
        return r.event_ticker, "greater", float(fl)
    if st == "between" and fl != "" and cp != "":
        return r.event_ticker, "bucket", (float(fl) + float(cp)) / 2
    return r.event_ticker, None, None


def load_quotes(date, ticker, t0, lookback):
    """Mid and spread (cents) on GRID; obs_mid is the mid only in minutes with a candle."""
    path = os.path.join(MIN, "candles", f"{date}__{ticker}.csv")
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path)
    d = d[d.bid.notna() & d.ask.notna()]
    if d.empty:
        return None
    rel = (d.ts.to_numpy() - t0) // 60
    keep = (rel >= -PRE - lookback) & (rel <= T2)
    if not keep.any():
        return None
    d, rel = d[keep], rel[keep]
    q = pd.DataFrame({"mid": ((d.bid + d.ask) / 2).to_numpy(), "spread": (d.ask - d.bid).to_numpy()}, index=rel)
    q = q[~q.index.duplicated(keep="last")].sort_index().reindex(np.arange(-PRE - lookback, T2 + 1))
    q["obs_mid"] = q.mid
    q[["mid", "spread"]] = q[["mid", "spread"]].ffill()
    return q.loc[GRID]


def pava_dec(y):
    """Least-squares non-increasing fit."""
    blocks = []
    for v in y[::-1]:
        blocks.append([v])
        while len(blocks) > 1 and np.mean(blocks[-2]) > np.mean(blocks[-1]):
            last = blocks.pop()
            blocks[-1] = blocks[-1] + last
    return np.concatenate([[np.mean(b)] * len(b) for b in blocks])[::-1]


def implied_mean(kind, strikes, mids):
    """Implied mean per minute from contract mids (minutes x contracts, cents)."""
    P = mids / 100.0
    if kind == "bucket":
        p = np.clip(P, 0, 1)
        p = p / p.sum(axis=1, keepdims=True)
        return p @ np.asarray(strikes)
    k = np.asarray(strikes)
    S = np.vstack([pava_dec(np.clip(r, 0, 1)) if np.isfinite(r).all() else np.full(len(k), np.nan) for r in P])
    step = np.median(np.diff(k))
    x = np.concatenate([[k[0] - step / 2], (k[:-1] + k[1:]) / 2, [k[-1] + step / 2]])
    p = np.column_stack([1 - S[:, 0], S[:, :-1] - S[:, 1:], S[:, -1]])
    return p @ x


def markets_of(g):
    """Group one release's contracts by market: {(market, kind): [(strike, ticker, row), ...]}."""
    out = {}
    for r in g.itertuples(index=False):
        m, kind, k = strike_of(r)
        if kind is not None:
            out.setdefault((m, kind), []).append((k, r.ticker, r))
    return {key: sorted(v, key=lambda x: x[0]) for key, v in out.items()}


# ---------------------------------------------------------------- jobs surprise
def payrolls_surprise(date, g, t0):
    """Published payrolls minus the implied mean one hour before (thousands), from the market settling on this release."""
    g = g[(g.series == PAYROLLS) & (g.role == "settles")]
    pre_w, pre60 = (GRID >= -5) & (GRID <= 0), (GRID >= -65) & (GRID <= -55)
    for (market, kind), items in markets_of(g).items():
        Q = {tk: load_quotes(date, tk, t0, 1440) for _, tk, _ in items}
        keep = [(k, tk, r) for k, tk, r in items if Q[tk] is not None and Q[tk].mid[pre_w].notna().any()
                and Q[tk].spread[GRID <= 0].median() <= MAX_SPREAD]
        keep = [x for x in keep if np.isfinite(Q[x[1]].mid[pre60]).all()] or keep  # strikes quoted an hour before
        if not keep or (kind == "bucket" and len(keep) < 2):
            continue
        M = np.column_stack([Q[tk].mid.to_numpy() for _, tk, _ in keep])
        E = np.nanmean(implied_mean(kind, [k for k, _, _ in keep], M)[pre60])
        published = next((float(r.expiration_value.replace(",", "")) for _, _, r in keep if r.expiration_value), np.nan)
        return {"release_date": date, "market": market, "kalshi_expectation_1h_before": E / 1e3,
                "published": published / 1e3, "surprise": (published - E) / 1e3}
    return None


# ---------------------------------------------------------------- implied values by minute
def market_levels(date, items, kind, t0, lookback, min_obs, node_spread):
    pre_w = (GRID >= -5) & (GRID <= 0)
    Q = {tk: load_quotes(date, tk, t0, lookback) for _, tk, _ in items}
    keep = [(k, tk) for k, tk, _ in items if Q[tk] is not None and Q[tk].mid[pre_w].notna().all()
            and Q[tk].spread[GRID <= 0].median() <= MAX_SPREAD and Q[tk].mid.notna().mean() >= 0.9]
    if len(keep) < 2:
        return None
    M = np.column_stack([Q[tk].mid.to_numpy() for _, tk in keep])
    # a candle exists only in minutes in which the quote changed or a trade happened
    obs = np.column_stack([Q[tk].obs_mid.notna().to_numpy() for _, tk in keep])[(GRID >= 1) & (GRID <= 60)]
    diag = {"obs_any_60": obs.any(axis=1).mean(), "obs_mean_60": obs.mean(),
            "spread_pre": float(np.median([Q[tk].spread[GRID <= 0].median() for _, tk in keep])), "n_strikes": len(keep)}
    if diag["spread_pre"] > node_spread or diag["obs_any_60"] < min_obs:
        return None
    return implied_mean(kind, [k for k, _ in keep], M), diag


def release_levels(rel, g, shift, lookback, min_obs, node_spread):
    t0p = pd.Timestamp(rel.release_utc) + pd.Timedelta(minutes=shift)
    t0 = int(t0p.timestamp())
    rows = []
    for name, series in COMPOSITES.items():
        fwd = g[(g.role == "forward") & (g.series == series)]
        cands = []
        for (market, kind), items in markets_of(fwd).items():
            hz = (pd.to_datetime([r.close_time for _, _, r in items], utc=True, format="ISO8601").max() - t0p)
            cands.append((hz.total_seconds() / 86400, -len(items), market, kind, items))
        for hz, _, market, kind, items in sorted(cands, key=lambda c: (abs(c[0]), c[1]))[:3]:  # nearest usable
            lv = market_levels(rel.date, items, kind, t0, lookback, min_obs, node_spread)
            if lv is None:
                continue
            y, diag = lv
            rows.append(pd.DataFrame({"release_date": rel.date, "release_type": rel.type, "composite": name,
                                      "market": market, "horizon_days": hz, "h": GRID, "level": y,
                                      "dlevel": y - y[(GRID >= -5) & (GRID <= 0)].mean(), **diag}))
            break
    return rows


# ---------------------------------------------------------------- regressions
def ols_b(s, Y):
    s = s - s.mean()
    return (s @ (Y - Y.mean(axis=0))) / (s @ s)


def lp(levels, sur):
    """Slope of the change at each minute on the surprise, bootstrap bands, shares b(h)/b(180), leave-one-out ranges."""
    rng = np.random.default_rng(SEED)
    beta, table = [], []
    for comp, g in levels.groupby("composite"):
        Y = g.pivot_table(index="release_date", columns="h", values="dlevel").sort_index()
        Y = Y.loc[:, Y.columns >= 0]
        s = sur.reindex(Y.index)
        ok = s.notna() & Y.notna().all(axis=1)
        events, Y, s = Y.index[ok].to_numpy(), Y[ok].to_numpy(), s[ok].to_numpy()
        n = len(s)
        if n < 8:
            continue
        hs = np.array(sorted(h for h in g.h.unique() if h >= 0))
        b = ols_b(s, Y)
        B = np.array([ols_b(s[i], Y[i]) if np.std(s[i]) > 0 else np.full(len(hs), np.nan)
                      for i in (rng.integers(0, n, n) for _ in range(REPS))])
        lo, hi = np.nanpercentile(B, [5, 95], axis=0)
        jT = len(hs) - 1
        sig = (lo[jT] > 0) or (hi[jT] < 0)
        sh_lo, sh_hi = np.nanpercentile(B / B[:, [jT]], [5, 95], axis=0)
        L = np.array([ols_b(np.delete(s, i), np.delete(Y, i, axis=0)) for i in range(n)])
        Ls = L / L[:, [jT]]
        infl = events[int(np.argmax(np.abs(L[:, jT] - b[jT])))]
        for j, h in enumerate(hs):
            r = {"composite": comp, "h": int(h), "n": n, "b": b[j], "lo90": lo[j], "hi90": hi[j],
                 "sd_surprise": np.std(s), "share": b[j] / b[jT] if sig else np.nan,
                 "share_lo90": sh_lo[j] if sig else np.nan, "share_hi90": sh_hi[j] if sig else np.nan}
            beta.append(r)
            if h in H_TABLE:
                table.append({**r, "b_sd": b[j] * np.std(s), "b_loo_min": L[:, j].min(), "b_loo_max": L[:, j].max(),
                              "b180_excludes_0": sig,
                              "share_loo_min": Ls[:, j].min() if sig else np.nan,
                              "share_loo_max": Ls[:, j].max() if sig else np.nan, "most_influential": infl})
    return pd.DataFrame(beta), pd.DataFrame(table)


def paired(levels, sur, seed=1):
    """Both markets on the reports they share, same bootstrap draws: responses to a one-s.d. surprise in bp
    (count market at -25 bp per cut), their difference, and the difference of the shares b(h)/b(180)."""
    Ys = []
    for comp, k in (("decision_next", 1.0), ("cuts_ye", -25.0)):
        Y = levels[levels.composite == comp].pivot_table(index="release_date", columns="h", values="dlevel")
        Ys.append(Y.loc[:, Y.columns >= 0] * k)
    s = sur.reindex(Ys[0].index.intersection(Ys[1].index))
    ev = s.index[s.notna() & Ys[0].reindex(s.index).notna().all(axis=1) & Ys[1].reindex(s.index).notna().all(axis=1)]
    if len(ev) < 8:
        return pd.DataFrame()
    s, A, B = s[ev].to_numpy(), Ys[0].loc[ev].to_numpy(), Ys[1].loc[ev].to_numpy()
    hs, n, sd = Ys[0].columns.to_numpy(), len(ev), np.std(s)

    def stats(i):
        ba, bb = ols_b(s[i], A[i]) * sd, ols_b(s[i], B[i]) * sd
        return np.vstack([ba, bb, bb - ba, bb / bb[-1] - ba / ba[-1]])

    pt = stats(np.arange(n))
    rng = np.random.default_rng(seed)
    D = np.array([stats(rng.integers(0, n, n)) for _ in range(REPS)])
    lo, hi = np.nanpercentile(D, [5, 95], axis=0)
    names = ["decision_next_bp", "cuts_ye_bp", "level_diff_bp", "share_diff"]
    return pd.DataFrame([{"n": n, "h": int(h), "measure": m, "est": pt[k, j], "lo90": lo[k, j], "hi90": hi[k, j]}
                         for j, h in enumerate(hs) if h in H_TABLE or h in (3, 7) for k, m in enumerate(names)])


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--placebo", type=int, default=0, metavar="MIN",
                    help="move every window by MIN minutes (-1440: same clock time the day before); surprises stay")
    ap.add_argument("--lookback", type=int, default=1440, metavar="MIN",
                    help="minutes a quote may be carried forward onto the grid; use 60 with --placebo")
    ap.add_argument("--min-obs", type=float, default=0.0, metavar="SHARE",
                    help="keep a market only if some contract had a candle in at least this share of minutes 1-60")
    ap.add_argument("--node-spread", type=float, default=20.0, metavar="CENTS",
                    help="keep a market only if the median pre-release spread of its contracts is at most this")
    a = ap.parse_args()
    name = {(-1440, 60): "placebo_day_before", (1440, 60): "placebo_day_after", (0, 60): "lookback60"}.get(
        (a.placebo, a.lookback), "all" if not a.placebo and a.lookback == 1440 else f"placebo{a.placebo}_lb{a.lookback}")
    if a.min_obs:
        name = "active" if name == "all" else f"{name}_active"
    if a.node_spread != 20.0:
        name += f"_spread{a.node_spread:g}"
    out = os.path.join(ROOT, "results", "part2_event_study", name)
    os.makedirs(out, exist_ok=True)

    rel = pd.read_csv(os.path.join(MIN, "releases.csv")).assign(date=lambda r: r.date.astype(str)).set_index("date")
    con = pd.read_csv(os.path.join(MIN, "contracts.csv"), dtype=str, keep_default_na=False)
    rows, sur = [], []
    for date, g in con.groupby("release_date"):
        r = rel.loc[date]
        r = pd.Series({"date": date, "type": r.type, "release_utc": r.release_utc})
        rows += release_levels(r, g, a.placebo, a.lookback, a.min_obs, a.node_spread)
        if r.type == "NFP":
            x = payrolls_surprise(date, g, int(pd.Timestamp(r.release_utc).timestamp()))
            if x:
                sur.append(x)
    levels = pd.concat(rows, ignore_index=True)
    sur = pd.DataFrame(sur)
    levels.to_csv(os.path.join(out, "levels.csv"), index=False)
    sur.to_csv(os.path.join(out, "surprises.csv"), index=False)
    s = sur.set_index("release_date").surprise
    nfp = levels[levels.release_type == "NFP"]
    beta, table = lp(nfp, s)
    beta.to_csv(os.path.join(out, "beta.csv"), index=False)
    table.to_csv(os.path.join(out, "table.csv"), index=False)
    paired(nfp, s).to_csv(os.path.join(out, "paired.csv"), index=False)
    pd.set_option("display.width", 200)
    print(out)
    print(table[table.h.isin([5, 15, 30, 60, 180])][["composite", "h", "n", "b", "lo90", "hi90", "share"]]
          .round(4).to_string(index=False))


if __name__ == "__main__":
    main()

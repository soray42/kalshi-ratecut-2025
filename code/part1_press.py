"""Part 1: what the press reported at the time, against Kalshi's price for the same question.

Reads results/press_claims.csv (quotes collected by hand). For each quote that states a market probability,
CLAIMS below says which Kalshi market answers the same question and when to read it (US Eastern): at 4 pm on the
day of the article, or 10 am for the one article that gives "Friday morning"; "before" is the same clock time a day
earlier, for articles that compare with the day before. Count-market probabilities use the rule in
part1_implied.py; Fed-meeting markets use the same 1-cent rule, rescaled over their five buckets.
On 10 January, "a single cut" means one cut in 2025 (CNBC: "the expectation of just one cut this year"), compared
here with Kalshi's "exactly 1".

    python code/part1_press.py   -> results/part1_press.csv
"""
import os
import numpy as np
import pandas as pd
from part1_implied import ROOT, RAW, TZ, MIN_BID, hourly

# (date, outlet) -> (Kalshi market, measure, time "at" (ET), time "before" (ET) or None, what the press figure measures)
CLAIMS = {
    ("2025-01-10", "CNBC"): ("count", "p1|ge1", "2025-01-10 16:00", "2025-01-09 16:00", "probability of a single cut this year"),
    ("2025-04-03", "CNBC"): ("count", "mean", "2025-04-03 16:00", "2025-04-02 16:00", "number of cuts priced"),
    ("2025-04-04", "CNBC"): ("count", "p5|ge5", "2025-04-04 10:00", "2025-04-03 10:00", "probability of five cuts"),
    ("2025-08-01", "CNBC"): ("KXFEDDECISION-25SEP", "cut", "2025-08-01 16:00", "2025-07-31 16:00",
                             "probability of a September cut"),
    ("2025-09-05", "CNBC"): ("KXFEDDECISION-25SEP", "cut50", "2025-09-05 16:00", "2025-09-04 16:00",
                             "probability of a 50 bp September cut"),
    ("2025-11-20", "CNBC"): ("KXFEDDECISION-25DEC", "cut", "2025-11-20 16:00", None, "probability of a December cut"),
    ("2025-11-21", "Axios"): ("KXFEDDECISION-25DEC", "cut", "2025-11-21 16:00", "2025-11-20 16:00",
                              "probability of a December cut"),
    ("2025-11-21", "Reuters (via Kitco)"): ("KXFEDDECISION-25DEC", "cut", "2025-11-21 16:00", None,
                                            "probability of a December cut"),
    ("2025-12-08", "CoinDesk"): ("KXFEDDECISION-25DEC", "cut", "2025-12-08 16:00", None,
                                 "probability of a December cut"),
}


def meeting_probs(event):
    h = pd.read_csv(os.path.join(RAW, "hourly.csv"))
    h = h[h.event_ticker == event].copy()
    h["t"] = pd.to_datetime(h.end_ts, unit="s", utc=True)
    h["b"] = h.ticker.str.rsplit("-", n=1).str[1]
    h["mid"] = np.where(h.yes_bid_close >= MIN_BID, (h.yes_bid_close + h.yes_ask_close) / 2, 0.0)
    P = h.pivot_table(index="t", columns="b", values="mid").resample("1h").last().ffill().fillna(0)
    P = P.div(P.sum(axis=1), axis=0)
    return pd.DataFrame({"cut": P.C25 + P.C26, "cut50": P.C26}, index=P.index)


def value_at(P, measure, when):
    """measure: mean (implied cuts), pK (exactly K), geK (K or more), cut / cut50 (meeting markets);
    "a|b" gives both, separated by " / "."""
    t = pd.Timestamp(when, tz=TZ).tz_convert("UTC")
    row = P[P.index <= t].iloc[-1]
    out = []
    for m in measure.split("|"):
        if m == "mean":
            out.append(f"{row['implied_cuts']:.2f}")
        elif m.startswith("ge"):
            out.append(f"{sum(row[f'p{k}'] for k in range(int(m[2:]), 15)) * 100:.0f}%")
        else:
            out.append(f"{row[m] * 100:.0f}%")
    return " / ".join(out)


def main():
    claims = pd.read_csv(os.path.join(ROOT, "results", "press_claims.csv"))
    count, _ = hourly()
    rows = []
    for c in claims.itertuples():
        spec = CLAIMS.get((c.date, c.outlet))
        if spec is None:
            continue  # no market probability to compare (e.g. the Fed's own projections)
        market, measure, at, before, what = spec
        P = count if market == "count" else meeting_probs(market)
        rows.append({"date": c.date, "outlet": c.outlet, "press_measures": what, "press_quote": c.quote,
                     "press_source_of_odds": c.odds_source,
                     "kalshi_market": "KXRATECUTCOUNT-25DEC31" if market == "count" else market,
                     "kalshi_measure": measure, "kalshi_time_et": at, "kalshi_value": value_at(P, measure, at),
                     "kalshi_before_time_et": before or "",
                     "kalshi_before_value": value_at(P, measure, before) if before else "",
                     "url": c.url})
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(ROOT, "results", "part1_press.csv"), index=False)
    print(out[["date", "outlet", "press_measures", "kalshi_measure", "kalshi_before_value", "kalshi_value"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()

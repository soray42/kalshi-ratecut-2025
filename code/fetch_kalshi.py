"""Download market records, hourly candles and trades from the public Kalshi API.

    python code/fetch_kalshi.py markets   # contract records for EVENTS -> data/raw/markets.csv
    python code/fetch_kalshi.py hourly    # hourly candles over each contract's life -> data/raw/hourly.csv
    python code/fetch_kalshi.py trades    # every trade in the 2025 rate-cut market -> data/raw/trades_cutcount25.csv

No API key is needed. All events here are settled, so they are served from the historical store.
"""
import csv, json, os, sys, time, urllib.error, urllib.request
from datetime import datetime

BASE = "https://api.elections.kalshi.com/trade-api/v2"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
COUNT = "KXRATECUTCOUNT-25DEC31"
FOMC = [f"KXFEDDECISION-{m}" for m in ("25JAN", "25MAR", "25MAY", "25JUN", "25JUL", "25SEP", "25OCT", "25DEC", "26JAN")]
PAYROLLS = [f"KXPAYROLLS-{m}" for m in ("24DEC", "25JAN", "25FEB", "25MAR", "25APR", "25MAY", "25JUN", "25JUL", "25AUG", "25SEP", "25NOV")]
EVENTS = [COUNT] + FOMC + PAYROLLS
FIELDS = ["event_ticker", "ticker", "title", "yes_sub_title", "strike_type", "floor_strike", "cap_strike",
          "open_time", "close_time", "status", "result", "expiration_value", "volume_fp", "open_interest_fp",
          "rules_primary"]


def get(url, tries=6):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (k + 1))
        except OSError:
            time.sleep(5 * (k + 1))
    raise RuntimeError(f"failed: {url}")


def markets():
    rows = []
    for ev in EVENTS:
        d = get(f"{BASE}/historical/markets?limit=1000&event_ticker={ev}") or {}
        got = d.get("markets", [])
        if not got:  # not yet moved to the historical store
            got = (get(f"{BASE}/markets?limit=1000&event_ticker={ev}") or {}).get("markets", [])
        rows += got
        print(ev, len(got), flush=True)
    with open(os.path.join(RAW, "markets.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def load_markets():
    with open(os.path.join(RAW, "markets.csv")) as fh:
        return list(csv.DictReader(fh))


def hourly():
    out = os.path.join(RAW, "hourly.csv")
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["event_ticker", "ticker", "end_ts", "yes_bid_close", "yes_ask_close", "price_close",
                    "volume", "open_interest"])
        for m in load_markets():
            if m["event_ticker"].startswith("KXPAYROLLS"):
                continue
            a, b = ts(m["open_time"]), min(ts(m["close_time"]), int(time.time()))
            n, t = 0, a
            while t < b:
                e = min(b, t + 100 * 86400)
                url = f"{BASE}/historical/markets/{m['ticker']}/candlesticks?start_ts={t}&end_ts={e}&period_interval=60"
                for c in (get(url) or {}).get("candlesticks", []):
                    yb, ya, pr = c.get("yes_bid", {}), c.get("yes_ask", {}), c.get("price", {})
                    w.writerow([m["event_ticker"], m["ticker"], c.get("end_period_ts"),
                                yb.get("close_dollars", yb.get("close")), ya.get("close_dollars", ya.get("close")),
                                pr.get("close_dollars", pr.get("close")),
                                c.get("volume_fp", c.get("volume")), c.get("open_interest_fp", c.get("open_interest"))])
                    n += 1
                t = e
            print(m["ticker"], n, flush=True)


def trades():
    out = os.path.join(RAW, "trades_cutcount25.csv")
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ticker", "created_time", "yes_price_dollars", "count_fp", "taker_side", "trade_id"])
        for m in load_markets():
            if m["event_ticker"] != COUNT:
                continue
            cur, n = None, 0
            while True:
                url = f"{BASE}/historical/trades?ticker={m['ticker']}&limit=1000" + (f"&cursor={cur}" if cur else "")
                d = get(url) or {}
                for x in d.get("trades", []):
                    w.writerow([x["ticker"], x["created_time"], x.get("yes_price_dollars"), x.get("count_fp"),
                                x.get("taker_side"), x["trade_id"]])
                    n += 1
                cur = d.get("cursor")
                if not cur or not d.get("trades"):
                    break
            print(m["ticker"], n, flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    {"markets": markets, "hourly": hourly, "trades": trades}[sys.argv[1]]()

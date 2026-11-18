# Kalshi 2025 rate-cut market and US jobs reports

Data for the club report on Kalshi's market "How many times will the Fed cut rates in 2025?"
([KXRATECUTCOUNT-25DEC31](https://kalshi.com/markets/kxratecutcount/number-of-rate-cuts/kxratecutcount-25dec31)).

Research question: *How quickly did Kalshi's 2025 rate-cut market absorb the news in US jobs reports, and what
factors affected the speed?* Kalshi's market on the next Fed meeting serves as the benchmark for when the news
itself was priced.

All market data come from the public Kalshi API (no key needed). Times are UTC unless a column says otherwise.

## Contents

```
data/raw/        whole life of the 2025 market (and the 2025 Fed-meeting markets), hourly + every trade
data/minute/     one-minute quotes and trades around 62 scheduled releases, Sep 2024 - Oct 2026
results/         event-study output and press quotes
figures/         fig1_life (daily implied cuts, from data/raw/hourly.csv), fig2_aug1 and fig_reports_2025 (Part 2 preview)
code/            fetch script and the Part 2 preview script
```

### data/raw

| File | What it is |
| --- | --- |
| `markets.csv` | One row per contract: the 15 contracts of the 2025 count market, the 5 contracts of each Fed meeting from Jan 2025 to Jan 2026, and Kalshi's payrolls markets for Dec 2024 to Nov 2025. `result` is yes/no at settlement; `expiration_value` holds the published number for payrolls; `volume_fp` is lifetime volume in contracts. |
| `hourly.csv` | Hourly candles over each contract's life (count market and Fed-meeting markets). `yes_bid_close`, `yes_ask_close`, `price_close` in dollars (0.30 = 30%); `volume` in contracts traded that hour; `open_interest` in contracts; `end_ts` is the Unix time at the end of the hour. |
| `trades_cutcount25.csv` | Every trade in the 2025 count market (64,731 trades, 20.6 million contracts). `yes_price_dollars`, `count_fp` (contracts), `taker_side`. |

One contract pays $1, so Kalshi's page shows volume in dollars equal to the number of contracts
($20,625,394 for this market). The count market has contracts "exactly 0 cuts" (`-T0`) to "exactly 13 cuts" (`-T13`)
and "14 or more" (`-T15`); a 50 bp cut counts as two. Fed-meeting contract suffixes: `H0` hold, `C25` cut 25 bp,
`C26` cut more than 25 bp, `H25`/`H26` hikes. The 2025 market resolved at exactly 3 cuts (17 Sep, 29 Oct, 10 Dec).

### data/minute

`releases.csv` lists the scheduled releases (`date`, `type` = NFP / CPI / FOMC, `release_utc`).
For each release date and each contract open at the time there are two files:

- `candles/<date>__<ticker>.csv`: one-minute bars from about a day before to a day or two after the release.
  `ts` Unix time; `bid`, `ask`, `close` in **cents**; `volume` and `open_interest` in contracts. A minute appears
  only when something changed, so carry the last quote forward.
- `trades/<date>__<ticker>.csv`: trades in the same window. `yes_price` in **cents**, `count` in contracts.

Series included: the count markets (`RATECUTCOUNT-24DEC31` for 2024, `KXRATECUTCOUNT-25DEC31`,
`KXRATECUTCOUNT-26DEC31`), the Fed-meeting markets (`FEDDECISION` in 2024, `KXFEDDECISION` from Dec 2024) and
Kalshi's market on the payrolls number (`PAYROLLS`, then `KXPAYROLLS`). Kalshi renamed its series with a `KX`
prefix in late 2024. The 2025 count market has files for every 2025 release.

### results

| File | What it is |
| --- | --- |
| `event_study/levels_by_minute.csv` | Implied value of each market by minute around each release, -60 to +180. `composite` is `decision_next` (expected policy-rate change at the next meeting, bp) or `cuts_ye` (implied number of cuts in the current year); `node` names the market used; `h` minutes from release; `dlevel` change from the average of the five minutes before release. `obs_any_60`: share of the first 60 minutes in which some contract of the market changed quote or traded. |
| `event_study/payrolls_surprises.csv` | Published payrolls (`published`), the expectation implied by Kalshi's payrolls market one hour before (`kalshi_expectation_1h_before`) and the difference (`surprise`). The delayed September 2025 report (released 20 Nov) has none: that market closed on the original date. |
| `event_study/beta_*.csv`, `paired_*.csv` | Average response to a payroll surprise across the 24 reports of Sep 2024 - Oct 2026, by minute (`b` = change per thousand jobs of surprise, in the market's own unit; 90% bootstrap band; `share` = b(h)/b(180)); `paired` compares the two markets on the same reports. `all` uses every report, `active` only reports with frequent quoting. |
| `part2_reports_2025.csv` | For each 2025 jobs report: surprise, the next-meeting market used, and the move of both markets at 15, 60 and 180 minutes in bp of the policy rate (count market at -25 bp per cut). |
| `press_claims.csv` | Dated quotes from press coverage about rate-cut odds, with links. All cite CME FedWatch (futures), none cite Kalshi. |

## Notes for Part 1

- To turn the count market into one number, take each contract's mid quote, rescale the fifteen so they sum to
  one, and average the counts. Watch the far tail: contracts for 9-13 cuts often sit at a 1-cent bid and 2-3 cent
  ask, and these quotes appear and disappear. Counting them moves the implied number of cuts by up to 0.7 on
  days with no news (21 Jan, 24 Jan, 28 Feb 2025). Treating a contract bid at 1 cent or less as zero removes this.
- Early in the market's life (Dec 2024) spreads are wide; prices from those days are less reliable.

## Reproduce

```
python code/fetch_kalshi.py markets   # then: hourly, trades
python code/part2_preview.py          # results/part2_reports_2025.csv, figures/fig2_aug1.png, figures/fig_reports_2025.png
```

Python 3.10+, pandas, numpy, matplotlib. The minute files and `results/event_study` were produced by an earlier
pipeline and are included as they are.

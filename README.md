# Kalshi 2025 rate-cut market and US jobs reports

Club report on Kalshi's market "How many times will the Fed cut rates in 2025?"
([KXRATECUTCOUNT-25DEC31](https://kalshi.com/markets/kxratecutcount/number-of-rate-cuts/kxratecutcount-25dec31)).

**Research question.** How quickly did Kalshi's 2025 rate-cut market absorb the news in US jobs reports, and what
factors affected the speed? Kalshi's market on the next Fed meeting serves as the benchmark for when the news itself
was priced.

**Deadlines.** Check-in 1 (Part 1 market summary) Thu 19 Nov · full draft Thu 26 Nov · final report (PDF, data,
code) Tue 1 Dec · presentation Wed 2 Dec.

## Working in this repo (people and AI agents)

Most of us work with AI coding agents. Left alone they leave scratch files everywhere, copy data, rewrite files
nobody asked them to touch and write long Markdown summaries. **Every agent working here must follow this
section.** If your agent does not read README files by itself, paste this section into its instructions.

### Layout

Do not create new top-level folders.

| Folder | Rule |
| --- | --- |
| `data/raw/`, `data/minute/` | **Read-only.** Never edit, re-save, rename or delete these files. New data: write `code/fetch_<what>.py`, save to a new file in `data/raw/`, and list it in this README. |
| `data/derived/` | Intermediate tables, each written by a script in `code/`. |
| `code/` | One script per task, named `part1_<topic>.py`, `part2_<topic>.py` or `fetch_<what>.py`. Runs from the repo root (`python code/part1_volume.py`), builds paths from the repo root, writes only to `data/derived/`, `results/` or `figures/`. |
| `results/` | CSV tables the report quotes, named after the script that makes them (`part1_volume.py` writes `results/part1_volume.csv`). |
| `figures/` | Figures for the report, named the same way (`figures/part1_volume.png`). |
| `notebooks/` | Exploration only; clear outputs before committing. Nothing in the report may come only from a notebook. |
| `report/` | Report source and the final PDF. |

### Do not commit

- Scratch and test files: `test.py`, `tmp_*`, `untitled*`, `*_old*`, `*_v2_final*`, backups.
- Copies of data that already exist in `data/`, or files over 10 MB without agreeing in the group first.
- Caches and environments: `__pycache__/`, `.ipynb_checkpoints/`, `.venv/`.
- Credentials of any kind. The Kalshi API used here needs no key.
- Extra Markdown files (`NOTES.md`, `SUMMARY.md`, `PLAN.md`, `CHANGELOG.md`, agent reports). `README.md` is the only
  Markdown file. If something needs documenting, add a few lines to the right section here.

### Making changes

- Work on a branch named `<name>/<topic>` and open a pull request into `main`; another member looks at it before it
  is merged. Do not push to `main` directly.
- One purpose per commit, with a short plain message (`Add monthly volume table`). No AI attribution or co-author
  lines, no emojis.
- Only touch the files your task needs. Do not reformat, rename or "clean up" other files, and never delete someone
  else's file without asking in the group chat.
- Run `git status` before every commit and remove anything that does not belong.

### Code

- Python 3.10+ with the packages in `requirements.txt`. Add a package only if it is really needed, and list it there.
- Fixed choices (thresholds, dates, windows) go at the top of the script as named constants.
- Short English comments where the code is not obvious. No comments that narrate what the agent did.
- Set random seeds wherever there is randomness (bootstrap, sampling).

### Numbers and methods

- Every number in the report must come from a file in `results/` that a script in `code/` produces.
- Use the conventions below. If a convention looks wrong, raise it with the group rather than changing it in one
  script.
- An agent may propose a method choice (a threshold, a window, a statistic, a chart type); a person checks it before
  it goes into the report.

## Conventions

- **Time.** Data files are in UTC. Daily values use the US Eastern calendar (America/New_York), end of day. Jobs
  reports come out at 8:30 ET.
- **Prices.** Dollars in `data/raw/` (0.30 = 30%), cents in `data/minute/` (30.0 = 30%). One contract pays $1, so
  volume in contracts equals volume in dollars as Kalshi's page reports it.
- **Implied distribution of the count market.** Mid quote of each contract; a contract with a bid of 1 cent or less
  (or no bid) counts as zero; rescale the fifteen values to sum to one; "14 or more" counts as 14. Without the 1-cent
  rule, quotes on the 9-13 cut contracts that appear and disappear move the implied number of cuts by up to 0.7 on
  days with no news (21 Jan, 24 Jan, 28 Feb 2025).
- **Policy-rate units.** The count market converts at -25 bp per cut, so both markets read as an expected change in
  the policy rate.
- **Next-meeting market.** The Fed meeting that comes first after the release.
- **Jobs surprise.** Published payrolls minus the expectation implied by Kalshi's payrolls market one hour before
  the release.
- Early in the market's life (Dec 2024) spreads are wide; prices from those days are less reliable.

## Contents

```
data/raw/        whole life of the 2025 market and the 2025 Fed-meeting markets: hourly quotes, every trade
data/minute/     one-minute quotes and trades around 62 scheduled releases, Sep 2024 - Oct 2026
data/derived/    implied distribution of the count market, by hour and by day
results/         Part 1 tables (largest moves, press vs Kalshi, liquidity); Part 2 event study (all
                 specifications), contract-level moves, the 2025 report table; press quotes
figures/         Part 1 and Part 2 figures
code/            fetch script, Part 1 and Part 2 scripts
```

### data/raw

| File | What it is |
| --- | --- |
| `markets.csv` | One row per contract: the 15 contracts of the 2025 count market, the 5 contracts of each Fed meeting from Jan 2025 to Jan 2026, and Kalshi's payrolls markets for Dec 2024 to Nov 2025. `result` is yes/no at settlement; `expiration_value` holds the published number for payrolls; `volume_fp` is lifetime volume in contracts. |
| `hourly.csv` | Hourly candles over each contract's life (count market and Fed-meeting markets). `yes_bid_close`, `yes_ask_close`, `price_close` in dollars; `volume` in contracts traded that hour; `open_interest` in contracts; `end_ts` Unix time at the end of the hour. |
| `trades_cutcount25.csv` | Every trade in the 2025 count market (64,731 trades, 20.6 million contracts): `yes_price_dollars`, `count_fp` (contracts), `taker_side`. |

The count market has contracts "exactly 0 cuts" (`-T0`) to "exactly 13 cuts" (`-T13`) and "14 or more" (`-T15`); a
50 bp cut counts as two. Fed-meeting contract suffixes: `H0` hold, `C25` cut 25 bp, `C26` cut more than 25 bp,
`H25`/`H26` hikes. The 2025 market resolved at exactly 3 cuts (17 Sep, 29 Oct, 10 Dec) with $20,625,394 in volume.

### data/minute

`releases.csv` lists the scheduled releases (`date`, `type` = NFP / CPI / FOMC, `release_utc`).
`contracts.csv` lists, for each release, every contract of these series that was open one hour before it:
`role` is `settles` (the contract resolves on this release, e.g. the payrolls market on a jobs report) or `forward`;
it also carries the contract terms (`event_ticker`, `strike_type`, `floor_strike`, `cap_strike`, `close_time`,
`result`, `expiration_value`). For each release and contract there are two files:

- `candles/<date>__<ticker>.csv`: one-minute bars from about a day before to a day or two after the release.
  `ts` Unix time; `bid`, `ask`, `close` in cents; `volume` and `open_interest` in contracts. A minute appears only
  when something changed, so carry the last quote forward.
- `trades/<date>__<ticker>.csv`: trades in the same window; `yes_price` in cents, `count` in contracts.

Series: the count markets (`RATECUTCOUNT-24DEC31` for 2024, `KXRATECUTCOUNT-25DEC31`, `KXRATECUTCOUNT-26DEC31`),
the Fed-meeting markets (`FEDDECISION` in 2024, `KXFEDDECISION` from Dec 2024) and Kalshi's payrolls market
(`PAYROLLS`, then `KXPAYROLLS`). Kalshi's series names gained a `KX` prefix in late 2024. `data/minute/` was
collected with an earlier pipeline and is included as it is.

### code and results (Part 1)

| Script | Output | What it does |
| --- | --- | --- |
| `part1_implied.py` | `data/derived/cutcount25_{hourly,daily}.csv` | Implied distribution over the number of cuts (`p0`-`p14`) and its mean (`implied_cuts`), by hour and at each US Eastern end of day, with the 1-cent rule in Conventions; hours where a 1-4 cut contract is quoted wider than 5 cents are dropped. The daily file also has the median spread of the 1-4 cut contracts, open interest, volume and trades. The other part1 scripts import from it. |
| `part1_top_moves.py` | `results/part1_top_moves.csv`, `figures/part1_top_moves.png` | The ten largest day-to-day changes in the implied number of cuts in 2025, the contract that moved most, volume, any scheduled release that day, and the news that day with a link (collected by hand, in the script). |
| `part1_press.py` | `results/part1_press.csv` | Each press quote in `press_claims.csv` that states a market probability, next to Kalshi's price for the same question at 4 pm US Eastern that day (10 am for the article that says "Friday morning") and, where the article compares with the day before, at the same time a day earlier. |
| `part1_liquidity.py` | `results/part1_liquidity.csv`, `results/part1_liquidity_by_contract.csv`, `figures/part1_liquidity.png` | By month: volume, trades, open interest at month end, median daily spread of the 1-4 cut contracts. By contract: share of lifetime volume and share of 2025 hourly quotes with a bid of 2 cents or more. |

Part 1 figures use a dark style to match the check-in template.

### code and results (Part 2)

| Script | Output | What it does |
| --- | --- | --- |
| `part2_event_study.py` | `results/part2_event_study/<run>/` | Implied value of both markets by minute (-60 to +180) around every release, the payrolls surprise, and the regressions across the 24 jobs reports (Sep 2024 - Oct 2026). |
| `part2_contract_moves.py` | `results/part2_contract_moves.csv` | Size and timing of each contract's move at the release and at the same clock time one day earlier and later. |
| `part2_reports_2025.py` | `results/part2_reports_2025.csv`, `figures/part2_aug1.png`, `figures/part2_reports_2025.png` | The eleven 2025 jobs reports one by one. |
| `part2_share.py` | `figures/part2_share.png` (active), `figures/part2_share_all.png` | Average response to a one-s.d. surprise and the share of the three-hour response by minute. |

Runs of `part2_event_study.py` (`<run>` folder): `all` (every report), `active` (`--min-obs 0.5`: only markets in
which some contract changed quote or traded in at least half of the first 60 minutes), `lookback60` (quotes carried
forward at most 60 minutes), `placebo_day_before` / `placebo_day_after` (`--placebo -1440/1440 --lookback 60`: the
same clock time one day earlier or later, when there is no release; the responses should be zero).

Files in each run folder:

- `levels.csv`: `composite` is `decision_next` (expected policy-rate change at the next meeting, bp) or `cuts_ye`
  (implied number of cuts in the current year); `market` names the Kalshi event used; `h` minutes from the
  release; `level` the implied value; `dlevel` its change from the average of the five minutes before the release;
  `obs_any_60` share of minutes 1-60 in which some contract changed quote or traded; `spread_pre` median
  pre-release spread (cents).
- `surprises.csv`: published payrolls, Kalshi's expectation one hour before, and the surprise, in thousands of jobs.
  The delayed September 2025 report (released 20 Nov) has none: that payrolls market closed on the original date.
- `beta.csv`: by minute, `b` = change per thousand jobs of surprise in the market's own unit, 90% bootstrap band,
  `share` = b(h)/b(180) with its band (only when the three-hour response is clearly non-zero).
- `table.csv`: the same at 1, 2, 5, 10, 15, 30, 60, 90, 120 and 180 minutes, plus `b_sd` (response to a
  one-s.d. surprise), leave-one-report-out ranges (`b_loo_*`, `share_loo_*`) and the most influential report.
- `paired.csv`: both markets on the same reports and bootstrap draws, in bp for a one-s.d. surprise: each response,
  their difference (`level_diff_bp`) and the difference in shares (`share_diff`).

`part2_contract_moves.csv`: one row per contract settling more than 20 days after the release and per `shift`
(0 at the release, -1440 / 1440 the day before / after). `R` move in cents from just before to 2-3 hours after,
`tau90` minutes until 90% of the move was reached and held, `half_spread` in cents.

The event study uses the earlier pipeline's rule for the count market (threshold ladders made non-increasing,
buckets rescaled, contracts with a median pre-release spread above 20 cents dropped), not the 1-cent rule in
Conventions. The port reproduces the earlier
results exactly except for the bootstrap bands, which differ slightly because the random draws differ.

`press_claims.csv`: dated quotes from press coverage on rate-cut odds, with links. Most cite CME FedWatch
(futures); none cite Kalshi.

Main findings so far (24 reports): the next-meeting market completes its three-hour response within 15 minutes;
the count market has done about 40% after 15 minutes and about 70% after an hour; at the same clock time on the
day before or after, both stay within 0.2 bp of zero at 5 and 30 minutes. With the 2025 reports alone the pattern
is weaker and leans on 10 January 2025.

## Reproduce

```
pip install -r requirements.txt
python code/fetch_kalshi.py markets          # then: hourly, trades (data/raw)
python code/part1_implied.py
python code/part1_top_moves.py
python code/part1_press.py
python code/part1_liquidity.py
python code/part2_event_study.py             # then the other runs listed above
python code/part2_contract_moves.py
python code/part2_reports_2025.py
python code/part2_share.py && python code/part2_share.py all
```

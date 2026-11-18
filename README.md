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
results/         event-study output from earlier work, the 2025 report table, press quotes
figures/         figures from the proposal and earlier work
code/            fetch script and the Part 2 preview script
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

`releases.csv` lists the scheduled releases (`date`, `type` = NFP / CPI / FOMC, `release_utc`). For each release
date and each contract open at the time there are two files:

- `candles/<date>__<ticker>.csv`: one-minute bars from about a day before to a day or two after the release.
  `ts` Unix time; `bid`, `ask`, `close` in cents; `volume` and `open_interest` in contracts. A minute appears only
  when something changed, so carry the last quote forward.
- `trades/<date>__<ticker>.csv`: trades in the same window; `yes_price` in cents, `count` in contracts.

Series: the count markets (`RATECUTCOUNT-24DEC31` for 2024, `KXRATECUTCOUNT-25DEC31`, `KXRATECUTCOUNT-26DEC31`),
the Fed-meeting markets (`FEDDECISION` in 2024, `KXFEDDECISION` from Dec 2024) and Kalshi's payrolls market
(`PAYROLLS`, then `KXPAYROLLS`). Kalshi's series names gained a `KX` prefix in late 2024.

### results

These come from earlier work on 24 jobs reports (Sep 2024 - Oct 2026) and are the starting point for Part 2.

| File | What it is |
| --- | --- |
| `event_study/levels_by_minute.csv` | Implied value of each market by minute, -60 to +180 around each release. `composite` is `decision_next` (expected policy-rate change at the next meeting, bp) or `cuts_ye` (implied number of cuts in the current year); `node` names the market; `h` minutes from release; `dlevel` change from the average of the five minutes before; `obs_any_60` share of the first 60 minutes in which some contract changed quote or traded. These were computed with the earlier pipeline's rule for the count market, not the 1-cent rule in Conventions. |
| `event_study/payrolls_surprises.csv` | Published payrolls, Kalshi's expectation one hour before, and the surprise. The delayed September 2025 report (released 20 Nov) has none because that market closed on the original date. |
| `event_study/beta_*.csv` | Average response to a payroll surprise by minute: `b` = change per thousand jobs of surprise in the market's own unit, 90% bootstrap band, `share` = b(h)/b(180). `all` every report; `active` only reports with frequent quoting; `lookback60` quotes carried forward at most 60 minutes; `placebo_day_before` / `placebo_day_after` the same clock time one day earlier or later, with no release. |
| `event_study/table_*.csv` | The same at 1, 2, 5, 10, 15, 30, 60, 90, 120 and 180 minutes, with leave-one-report-out ranges (`b_loo_*`, `share_loo_*`) and the most influential report. |
| `event_study/paired_*.csv` | The two markets on the same reports and bootstrap draws: each response in bp, their difference (`level_diff_bp`) and the difference in shares (`share_diff`). |
| `event_study/contract_moves.csv` | Contract-level moves for contracts settling more than 20 days after each release (all series in the earlier data): `R` move in cents from before to 2-3 hours after, `tau90` minutes until 90% of the move was reached and held, `hspread` half the median spread; `shift` 0 at the release, -1440 / 1440 the day before / after. |
| `part2_reports_2025.csv` | Each 2025 jobs report: surprise, next-meeting market used, and the move of both markets at 15, 60 and 180 minutes in bp. |
| `press_claims.csv` | Dated quotes from press coverage on rate-cut odds, with links. Most cite CME FedWatch (futures); none cite Kalshi. |

Main findings so far (24 reports): the next-meeting market completes its three-hour response within 15 minutes; the
count market has done about 40% after 15 minutes and about 70% after an hour; at the same clock time on the day
before or after, both stay within 0.2 bp of zero at 5 and 30 minutes. With the 2025 reports alone the pattern is weaker and leans on 10 January 2025.

### figures

| File | What it shows |
| --- | --- |
| `fig1_life.png` | Daily implied number of 2025 cuts and the prices of 1, 2 and 3 cuts, with jobs reports and the three cuts marked. Draft from the proposal, made with the conventions above; Part 1 replaces it with a script in `code/`. |
| `fig2_aug1.png` | Minute-by-minute response of both markets to the 1 August 2025 jobs report. |
| `fig_reports_2025.png` | The same for each of the eleven 2025 jobs reports. |
| `fig_share_24reports.png` | Average response and share of the three-hour response by minute, 24 reports, active sample. |

## Reproduce

```
pip install -r requirements.txt
python code/fetch_kalshi.py markets   # then: hourly, trades
python code/part2_preview.py          # results/part2_reports_2025.csv, fig2_aug1.png, fig_reports_2025.png
```

`data/minute/` and `results/event_study/` were produced by an earlier pipeline and are included as they are.

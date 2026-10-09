# nfl-odds

Automatic NFL receptions-prop odds pulls (DraftKings + FanDuel via The Odds API) for Alex's prop model.

- `pull_odds.py` — the puller. Needs the `ODDS_API_KEY` repository secret.
- `.github/workflows/pull-odds.yml` — runs Wed (first look), Fri (after injury reports), Sun (closing lines); can also be run by hand from the Actions tab ("Run workflow").
- `odds/latest.json` — most recent pull; `odds/<UTC timestamp>.json` — every pull, kept for line-movement and closing-line checks.

Each pull costs ~2 API credits per game (~30 per week-slate). Free plan: 500/month.

## Test market: receiving yards
- `.github/workflows/pull-yards.yml` pulls alternate receiving-yards ladders once a week (Wednesday) into `yards/`.
  It is graded silently for a few weeks; nothing is bet from it. It skips itself when credits drop under 150.

"""Pull NFL receptions props (DraftKings + FanDuel, plus 8 other US books for consensus) from The Odds API.

Saves compact rows to odds/<UTC timestamp>.json and odds/latest.json:
  {"pulled_at": ..., "credits_remaining": ..., "rows": [[game, commence, book, player, side, point, price], ...]}
Only games that haven't kicked off and start within the next 7 days. ~2 credits per game.
"""
import datetime as dt, json, os, sys, urllib.request

KEY = os.environ["ODDS_API_KEY"]
BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
MARKETS = os.environ.get("MARKETS", "player_receptions_alternate,player_receptions")
OUTDIR = os.environ.get("OUTDIR", "odds")
# skip the pull if credits are below this (keeps room for the receptions pulls, which come first)
MIN_CREDITS = int(os.environ.get("MIN_CREDITS", "40"))
# Up to 10 bookmakers cost the same as one region (~2 credits/game). DK + FD are where Alex bets;
# the rest give a market consensus to spot when DK/FD are out of line.
BOOKS = "draftkings,fanduel,betmgm,williamhill_us,espnbet,fanatics,betrivers,hardrockbet,bovada,betonlineag"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r), r.headers.get("x-requests-remaining")


now = dt.datetime.now(dt.timezone.utc)
events, left = get(f"{BASE}/events?apiKey={KEY}")  # free call; header tells us credits left
if left is not None and int(left) < MIN_CREDITS:
    print(f"only {left} credits left (< {MIN_CREDITS}); skipping {OUTDIR} pull")
    sys.exit(0)
todo = [e for e in events
        if now < dt.datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00")) < now + dt.timedelta(days=7)]
rows = []
for e in todo:
    try:
        j, left = get(f"{BASE}/events/{e['id']}/odds?apiKey={KEY}&regions=us&markets={MARKETS}"
                      f"&bookmakers={BOOKS}&oddsFormat=american")
    except Exception as ex:  # one bad game shouldn't sink the pull
        print("failed", e.get("home_team"), ex, file=sys.stderr)
        continue
    g = f"{j['away_team']} @ {j['home_team']}"
    for b in j.get("bookmakers", []):
        for m in b["markets"]:
            for o in m["outcomes"]:
                rows.append([g, j["commence_time"], b["key"], o.get("description"), o["name"], o.get("point"), o["price"]])

out = dict(markets=MARKETS, pulled_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"), games=len(todo), credits_remaining=left, rows=rows)
os.makedirs(OUTDIR, exist_ok=True)
stamp = now.strftime("%Y-%m-%d_%H%M")
for path in (f"{OUTDIR}/{stamp}.json", f"{OUTDIR}/latest.json"):
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
print(f"games {len(todo)}, rows {len(rows)}, credits left {left}")

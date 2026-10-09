"""Pull NFL receptions props (DraftKings + FanDuel) from The Odds API.

Saves compact rows to odds/<UTC timestamp>.json and odds/latest.json:
  {"pulled_at": ..., "credits_remaining": ..., "rows": [[game, commence, book, player, side, point, price], ...]}
Only games that haven't kicked off and start within the next 7 days. ~2 credits per game.
"""
import datetime as dt, json, os, sys, urllib.request

KEY = os.environ["ODDS_API_KEY"]
BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
MARKETS = "player_receptions_alternate,player_receptions"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r), r.headers.get("x-requests-remaining")


now = dt.datetime.now(dt.timezone.utc)
events, left = get(f"{BASE}/events?apiKey={KEY}")
todo = [e for e in events
        if now < dt.datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00")) < now + dt.timedelta(days=7)]
rows = []
for e in todo:
    try:
        j, left = get(f"{BASE}/events/{e['id']}/odds?apiKey={KEY}&regions=us&markets={MARKETS}"
                      f"&bookmakers=draftkings,fanduel&oddsFormat=american")
    except Exception as ex:  # one bad game shouldn't sink the pull
        print("failed", e.get("home_team"), ex, file=sys.stderr)
        continue
    g = f"{j['away_team']} @ {j['home_team']}"
    for b in j.get("bookmakers", []):
        for m in b["markets"]:
            for o in m["outcomes"]:
                rows.append([g, j["commence_time"], b["key"], o.get("description"), o["name"], o.get("point"), o["price"]])

out = dict(pulled_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"), games=len(todo), credits_remaining=left, rows=rows)
os.makedirs("odds", exist_ok=True)
stamp = now.strftime("%Y-%m-%d_%H%M")
for path in (f"odds/{stamp}.json", "odds/latest.json"):
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
print(f"games {len(todo)}, rows {len(rows)}, credits left {left}")

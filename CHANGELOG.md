# Forge Daily Brief — change log

Hand-maintained. Newest first. Written so a future session can pick up cold.

## How the pieces fit

| File | Maintained how | Deploy |
|---|---|---|
| `forge_actions.py` | the **generator** — builds the brief | patch, push, **then run the workflow** |
| `index.html` | **generated output** | never edit by hand |
| `planner.html` | hand-maintained | patch and push, no workflow |
| `forge-evening-debrief.html` | hand-maintained | patch and push, no workflow |

Sync goes through a Cloudflare Worker at `forge-sync.yoseanreid.workers.dev`.
A green workflow run is **not** evidence code was pushed — verify by fetching the
raw file from `gh-pages` and comparing its hash.

## 2026-08-03

### install17 — planner links stay inside the app
The planner's link back to the brief was an absolute `https://theseanman.github.io/...`
URL. Changed to `./`. See install16 for why.

### install16 — brief links stay inside the app
All four navigation links in the generated brief (input, planner, models ×2) were
absolute URLs. On iOS, a link to an absolute URL inside a home-screen web app is
treated as leaving the app, so it opens in an in-app browser **with a different,
non-persistent storage jar**. That is why mushin minutes recorded via the brief's
planner link vanished on reopen, while the same timer used from a planner icon
persisted. All four are now relative.

### install15 — scoped goal 5, practice card on the brief
Paramount Goal 5 changed from "NO NARRATIVES / shut down internal narratives the
moment they begin" to "NOT RELEVANT", with an explicit scope line: optimization
thoughts only, not a general silencer. Added a Practice card under Today's Five
showing mushin against 10:00 today and project time against the 3h weekly floor.

### install14 — practice timers in the planner
Mushin timer (10 min/day, resets at midnight) and project timer (3h/week, resets
Monday, with a streak of weeks clearing the floor). Time accrues by wall clock so
the phone can be locked. Any single unattended stretch is capped at 60 minutes and
then pauses itself; a timer left running into a new day is closed out against the
day it belonged to. Sync merge for these keys is max-wins on seconds, so a stale
copy can never reduce an accumulated total.

### install13 — daily frame, OPTIMIZE/IMMERSE, mushin row
Evening debrief gained the daily frame, OPTIMIZE/IMMERSE task tags, and a mushin
row. Mushin auto-marks done at 600 seconds, so the timer fills it in.

## Known open items

- **The Worker does not recognise `forge-mushin` or `forge-project`.** `GET /forge-mushin`
  returns `{"error":"unknown key"}` while `/forge-top5` returns data, so the Worker is
  healthy but appears to serve a fixed allowlist. Until that is fixed these two keys live
  in local storage only and have **no cloud backup**. Fixing it means editing the Worker,
  not this repo.
- **Encoding.** The raw Worker view renders curly apostrophes as `â€™`. Believed to be a
  display fault in that view only, since the brief parses with `r.json()`. Unconfirmed.
- **Debrief loads without pulling.** The evening debrief never pulls from the Worker on
  load, and an empty cloud entry can still overwrite a populated local one.
- **Repo clutter.** Roughly 40 untracked files on `gh-pages` (old `.bak` files, `patch_*.py`).
  Always stage by explicit filename; never `git add .`.

## Travel override

`FORGE_TZ`, `FORGE_LAT`, `FORGE_LON` are repository variables. With all three unset the
brief builds exactly as it did for Richmond. To revert after travel, delete the three
variables under Settings → Secrets and variables → Actions → Variables and re-run the
workflow. No code change is needed.

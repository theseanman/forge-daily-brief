# FORGE DAILY BRIEF — DEPLOY STATE

**Last updated:** 2026-08-14
**Purpose:** the one place that says what's live, which installer names are taken,
what's parked, and how to deploy safely. Read this before building or running any
installer. Keeping it current is what stops the kind of mess that happened on Aug 14.

---

## 1. WHAT IS LIVE RIGHT NOW

- **Repo:** `github.com/theseanman/forge-daily-brief`, branch **gh-pages**
- **Live site:** theseanman.github.io/forge-daily-brief
- **Generator:** `forge_actions.py` — current live SHA:
  `c888ab079a28a634a3315a25806eeb15ef7e6ca489ac51e9e54706e440621e35`
- **`index.html` is generated output.** Never hand-edit it. It's rebuilt when the
  Actions workflow runs.

### Fixes deployed Aug 14 2026 (both verified live)

1. **Sleep score fix** — the Sleep card, SITREP, and red banner now prefer the
   Health-Auto-Export `computed_score` and fall back to the manual score when it's
   absent. Shipped by `sleepfix_computed_aug14.py`. (Fixed the brief showing a
   stale 62 instead of the real 85.)
2. **Calendar loud-failure safeguard** — calendar lookups that used to fail
   silently now show up in the red "CALENDAR FEED PROBLEM" banner, with the
   calendar name, the error type, and a count of any unparseable events. Shipped
   by `calfix_loud_errors_aug14.py`.

---

## 2. INSTALLER NAMING — READ THIS FIRST

**The `forge_installNN.py` name series belongs to Sean's own prior builds.**
Downloads and the repo are full of them (numbers seen: 2–35, not contiguous).
Do NOT create a new installer with a `forge_installNN.py` name — it WILL collide
with an old one, and running the wrong file is exactly what broke Aug 14.

**Rules for any new installer (Claude or Sean):**
- Name it descriptively and dated, never `installNN` — e.g.
  `sleepfix_computed_aug14.py`, `calfix_loud_errors_aug14.py`.
- Before running, **verify its SHA**: `shasum -a 256 <file>` must match the value
  given when it was built. A wrong or corrupted file can't match, so it can't run
  by accident.
- Build every installer against the CURRENT live generator SHA (section 1), and
  have it refuse to run if the file it finds doesn't match that pre-image.

---

## 3. INSTALLER NUMBERS KNOWN TO BE USED

These `forge_installNN.py` names already exist in Downloads and/or the repo. This
list is for collision-avoidance, not a full history.

- **install2–11** — earlier brief/calendar/sleep builds (11 = REM/Core/Deep row).
- **install13–30** — a dense range of prior work (Aug 3–7 sessions).
- **install31, install32** — in the repo; 32 set the red sleep-banner threshold to 90.
- **install33** — PARKED build: adds the "exit number" to the evening debrief.
- **install34** — PARKED build: daily health push (accumulates `forge-health-daily`).
- **install35** — referenced (weekly trend), not yet inspected.

Treat every number 2–35 as taken. Higher numbers may also exist — check first.

---

## 4. PARKED WORK (real, unfinished — do NOT run casually)

Both are legitimate features that were mid-flight. Each needs its own focused
session AND a Cloudflare step. They are renamed in the repo so they can't be
mistaken for a live installer:

- **`forge_exitnumber_build.py`** (was `forge_install33.py`) — adds a monthly
  "exit number" (non-teaching income vs teaching salary) to the evening debrief's
  Sunday review. Patches `forge-evening-debrief.html`. Still needs: a Cloudflare
  paste adding `'forge-exit'` to the Worker KEYS array. Also has a salary figure
  baked in that should be confirmed before shipping.
- **`forge_install34.py`** (daily health push — consider renaming to
  `forge_healthpush_build.py`) — each brief load stores today's sleep + HRV to a
  synced `forge-health-daily` key, building history for a future weekly trend.
  Patches `forge_actions.py`. Still needs: a Cloudflare paste adding
  `'forge-health-daily'` to the Worker KEYS array.

**Also parked:** a git stash named `wip-evening-debrief-uninvestigated-2026-08-14`.
This turned out to be the exit-number installer's output (not mystery work), so it
can be dropped once the exit-number feature is properly handled.

---

## 5. THE DEPLOY ROUTE THAT WORKS

Downloads-to-folder and Terminal here-docs both failed on Aug 14 (downloads didn't
land; here-doc paste corrupted the file). **The reliable route:**

1. **Browser** → `github.com/theseanman/forge-daily-brief` → confirm branch
   dropdown says **gh-pages** → **Add file → Create new file**.
2. Name the file, paste its full contents, **Commit directly to gh-pages**.
3. **Terminal** (in `~/Desktop/forge-daily-brief`):
   - `git pull --rebase`  (brings the new file down)
   - `shasum -a 256 <file>`  (must match the expected SHA — do NOT run if it doesn't)
   - `python3 <file>`  (runs the installer; expect an "OK" line + a post SHA)
   - `git add forge_actions.py <file>`  (name files explicitly — never `git add .`)
   - `git commit -m "..."`
   - `git pull --rebase`
   - `git push`
4. **Browser** → repo **Actions** tab → the main workflow → **Run workflow** →
   branch **gh-pages** → **Run**. This regenerates `index.html`.

A generator change is only live after BOTH the push AND the workflow run.

---

## 6. OPEN WORK (priority order)

1. ~~Sleep score fix~~ — **DONE Aug 14.**
2. ~~Calendar loud-failure safeguard~~ — **DONE Aug 14.**
3. **HAE cadence / workflow-cron fix** — this morning's root cause: the health
   auto-export didn't fire overnight (iOS blocks health reads while the phone is
   locked, and a once-a-day cadence gets one shot). Options: shorten the export
   cadence for more unlocked windows, and/or shift the workflow cron later so the
   export has time to land before the brief regenerates. Decision + small change.
   NOTE: the HAE Premium trial started Aug 13 — **buy LIFETIME before ~Aug 20** or
   background auto-export stops.
4. **Daily record + CSV export + git-history backfill** — the correlation blocker
   (join sleep/HRV to task completion). The meaty build. Not yet started.
5. **Finish the parked builds** — exit-number and health-push (section 4), each
   with its Cloudflare paste.
6. Live Rangers fixtures via ESPN; betting-intel 404; `calendar.date_search` →
   `calendar.search` deprecation.
7. Ringette feed is dead (off-season) — comment out with a dated note.
8. Consider setting `SI_TOKEN` on `/sleep-import` (the endpoint writes to live
   `data.json` and is currently open).

---

## 7. TIDY-UP CANDIDATES (safe, low priority)

- Backup files piling up in the repo: `forge_actions.py.*.bak-*`,
  `forge_actions.py.bak.20260810-111237`. Harmless; can be deleted anytime.
- Duplicate `content/content/*.json` copies may exist (nothing reads them).
- `sleep_score: 0` rows in the browser's `forge-health-history` (~Jul 20–30) need a
  one-off 0→absent pass before the first correlation run.

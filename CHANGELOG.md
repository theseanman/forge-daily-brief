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
`gh-pages` **branch archive** from `codeload.github.com` and comparing hashes.
Do **not** verify via `raw.githubusercontent.com`; it serves stale copies for
minutes after a push and has twice caused a deploy to be wrongly declared failed.

## 2026-08-06 / 07

### install28 — the planner actually pushes the five
`syncPush(K_TOP5)` sat **below** `saveTop5`'s closing brace, and `syncPush(K_PLAN)`
below `savePlan`'s. Both were stray top-level statements: they fired once at page
load and never on save. Saving the five wrote to local storage and stopped there,
so the Worker received nothing after 2026-08-03. This is install11's bug
reintroduced on a different page.

Both calls moved inside their functions. Also added the emptiness guard the planner
never got — the debrief got one in install18, the brief in install19. A cloud entry
that is blank can no longer overwrite a populated local one.

**Deliberate trade-off:** deliberately *clearing* the five on one surface will not
propagate to the other; it has to be cleared in both. Principle applied:
stale-but-present beats silently wiped.

Verified by AST rather than brace counting — the patched file parses and contains
zero top-level call statements, so no other strays are hiding.

**Note on installer self-checks:** the first draft of this installer asserted a
hardcoded brace delta and failed closed because the real delta differed by one.
Assert the *invariant* (open delta equals close delta), never the arithmetic.

### Repo tidy
Roughly 33 `.bak`/`.backup` files moved to a vault folder **outside** the repo —
rollbacks still exist, they are simply no longer tracked. About 22 dead one-off
patchers (`patch_*.py`, `forge_actions_patched.py`, `input_patched.html`) moved
alongside them. Installers 10, 11, 22, 23, 24, 25 and 27 committed, since they are
the change history and should not float untracked. A `.gitignore` now covers
`*.bak`, `*.bak-*`, `*.backup`, `*.backup-*`.

Three files were sitting in the repo literally named `python3 forge_installNN.py` —
the whole shell command had been typed into the GitHub web editor's filename field.
Their patches had been applied from elsewhere, so removing them lost nothing. When
giving web-editor instructions, say explicitly to clear the filename field first.

## 2026-08-03 (later)

### install27 — cue block and three-tier decision rule
Generator change. Seven cue strings on the brief plus a three-tier decision rule.
Blue `#1a5fa8`, consistent with the existing blue-gradient card. No sunset: silent
removal during a bad month is a real failure mode. **Supersedes install26, which
must never be run** — install27 targets install24's post-image directly and will
refuse on the pre-image check if install26 was applied.

### install25 — video audit logging and the Sunday checklist
Debrief change, runs after install23. A tick in the step-5 reps card lets an audit
be logged on any day, which is what makes the twice-weekly front-load work without
a scheduler. A three-item checklist was added inside install20's existing Sunday
review, with a count of audits done that week. New key `forge-video`,
`{date: {done: true}}`, 60-day prune.

**The checklist is review-only and the copy must keep saying so.** Running it
*during* a conversation reinstates the self-monitoring loop the build exists to
remove.

### install22 / 23 / 24 — social reps
New key `forge-reps`. The planner authors the count `n`; the debrief authors the
attribution `att`. Sync merge is max-wins on the count.

### install20 / install21 — weekly review and the park button
Debrief gained a "week behind" card rendering only on review days, sitting directly
above the rocks card so the week is reviewed before next week's rocks are set. It
shows mushin days, project time against the 3h floor, unfinished recurring items,
and the parked list with Rock / Backlog / Drop per item. Rocks cap at three:
promoting a fourth refuses and writes a reason rather than silently dropping one.

Planner gained a PARK IT box under the timers. New key `forge-parked` — a flat
array of `{t, d}`, 100-item cap, case-insensitive de-dupe. Note this is *not* the
`{date: {…}}` shape the other keys use.

### install18 / install19 — the hardening pass
The debrief gained `syncPullDebrief()`, called from `init()` **after** the local
paint so the page is never blank while waiting. Before this it only ever pushed.
`syncPullBrief` was rewritten to pull `forge-week-rocks` as well as `forge-top5`
(rocks were never pulled), to repaint every panel rather than only the five, and to
show sync state in the footer.

Both sides ignore a body containing `error`, so a Worker error object is never
mistaken for data and written as a bogus date key.

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

## Closed since the last revision of this file

- **The Worker allowlist.** Previously listed here as rejecting `forge-mushin` and
  `forge-project`. Resolved — the Worker's key list now contains all eleven keys
  (`forge-top5`, `forge-dayplan`, `forge-backlog`, `forge-fun`, `forge-week-rocks`,
  `forge-frame`, `forge-mushin`, `forge-project`, `forge-parked`, `forge-reps`,
  `forge-video`), and every `K_*` constant in the deployed pages matches it exactly.
- **Debrief loads without pulling.** Fixed by install18.
- **Repo clutter.** Cleared, see the tidy above.

## Known open items

- **Encoding.** The raw Worker view renders curly apostrophes as `â€™`. Believed to be
  a display fault in that view only, since the brief parses with `r.json()`. Unconfirmed
  and low priority.
- **Unsynced keys.** `forge-project`, `forge-parked` and `forge-video` currently read
  as empty in the cloud. This is not a bug — the push wiring for each was audited and
  is correct; those features simply have not been used yet.
- **Travel override active.** See below. Must be reversed on return.

## Travel override

`FORGE_TZ`, `FORGE_LAT`, `FORGE_LON` are repository variables. With all three unset the
brief builds exactly as it did for Richmond. To revert after travel, delete the three
variables under Settings → Secrets and variables → Actions → Variables and re-run the
workflow. No code change is needed.

Three sites are **deliberately** left on `America/Vancouver` and this is correct, not an
oversight: `fetch_ics_events` and `fetch_ics_structured` pull Richmond feeds whose
floating times genuinely are Pacific, and `get_sports_updates` labels schedules with a
literal " PT" suffix that moving the zone would falsify.

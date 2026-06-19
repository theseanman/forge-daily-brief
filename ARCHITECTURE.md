# FORGE Daily Brief — Architecture Reference

**Last updated:** June 18, 2026
**Live at:** theseanman.github.io/forge-daily-brief
**Purpose:** Source of truth for how this system actually works. This repo is PUBLIC, so any AI assistant (or anyone) can fetch and read it directly via `raw.githubusercontent.com/theseanman/forge-daily-brief/main/...` — no need to ask Sean to paste file contents. Read this file first, before assuming anything about state.

---

## How It Runs

```
GitHub Actions cron: 0 14 * * * (14:00 UTC daily)
  │  NOTE: this is 6:00 AM Pacific in winter (PST, UTC-8) but 7:00 AM
  │  Pacific in summer (PDT, UTC-7) — the cron time is fixed in UTC and
  │  does NOT shift with daylight saving. "Runs at 6AM Pacific" is only
  │  true part of the year.
  │
  ├─→ Workflow checks out the gh-pages branch (NOT main)
  ├─→ Runs forge_actions.py FROM gh-pages
  ├─→ Generates index.html
  └─→ Commits index.html + data.json back to gh-pages
```

**Critical structural fact:** `forge_actions.py` is the actual source code. It must exist identically on BOTH `main` (where Sean edits it) AND `gh-pages` (where the workflow actually runs it). If gh-pages has a stale copy, the workflow silently runs old code — this was the root cause of multiple bug reports in the past (see Deploy Rule below).

---

## Deploy Rule (MANDATORY — do not skip steps)

```bash
# 1. Make your edit to forge_actions.py on main, commit, push
git add forge_actions.py
git commit -m "description"
git pull --rebase && git push

# 2. Sync to gh-pages — git pull --rebase is NOT optional here.
#    GitHub Actions commits to gh-pages every morning, so local gh-pages
#    is ALWAYS behind remote. Skipping the pull causes a rejected push.
git checkout gh-pages
git pull --rebase
git checkout main -- forge_actions.py
git commit -m "Sync forge_actions.py to gh-pages"
git push origin gh-pages
git checkout main

# 3. Verify
git log --oneline gh-pages | head -3
# Your new sync commit should be at the top.
```

To see today's fix live immediately instead of waiting for tomorrow's 6/7 AM run: GitHub repo → Actions tab → "FORGE Morning Brief" workflow → Run workflow.

---

## Known Issues — Status as of June 18, 2026

### ✅ Fixed June 18

| Issue | Details |
|---|---|
| Scotland World Cup fixtures were fabricated wrong from day one | `SCOTLAND_WC` array listed Switzerland and South Korea as opponents — neither was ever real. Actual Group C is Brazil, Morocco, Haiti. Corrected to real fixtures (Haiti, Morocco Jun 19, Brazil Jun 24). |
| UFC section threw `'>=' not supported between datetime.date and function` every run | `today_pt` (a function) was being compared directly instead of called as `today_pt()`. Two call sites fixed. |
| MiLB (Vancouver Canadians) ESPN endpoint returned HTTP 400 every run | That specific ESPN endpoint has been broken since at least Jun 11. Removed it, now goes straight to the working MLB infra fallback endpoint. |
| Art and music "daily" picks repeated every ~14 days | Pools only had 14 entries each, cycling by day-of-year. Expanded both to 60 entries — cycles every 2 months instead of 2 weeks. |
| Music pool only surfaced bands Sean already knows | Original intent was discovery, not familiar favorites. Replaced with a 60-entry "FFO: [known band]" discovery list — bands adjacent to his taste but not ones he already listens to. |
| No cache-control on the page, combined with `apple-mobile-web-app-capable=yes` | iOS "Add to Home Screen" web clips can freeze on a stale snapshot for days with no cache headers telling them to refetch. Added `no-cache`/`no-store` meta tags. Real fix also requires deleting and re-adding the home screen icon once. |

### ⚠️ Confirmed NOT a bug (investigated, ruled out)

- **"Quotes repeat" reports**: server-side rotation math was verified correct (day-of-year % pool length) and the live gh-pages page was checked directly and showed the correct day's content. The actual cause was client-side iOS caching, not a server-side rotation bug — see cache fix above.

### 🧹 Known permanent limitations (not bugs, just constraints)

- Brighouse School's calendar blocks GitHub Actions IPs — 8 of 9 subscribed ICS calendars work, this one doesn't and can't be fixed from this side.
- JSONBin free tier blocks GitHub Actions IPs — reminders are fetched via the Cloudflare Worker proxy (`forge-input.yoseanreid.workers.dev`) specifically to work around this.
- Scotland flag emoji causes `UnicodeEncodeError` in the GitHub Actions environment — use `[SCO]` text or HTML entities, never the raw emoji character.
- zsh on Sean's Mac breaks heredocs — all patches must be delivered as standalone `.py` files, never inline shell heredocs.

---

## Confirmed Working (as of June 18, 2026)

FORGE SITREP, Hannibal photo card, weight in lbs, Scotland WC card (now accurate), SBOS card with live EV betting signals (sourced from `trading-system` repo's `betting_intel.py`, 48h filter, 4–25% EV range), Pacific-timezone calendar, 8/9 subscribed ICS calendars, reminders via Cloudflare Worker, rotating wisdom/art/music pools (now 60 entries each), weather, ESPN sports (NFL/NHL/MLB/soccer — MiLB now fixed), Five Paramount Goals, SUNFURY orange/gold aesthetic.

---

## Files / Areas NOT Yet Reviewed Line-by-Line

The FORGE SITREP rule-based briefing logic, the full calendar/ICS integration code, the Cloudflare Worker reminders integration code itself (lives in a separate Worker script, not this repo), the weather module, and the full sports intel beyond what was touched in recent fixes (NFL/NHL/MLB sections specifically).

**If you're an AI assistant reading this in a future session: this repo is public, so fetch `forge_actions.py` directly via `raw.githubusercontent.com/theseanman/forge-daily-brief/main/forge_actions.py` to check current state before assuming anything is broken or already fixed. Update this file after any new investigation or fix.**

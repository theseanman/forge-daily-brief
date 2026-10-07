# CLAUDE.md — forge-daily-brief

This repo serves https://theseanman.github.io/forge-daily-brief/ from the **gh-pages**
branch. Protocol pages sit as siblings (`charisma.html`, `return.html`, …) and
`protocols.html` is the hand-maintained list page that links them. `main` is not the
working branch; everything happens on `gh-pages`.

Read `DEPLOY_STATE.md` as well — it holds installer naming and collision rules, the
parked builds, and the generator's live SHA. It is hand-maintained and dated Aug 14
2026, so treat its status sections as possibly stale and **see "Superseded" at the
bottom of this file before following its section 5.**

---

## Honesty

Label load-bearing claims **verified / reasoning / guess**. Sean's audit phrase is
"verified or vibe?".

Check before asserting:

- About a file → read the file.
- About the state of something → read the live artifact, not your memory of it.
- About why something failed → get the actual error before theorising a cause.
- About a spec or protocol that already exists here → read it first, so a reversal is
  never accidental.
- About a UI you cannot see → ask what it says. Never guess a menu.

Never give a simplified criterion you then correct. Lead with the real standard.

What has held up in this repo is what was tested. What has failed is what was merely
asserted.

## Confirm before generating

Read the spec back and get an explicit go before writing code or files. Do not build
straight off a request, even a clear one.

When an edit touches an existing file, produce the complete updated file, not a
fragment.

---

## Verification — three separate claims

"On the branch", "published" and "working" are three different things. Never let one
stand in for another.

- **On the branch:** `raw.githubusercontent.com/theseanman/forge-daily-brief/gh-pages/<file>`
- **Published:** load the live URL. GitHub Pages has its own build layer, so a 404
  straight after a successful push is that layer, not the branch.
- **Working:** load the live URL in headless Chrome over the DevTools protocol and read
  `getComputedStyle`.

Any page with a tab toggle must be verified on **computed display** — never inline
style, never a DOM stub. In September, `setMode` set `el.style.display = ''`, which does
not override a stylesheet's `display: none`. Every Drill tab on eight pages was blank
for two months, and the test suite passed *because* it asserted the broken state.

The precise rule, since the naive version causes false alarms: clearing an inline
display (`style.display = ''`) is only safe when the element's stylesheet default is
visible. In `return.html`'s `restart()` it is safe, because `.stage` is
`display: flex`. It was unsafe in the September toggle, because the rule there was
`display: none`. Check the stylesheet default before judging either way.

Use a **fresh** cache-buster query string on every deploy. Reusing `?v=2` produced three
separate false "it's not there" reports.

---

## protocols.html

Re-pull it from raw.githubusercontent **immediately** before editing or handing it over
— every time, however recently it was pulled in the same session. It has drifted
mid-session on four separate occasions, and building forward from a stale copy would
have deleted live cards.

Insert a new card by anchoring on the **preceding card's name through its closing
tags**, and assert the match count is exactly 1. A naive anchor matched twice and
dropped a card into the wrong section.

Count cards with the opening fragment only:

    grep -c '<a class="protocol' protocols.html

Leave the closing quote off. Verified Oct 7 2026: the correct pattern reports **31**,
while `'a class="protocol"'` reports **25**, because it excludes the six
`class="protocol gold"` cards. That 6-card gap has already been misread once as a
catastrophe.

A purely additive change shows insertions and **zero deletions** in the diff. That is
the tell that nothing was lost.

---

## Deploys

New page files stay untracked and silently never land. After writing one, run
`GIT_OPTIONAL_LOCKS=0 git status --short` and `git add` by explicit filename — never
`git add .`. Two pages returned 401 for a day because only the already-tracked
`protocols.html` went up.

`git pull --rebase` hangs on Sean's district Mac even with `GIT_OPTIONAL_LOCKS=0`. Use
the split form:

    GIT_OPTIONAL_LOCKS=0 git -c fetch.unpackLimit=1 fetch origin gh-pages
    git rebase origin/gh-pages
    git push origin HEAD:gh-pages

`index.html` is generated output. Never hand-edit it. Edit `forge_actions.py`, sync to
gh-pages, then trigger the workflow. A generator change is live only after both the push
**and** the workflow run.

---

## Protocol pages

Every protocol page carries a device-only photo slot at the top: key
`forge-img-<name>`, tap to add, long-press to remove. On-device only — never synced,
never committed.

Before building a new page, pull and read the live pages it might overlap, and scope
against them explicitly rather than restating what they already own.

Evidence grades are [A]–[D], checked against primary sources at build time rather than
recalled. Grade honestly and mark weak claims weak.

---

## Superseded

`DEPLOY_STATE.md` section 5 ("THE DEPLOY ROUTE THAT WORKS") describes a
browser-upload route followed by `git pull --rebase`. That is **no longer the route**:

- `git pull --rebase` hangs on this Mac — use the split fetch/rebase/push above.
- Direct `git push` from the local clone has been proven repeatedly since Sep 6 2026.
- The browser-upload route also depends on `~/Downloads`, which is a decoy field:
  Safari parks numbered copies (`protocols-8.html` and similar) while the plain
  `protocols.html` there is an Aug 31 relic. Copying by plain name once pulled in a
  stale file that would have deleted six cards.

Its installer-naming rules (section 2), used-number list (section 3) and parked work
(section 4) are still current and worth reading.

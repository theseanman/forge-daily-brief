#!/usr/bin/env python3
"""
forge_checklist_card_20260906.py

Adds a read-only Daily Checklist card to step 06 (Protocol review) of the
evening debrief, plus a link that opens checklist.html in a NEW TAB.

  Edits    : forge-evening-debrief.html  (hand-maintained, live on push, NO workflow)
  Writes   : nothing else
  New key  : forge-checklist  -- READ ONLY here. The debrief never writes a tick.
             Already in the forge-sync Worker allowlist (confirmed Sep 6).

WHY A NEW TAB: the debrief persists nothing until finishDebrief(). next() only
swaps the visible step. A same-tab link out of this page would silently discard
everything entered so far. target="_blank" keeps the debrief tab and its JS
state alive.

CL_TOTAL is the ONE duplicated fact -- the checklist item count. It is a single
named constant, deliberately not a copy of the 23-row item/tier table, so the
score stays computed in checklist.html only. Bump CL_TOTAL if items are added
or removed there.

Merge semantics: union of ticks. A stale cloud copy can never un-tick anything,
matching checklist.html's own pull branch.

Fails closed: any anchor problem leaves the file byte-identical.
"""

import hashlib
import os
import shutil
import sys

TARGET = "forge-evening-debrief.html"
PRE_SHA = "9ec4f782a2b527b114f0abb2d932e18c102490a5f8a5324e03a710d717b0c90d"

# ---- A1: key declaration -------------------------------------------------
A1_OLD = "var K_PROTO='forge-protocol-counts'; /* debrief_protocol_review_aug14 */"
A1_NEW = ("var K_PROTO='forge-protocol-counts'; /* debrief_protocol_review_aug14 */\n"
          "var K_CHECKLIST='forge-checklist'; /* checklist_card_20260906, read-only here */")

# ---- A2: pull list -------------------------------------------------------
A2_OLD = ("var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, K_PARKED, "
          "K_PROJ, K_REPS, K_VIDEO, K_PROTO, K_DAILY, K_STRESS, K_BLOG, K_JOTS]; "
          "/* install25 + tally_pull_key_aug14 + dailylog_backup + stressinoc + breathelog + jots */")
A2_NEW = ("var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, K_PARKED, "
          "K_PROJ, K_REPS, K_VIDEO, K_PROTO, K_DAILY, K_STRESS, K_BLOG, K_JOTS, K_CHECKLIST]; "
          "/* install25 + tally_pull_key_aug14 + dailylog_backup + stressinoc + breathelog + jots "
          "+ checklist_card_20260906 */")

# ---- A3: union merge branch ---------------------------------------------
A3_OLD = "  if (key === K_VIDEO) {                       /* install25: done is sticky, never un-ticked */"
A3_NEW = """  if (key === K_CHECKLIST) {                   /* checklist_card_20260906: union of ticks, never un-ticks */
    if (!cloudVal || typeof cloudVal !== 'object' || Array.isArray(cloudVal)) return false;
    var lDay = (localVal && typeof localVal === 'object' && !Array.isArray(localVal)) ? localVal : null;
    var merged = {}, ck, added = false;
    if (lDay) { for (ck in lDay) { if (lDay.hasOwnProperty(ck) && lDay[ck] === true) merged[ck] = true; } }
    for (ck in cloudVal) {
      if (!cloudVal.hasOwnProperty(ck)) continue;
      if (cloudVal[ck] === true && merged[ck] !== true) { merged[ck] = true; added = true; }
    }
    if (!added) return false;
    local[dk] = merged;
    return true;
  }

  if (key === K_VIDEO) {                       /* install25: done is sticky, never un-ticked */"""

# ---- A4: the card markup, above step-6's button row ---------------------
A4_OLD = """      <div class="btn-row">
        <button class="btn" onclick="prev()"><i class="ti ti-arrow-left"></i></button>
        <button class="btn primary" onclick="next()">Tomorrow&rsquo;s five <i class="ti ti-arrow-right"></i></button>
      </div>"""
A4_NEW = """      <!-- checklist_card_20260906 -->
      <div class="proto-sec" style="background:linear-gradient(135deg,rgba(26,95,168,.22),rgba(18,58,108,.10)); border:1px solid #4a9de8; margin-bottom:14px;">
        <div class="proto-head" style="color:#4a9de8;">DAILY CHECKLIST</div>
        <div class="proto-sub" style="color:#4a9de8;">Today&rsquo;s tick count, read straight from the checklist.</div>
        <div style="padding:2px 12px 12px;">
          <div id="cl-count" style="font-size:20px; font-weight:700; color:#f0f0f8; margin-bottom:8px;">&mdash;</div>
          <div style="height:6px; border-radius:99px; background:rgba(74,157,232,.18); overflow:hidden; margin-bottom:10px;">
            <div id="cl-bar" style="height:100%; width:0%; border-radius:99px; background:linear-gradient(90deg,#4a9de8,#7fc4ff);"></div>
          </div>
          <div id="cl-sub" style="font-size:12px; color:#8a9ad0; line-height:1.5; margin-bottom:12px;"></div>
          <a href="./checklist.html" target="_blank" rel="noopener" style="display:inline-block; text-decoration:none; font-size:13px; font-weight:600; color:#0d1b2e; background:#4a9de8; border-radius:8px; padding:9px 16px;">Open the checklist &nearr;</a>
        </div>
      </div>

      <div class="btn-row">
        <button class="btn" onclick="prev()"><i class="ti ti-arrow-left"></i></button>
        <button class="btn primary" onclick="next()">Tomorrow&rsquo;s five <i class="ti ti-arrow-right"></i></button>
      </div>"""

# ---- A5: render function ------------------------------------------------
A5_OLD = "function fdToday(){ return fdYmd(fdNow()); }"
A5_NEW = """function fdToday(){ return fdYmd(fdNow()); }

/* ---- checklist_card_20260906 ----
   READ ONLY. checklist.html owns the ticks and owns the score. CL_TOTAL is the
   only fact copied out of that page -- bump it if the item list changes. */
var CL_TOTAL = 23;
function renderChecklistCard(){
  var el = document.getElementById('cl-count');
  if (!el) return;
  var sub = document.getElementById('cl-sub');
  var bar = document.getElementById('cl-bar');
  var all = fdRead(K_CHECKLIST, {});
  if (!all || typeof all !== 'object' || Array.isArray(all)) all = {};
  var day = all[fdToday()];
  var opened = !!(day && typeof day === 'object' && !Array.isArray(day));
  var n = 0;
  if (opened) { for (var k in day) { if (day.hasOwnProperty(k) && day[k] === true) n++; } }
  if (!opened) {
    el.textContent = 'Not opened today';
    if (sub) sub.textContent = 'Opens in a new tab, so nothing you have entered here is lost.';
  } else {
    el.textContent = n + ' of ' + CL_TOTAL + ' ticked today';
    if (sub) sub.textContent = (n >= CL_TOTAL)
      ? 'Full sweep. Opens in a new tab \\u2014 this debrief keeps its place.'
      : 'Opens in a new tab, so nothing you have entered here is lost.';
  }
  var pct = CL_TOTAL > 0 ? Math.round(100 * n / CL_TOTAL) : 0;
  if (pct > 100) pct = 100;
  if (pct < 0) pct = 0;
  if (bar) bar.style.width = pct + '%';
}"""

# ---- A6: paint on entering step 6 ---------------------------------------
A6_OLD = "  if (n === 6) protoLoad();"
A6_NEW = "  if (n === 6) { protoLoad(); try { renderChecklistCard(); } catch (e) {} }"

# ---- A7: repaint after a successful pull --------------------------------
A7_OLD = ("    if (touched) { try { loadTodayTop5(); } catch (e) {} try { renderWeeklyReview(); } "
          "catch (e) {} try { protoLoad(); } catch (e) {} }")
A7_NEW = ("    if (touched) { try { loadTodayTop5(); } catch (e) {} try { renderWeeklyReview(); } "
          "catch (e) {} try { protoLoad(); } catch (e) {} try { renderChecklistCard(); } catch (e) {} }")

EDITS = [
    ("K_CHECKLIST declaration", A1_OLD, A1_NEW),
    ("PULL_KEYS", A2_OLD, A2_NEW),
    ("fdMergeEntry union branch", A3_OLD, A3_NEW),
    ("step-6 card markup", A4_OLD, A4_NEW),
    ("renderChecklistCard function", A5_OLD, A5_NEW),
    ("showStep paint call", A6_OLD, A6_NEW),
    ("post-pull repaint", A7_OLD, A7_NEW),
]


def die(msg):
    print("ABORT: " + msg)
    print("Nothing was written.")
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die(TARGET + " not found. Run this from inside the repo, on gh-pages.")

    with open(TARGET, encoding="utf-8") as fh:
        src = fh.read()

    pre = hashlib.sha256(src.encode("utf-8")).hexdigest()
    if pre != PRE_SHA:
        die("pre-image mismatch.\n  expected " + PRE_SHA + "\n  found    " + pre +
            "\nThe file has changed since this installer was built.")

    out = src
    for name, old, new in EDITS:
        count = out.count(old)
        if count != 1:
            die("anchor '" + name + "' matched " + str(count) + " times, expected exactly 1.")
        out = out.replace(old, new, 1)
        print("  ok  " + name)

    if "forge-checklist" not in out or "renderChecklistCard" not in out:
        die("post-check failed: expected strings missing.")

    backup = TARGET + ".checklistcard.bak"
    shutil.copy2(TARGET, backup)
    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(out)

    post = hashlib.sha256(out.encode("utf-8")).hexdigest()
    print("\nWrote " + TARGET)
    print("  pre  " + pre)
    print("  post " + post)
    print("  backup: " + backup)


if __name__ == "__main__":
    main()

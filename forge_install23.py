#!/usr/bin/env python3
"""
install23 - social reps in forge-evening-debrief.html

Two additions to step-5 (Wins & misses, a TODAY record - deliberately NOT the
frame card, which is forward-dated and rebuilds its entry on save):
  1. today's rep count, pulled from the planner tally, correctable here
  2. one unscored attention question - where did attention sit

Shares forge-reps {date:{n,att}} with install22. The debrief authors `att`;
the planner authors `n`. Neither destroys the other's field.

Reps are NOT wired into enoughVerdict(). This is practice, not a test.
Fails closed: any anchor problem leaves the file byte-identical.
"""
import hashlib
import os
import shutil
import sys

TARGET = "forge-evening-debrief.html"
PRE_SHA = "407ec4a8855b1cf654f998c0ea186031b944723ab7318eb91ce67f08c024788f"

A1_OLD = "var K_FRAME='forge-frame', K_MUSHIN='forge-mushin'; /* install13 */"
A1_NEW = (
    "var K_FRAME='forge-frame', K_MUSHIN='forge-mushin'; /* install13 */\n"
    "var K_REPS='forge-reps'; /* install23 */"
)

A2_OLD = (
    "var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, "
    "K_PARKED, K_PROJ]; /* install20 */"
)
A2_NEW = (
    "var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, "
    "K_PARKED, K_PROJ, K_REPS]; /* install23 */"
)

A3_OLD = "  if (fdBlank(cloudVal) && !fdBlank(localVal)) return false;   /* the guard */"
A3_NEW = """  if (key === K_REPS) {                        /* install23: n only goes up, att is preserved */
    var ln = (localVal && typeof localVal.n === 'number') ? localVal.n : -1;
    var cn = (cloudVal && typeof cloudVal.n === 'number') ? cloudVal.n : -1;
    var lAtt = (localVal && typeof localVal.att === 'string') ? localVal.att : '';
    var cAtt = (cloudVal && typeof cloudVal.att === 'string') ? cloudVal.att : '';
    var wantN = cn > ln ? cn : (ln > 0 ? ln : 0);
    var wantAtt = lAtt || cAtt;               /* a local answer typed tonight wins */
    if (wantN === (ln > 0 ? ln : 0) && wantAtt === lAtt) return false;
    local[dk] = { n: wantN, att: wantAtt };
    return true;
  }

  if (fdBlank(cloudVal) && !fdBlank(localVal)) return false;   /* the guard */"""

A4_OLD = """      <div class="field"><div class="field-label">One thing to carry into tomorrow</div><textarea id="carry" placeholder="e.g. do the hard thing first..." style="min-height:60px;"></textarea></div>
      <div class="btn-row">"""
A4_NEW = """      <div class="field"><div class="field-label">One thing to carry into tomorrow</div><textarea id="carry" placeholder="e.g. do the hard thing first..." style="min-height:60px;"></textarea></div>

      <!-- install23 -->
      <div class="rocks-card show" id="reps-card" style="margin-top:6px;">
        <div style="font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:#4a9de8; margin-bottom:6px;">Reps</div>

        <div class="field-label" style="margin:0 0 4px;">Conversations you started today</div>
        <div class="note-line" style="margin:0 0 8px;">With someone you didn&rsquo;t have to talk to. Counted on the planner &mdash; fix it here if it drifted. Nothing passes or fails.</div>
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
          <button class="pick" onclick="repsNudge(-1)" style="padding:8px 14px; font-size:15px; font-weight:700;">&minus;</button>
          <span id="reps-n" style="font-size:22px; font-weight:800; min-width:32px; text-align:center;">0</span>
          <button class="pick" onclick="repsNudge(1)" style="padding:8px 14px; font-size:15px; font-weight:700;">+</button>
        </div>

        <div class="field-label" style="margin:0 0 4px;">Where did your attention sit?</div>
        <div class="note-line" style="margin:0 0 6px;">On them, or on how you were coming across. No right answer &mdash; the noticing is the whole exercise.</div>
        <div class="pick-wrap" id="reps-att-picks"></div>
      </div>

      <div class="btn-row">"""

A5_OLD = "function initFrame(){"
A5_NEW = """/* ---------- install23: social reps ---------- */
var repsState = { n: 0, att: '' };
var REPS_ATT = [['them','on them'],['split','split'],['me','on me']];

function repsToday(){
  var all = fdRead(K_REPS, {});
  if (!all || typeof all !== 'object' || Array.isArray(all)) return { n: 0, att: '' };
  var e = all[fdToday()];
  if (!e || typeof e !== 'object' || Array.isArray(e)) return { n: 0, att: '' };
  return {
    n: (typeof e.n === 'number' && e.n > 0) ? Math.floor(e.n) : 0,
    att: (typeof e.att === 'string') ? e.att : ''
  };
}
function initReps(){
  repsState = repsToday();
  paintReps();
}
function paintReps(){
  var el = document.getElementById('reps-n');
  if (el) el.textContent = repsState.n;
  var host = document.getElementById('reps-att-picks');
  if (!host) return;
  host.innerHTML = '';
  REPS_ATT.forEach(function(pair){
    var b = document.createElement('button');
    b.className = 'pick' + (repsState.att === pair[0] ? ' fam' : '');
    b.textContent = pair[1];
    b.onclick = function(){
      repsState.att = (repsState.att === pair[0]) ? '' : pair[0];
      paintReps();
    };
    host.appendChild(b);
  });
}
function repsNudge(d){
  repsState.n += d;
  if (repsState.n < 0) repsState.n = 0;
  paintReps();
}
function saveReps(){
  var all = fdRead(K_REPS, {});
  if (!all || typeof all !== 'object' || Array.isArray(all)) all = {};
  all[fdToday()] = { n: repsState.n, att: repsState.att };
  var keys = Object.keys(all).sort();
  if (keys.length > 60){ var o = {}; keys.slice(-60).forEach(function(k){ o[k] = all[k]; }); all = o; }
  fdWrite(K_REPS, all);
  syncPush(K_REPS);
}

function initFrame(){"""

A6_OLD = "  renderPlanRows(); renderPicks(); maybeShowRocks(); initFrame(); /* install13 */"
A6_NEW = ("  renderPlanRows(); renderPicks(); maybeShowRocks(); initFrame(); /* install13 */\n"
          "  try { initReps(); } catch(e) {} /* install23 */")

A7_OLD = "  saveFrame(); /* install13 */"
A7_NEW = ("  saveFrame(); /* install13 */\n"
          "  try { saveReps(); } catch(e) {} /* install23 */")

EDITS = [
    ("K_REPS declaration", A1_OLD, A1_NEW),
    ("PULL_KEYS", A2_OLD, A2_NEW),
    ("fdMergeEntry branch", A3_OLD, A3_NEW),
    ("step-5 reps card", A4_OLD, A4_NEW),
    ("reps functions", A5_OLD, A5_NEW),
    ("initReps call", A6_OLD, A6_NEW),
    ("saveReps call", A7_OLD, A7_NEW),
]

MARKERS = ["install23", "K_REPS", "repsNudge", "reps-att-picks", "saveReps"]


def main():
    if not os.path.exists(TARGET):
        sys.exit("FAIL: %s not found. Run this from the repo root." % TARGET)

    original = open(TARGET, "r", encoding="utf-8").read()
    sha = hashlib.sha256(original.encode("utf-8")).hexdigest()

    if "install23" in original:
        print("Already applied (install23 marker present). Nothing written.")
        return

    if sha != PRE_SHA:
        sys.exit(
            "FAIL: pre-image mismatch.\n  expected %s\n  found    %s\n"
            "File not modified. Do not force this." % (PRE_SHA, sha)
        )

    text = original
    for name, old, new in EDITS:
        count = text.count(old)
        if count != 1:
            sys.exit("FAIL: anchor '%s' matched %d times, need exactly 1. "
                     "File not modified." % (name, count))
        text = text.replace(old, new, 1)
        print("  ok  %s" % name)

    for m in MARKERS:
        if m not in text:
            sys.exit("FAIL: marker '%s' missing after edit. File not modified." % m)

    body = text.split("function enoughVerdict")[1].split("\n}")[0]
    if "K_REPS" in body or "reps" in body:
        sys.exit("FAIL: reps leaked into enoughVerdict(). File not modified.")

    shutil.copy2(TARGET, TARGET + ".install23.bak")
    open(TARGET, "w", encoding="utf-8").write(text)

    post = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print("\nWrote %s" % TARGET)
    print("  pre  %s" % sha)
    print("  post %s" % post)
    print("  backup: %s.install23.bak" % TARGET)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
install22 - social rep counter on planner.html

Adds a third PRACTICE row: a tap-to-increment count of conversations
initiated with someone Sean did not have to talk to.

NEW KEY: forge-reps  {date: {n, att}}
  n   - integer count, written by the planner
  att - one-line attention answer, written by the DEBRIEF only.
        The planner must preserve it and never write it.

Fails closed: any anchor problem leaves the file byte-identical.
"""
import hashlib
import os
import shutil
import sys

TARGET = "planner.html"
PRE_SHA = "13bdc773fe8c4d0b8744dec0e47a3a2ab2f2889e3cf09767ff60678b65235d86"

# ---------------------------------------------------------------- edits

A1_OLD = "var K_PARKED = 'forge-parked'; /* install21 */"
A1_NEW = (
    "var K_PARKED = 'forge-parked'; /* install21 */\n"
    "var K_REPS = 'forge-reps'; /* install22 */"
)

A2_OLD = (
    "var SYNC_KEYS = [K_TOP5, K_PLAN, K_BACKLOG, K_FUN, 'forge-week-rocks', "
    "K_MUSHIN, K_PROJ, K_PARKED]; /* install21 */"
)
A2_NEW = (
    "var SYNC_KEYS = [K_TOP5, K_PLAN, K_BACKLOG, K_FUN, 'forge-week-rocks', "
    "K_MUSHIN, K_PROJ, K_PARKED, K_REPS]; /* install22 */"
)

# max-wins merge for the counter, inserted ahead of the generic cloud-wins tail
A3_OLD = """                continue;
              }
              if (JSON.stringify(local[dk]) !== JSON.stringify(cloud[dk])) {
                local[dk] = cloud[dk]; changed = true;
              }"""
A3_NEW = """                continue;
              }
              if (key === K_REPS) { /* install22: counts only ever go up; att is the debrief's */
                var lr = local[dk], cr = cloud[dk];
                var ln = (lr && typeof lr.n === 'number') ? lr.n : -1;
                var cn = (cr && typeof cr.n === 'number') ? cr.n : -1;
                var lAtt = (lr && typeof lr.att === 'string') ? lr.att : '';
                var cAtt = (cr && typeof cr.att === 'string') ? cr.att : '';
                var wantN = cn > ln ? cn : (ln > 0 ? ln : 0);
                var wantAtt = cAtt || lAtt;
                if (wantN !== (ln > 0 ? ln : 0) || wantAtt !== lAtt) {
                  local[dk] = { n: wantN, att: wantAtt };
                  changed = true;
                }
                continue;
              }
              if (JSON.stringify(local[dk]) !== JSON.stringify(cloud[dk])) {
                local[dk] = cloud[dk]; changed = true;
              }"""

# helpers + render, appended ahead of practiceTick
A4_OLD = """function practiceTick(){"""
A4_NEW = """/* ---------- install22: social reps ---------- */
var REPS_KEEP = 60;
function repsAll(){
  var o = readJSON(K_REPS, {});
  return (o && typeof o === 'object' && !Array.isArray(o)) ? o : {};
}
function repsEntry(dk){
  var e = repsAll()[dk];
  if (!e || typeof e !== 'object' || Array.isArray(e)) return { n: 0, att: '' };
  return {
    n: (typeof e.n === 'number' && e.n > 0) ? Math.floor(e.n) : 0,
    att: (typeof e.att === 'string') ? e.att : ''
  };
}
function repsBump(delta){
  var dk = pDayKey(), all = repsAll(), cur = repsEntry(dk);
  var n = cur.n + delta;
  if (n < 0) n = 0;
  all[dk] = { n: n, att: cur.att };   /* att preserved, never authored here */
  var ks = Object.keys(all).sort();
  if (ks.length > REPS_KEEP){
    var trimmed = {};
    ks.slice(-REPS_KEEP).forEach(function(x){ trimmed[x] = all[x]; });
    all = trimmed;
  }
  writeJSON(K_REPS, all);
  syncPush(K_REPS);
  paintReps();
}
function paintReps(){
  var el = document.getElementById('p-reps-n');
  if (el) el.textContent = repsEntry(pDayKey()).n;
}

function practiceTick(){"""

# third row in the practice card
A5_OLD = """          'pToggle(K_PROJ)') +
    '</div>';"""
A5_NEW = """          'pToggle(K_PROJ)') +
      /* install22: reps. No target, no tick - it cannot be failed. */
      '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;' +
        'border-top:1px solid rgba(255,201,7,0.25);">' +
        '<div style="flex:1;min-width:0;">' +
          '<div style="font-size:10px;letter-spacing:0.16em;opacity:0.75;">\\u25B3 REPS</div>' +
          '<div style="font-size:19px;font-weight:800;line-height:1.25;">' +
            '<span id="p-reps-n">' + repsEntry(pDayKey()).n + '</span>' +
          '</div>' +
          '<div style="font-size:10px;opacity:0.7;margin-top:2px;">' +
            'conversations you started with someone you didn\\u2019t have to' +
          '</div>' +
        '</div>' +
        '<button onclick="repsBump(-1)" style="border:none;border-radius:8px;padding:9px 12px;' +
          'font-weight:800;font-size:12px;cursor:pointer;touch-action:manipulation;' +
          'background:rgba(255,201,7,0.25);color:#ffc107;">\\u2212</button>' +
        '<button onclick="repsBump(1)" style="border:none;border-radius:8px;padding:9px 14px;' +
          'font-weight:800;font-size:12px;cursor:pointer;touch-action:manipulation;' +
          'background:#ffc107;color:#0d0d0d;">+1</button>' +
      '</div>' +
    '</div>';"""

EDITS = [
    ("K_REPS declaration", A1_OLD, A1_NEW),
    ("SYNC_KEYS", A2_OLD, A2_NEW),
    ("syncPull max-wins branch", A3_OLD, A3_NEW),
    ("reps helpers", A4_OLD, A4_NEW),
    ("practice card row", A5_OLD, A5_NEW),
]

MARKERS = ["install22", "K_REPS", "repsBump", "p-reps-n"]


def main():
    if not os.path.exists(TARGET):
        sys.exit("FAIL: %s not found. Run this from the repo root." % TARGET)

    original = open(TARGET, "r", encoding="utf-8").read()
    sha = hashlib.sha256(original.encode("utf-8")).hexdigest()

    if "install22" in original:
        print("Already applied (install22 marker present). Nothing written.")
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

    shutil.copy2(TARGET, TARGET + ".install22.bak")
    open(TARGET, "w", encoding="utf-8").write(text)

    post = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print("\nWrote %s" % TARGET)
    print("  pre  %s" % sha)
    print("  post %s" % post)
    print("  backup: %s.install22.bak" % TARGET)


if __name__ == "__main__":
    main()

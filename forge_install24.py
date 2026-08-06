#!/usr/bin/env python3
"""
install24 - reps line on the brief's practice card (forge_actions.py)

Read-only display. The brief never writes forge-reps.
Deliberately no tick box: a practice that cannot be failed must not render
a checkbox next to the two things that can be.

NOTE: forge_actions.py holds the whole brief in a Python f-string, so every
literal brace in injected JS is DOUBLED. This installer's payload is already
doubled - do not "fix" it.

This is a GENERATOR patch. It needs a workflow run to reach index.html.
Fails closed: any anchor problem leaves the file byte-identical.
"""
import ast
import hashlib
import os
import shutil
import sys

TARGET = "forge_actions.py"
PRE_SHA = "b097a31593d8b7884e274ccb532110b0805bf1ed770fe6c59a26d25a710034f7"

# --- reps reader, placed beside the other pf helpers -------------------
A1_OLD = """function pfStreak() {{"""
A1_NEW = """function pfReps() {{
  var all = pfAll('forge-reps');
  var e = all[ymdOffset(0)];
  if (!e || typeof e !== 'object' || Array.isArray(e)) return 0;
  return (typeof e.n === 'number' && e.n > 0) ? Math.floor(e.n) : 0;
}}
function pfStreak() {{"""

# --- third row in the practice card ------------------------------------
A2_OLD = """        '<div class="t5-meta">' + pfClock(p.sec, true) + ' of 3h 00m this week &middot; ' + sub + '</div>' +
      '</div>' +
    '</div>';
}}"""
A2_NEW = """        '<div class="t5-meta">' + pfClock(p.sec, true) + ' of 3h 00m this week &middot; ' + sub + '</div>' +
      '</div>' +
    '</div>' +
    '<div class="t5-row">' +
      '<span class="t5-tick">&#9653;</span>' +
      '<div style="flex:1; min-width:0;">' +
        '<div class="t5-task">Reps</div>' +
        '<div class="t5-meta">' + pfReps() + ' today &middot; conversations you started</div>' +
      '</div>' +
    '</div>';
}}"""

# --- pull forge-reps, max-wins on n ------------------------------------
A3_OLD = """window.addEventListener('load', function () {{
  try {{ paintTodayFive(); }} catch (e) {{}}"""
A3_NEW = """/* Counts never go backwards on a pull. `att` is the debrief's field - the
   brief must carry it through untouched rather than dropping it. */
function pullReps() {{
  fetch(SYNC_URL + '/' + encodeURIComponent('forge-reps'))
    .then(function (r) {{ if (!r.ok) throw new Error(r.status); return r.json(); }})
    .then(function (cloud) {{
      if (!cloud || typeof cloud !== 'object' || Array.isArray(cloud)) return;
      var all = pfAll('forge-reps');
      var changed = false;
      for (var dk in cloud) {{
        if (!cloud.hasOwnProperty(dk)) continue;
        var lc = all[dk], cc = cloud[dk];
        if (!cc || typeof cc !== 'object' || Array.isArray(cc)) continue;
        var ln = (lc && typeof lc.n === 'number') ? lc.n : -1;
        var cn = (typeof cc.n === 'number') ? cc.n : -1;
        var lAtt = (lc && typeof lc.att === 'string') ? lc.att : '';
        var cAtt = (typeof cc.att === 'string') ? cc.att : '';
        var wantN = cn > ln ? cn : (ln > 0 ? ln : 0);
        var wantAtt = lAtt || cAtt;
        if (wantN !== (ln > 0 ? ln : 0) || wantAtt !== lAtt) {{
          all[dk] = {{ n: wantN, att: wantAtt }};
          changed = true;
        }}
      }}
      if (changed) {{
        try {{ localStorage.setItem('forge-reps', JSON.stringify(all)); }} catch (e) {{}}
        try {{ paintPractice(); }} catch (e) {{}}
      }}
    }})
    .catch(function () {{}});
}}

window.addEventListener('load', function () {{
  try {{ paintTodayFive(); }} catch (e) {{}}"""

A4_OLD = "  try {{ pullPractice(); }} catch (e) {{}}"
A4_NEW = ("  try {{ pullPractice(); }} catch (e) {{}}\n"
          "  try {{ pullReps(); }} catch (e) {{}}")

EDITS = [
    ("pfReps helper", A1_OLD, A1_NEW),
    ("practice card reps row", A2_OLD, A2_NEW),
    ("pullReps function", A3_OLD, A3_NEW),
    ("pullReps call", A4_OLD, A4_NEW),
]

MARKERS = ["pfReps", "pullReps", "conversations you started"]


def main():
    if not os.path.exists(TARGET):
        sys.exit("FAIL: %s not found. Run this from the repo root." % TARGET)

    original = open(TARGET, "r", encoding="utf-8").read()
    sha = hashlib.sha256(original.encode("utf-8")).hexdigest()

    if "pfReps" in original:
        print("Already applied (pfReps marker present). Nothing written.")
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

    try:
        ast.parse(text)
    except SyntaxError as e:
        sys.exit("FAIL: ast.parse rejected the result at line %s: %s\n"
                 "File not modified." % (e.lineno, e.msg))

    shutil.copy2(TARGET, TARGET + ".install24.bak")
    open(TARGET, "w", encoding="utf-8").write(text)

    post = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print("\nWrote %s" % TARGET)
    print("  pre  %s" % sha)
    print("  post %s" % post)
    print("  backup: %s.install24.bak" % TARGET)
    print("\nast.parse passing does NOT prove the emitted JS is valid.")
    print("This is a GENERATOR patch - it needs a workflow run.")


if __name__ == "__main__":
    main()

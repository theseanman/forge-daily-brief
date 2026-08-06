#!/usr/bin/env python3
"""
install28 - planner.html: the five never reached the Worker

TWO DEFECTS, one root cause.

  syncPush(K_TOP5) sat BELOW saveTop5's closing brace, and syncPush(K_PLAN)
  below savePlan's. Both were stray top-level statements: they fired once at
  page load and never on save. Saving the five wrote to localStorage and
  stopped there, which is why forge-top5 had no cloud entry after 2026-08-03.

  This is install11's bug reintroduced on a different page. install11 fixed
  exactly this shape in forge-evening-debrief.html.

ALSO ADDED: the emptiness guard the planner never got. The debrief got it in
install18 and the brief in install19. A cloud entry that is blank can no
longer overwrite a populated local one.

  DELIBERATE TRADE-OFF: deliberately CLEARING the five on one surface will not
  propagate to the other - it has to be cleared in both. Principle:
  stale-but-present beats silently wiped. Sean accepted this Aug 6 2026.

Planner is hand-maintained. Push is enough - NO WORKFLOW RUN.

Fails closed: any anchor problem leaves the file byte-identical.
"""
import hashlib
import os
import shutil
import sys
from datetime import datetime

TARGET = "planner.html"
PRE_SHA = "c4ad3b8d5432c1040cd5987bbc0454394af066ad1f06a6e684c99f84e9f61c36"

# ------------------------------------------------------------------ edit 1
A1_OLD = """function saveTop5(arr){
  var all = readJSON(K_TOP5, {});
  all[dayKey()] = arr;
  var ok = writeJSON(K_TOP5, prune(all));
  afterSave(ok);
}
  syncPush(K_TOP5);"""

A1_NEW = """function saveTop5(arr){
  var all = readJSON(K_TOP5, {});
  all[dayKey()] = arr;
  var ok = writeJSON(K_TOP5, prune(all));
  afterSave(ok);
  syncPush(K_TOP5); /* install28: was a stray top-level call below this brace */
}"""

# ------------------------------------------------------------------ edit 2
A2_OLD = """function savePlan(plan){
  var all = readJSON(K_PLAN, {});
  all[dayKey()] = plan;
  var ok = writeJSON(K_PLAN, prune(all));
  afterSave(ok);
}
  syncPush(K_PLAN);"""

A2_NEW = """function savePlan(plan){
  var all = readJSON(K_PLAN, {});
  all[dayKey()] = plan;
  var ok = writeJSON(K_PLAN, prune(all));
  afterSave(ok);
  syncPush(K_PLAN); /* install28: was a stray top-level call below this brace */
}"""

# ------------------------------------------------------------------ edit 3
A3_OLD = "function syncPull(cb) {"

A3_NEW = """/* install28: emptiness guard, matching install18 (debrief) and install19 (brief).
   A blank cloud entry never overwrites a populated local one. `done` and `run`
   are flags, not content, so {done:true} alone counts as blank. */
function plBlank(v) {
  if (v === null || v === undefined) return true;
  if (typeof v === 'number') return !(v > 0);
  if (typeof v === 'string') return v.trim() === '';
  if (Object.prototype.toString.call(v) === '[object Array]') {
    for (var i = 0; i < v.length; i++) if (!plBlank(v[i])) return false;
    return true;
  }
  if (typeof v === 'object') {
    for (var k in v) {
      if (!v.hasOwnProperty(k)) continue;
      if (k === 'done' || k === 'run') continue;
      if (!plBlank(v[k])) return false;
    }
    return true;
  }
  return false;
}

function syncPull(cb) {"""

# ------------------------------------------------------------------ edit 4
A4_OLD = """              if (JSON.stringify(local[dk]) !== JSON.stringify(cloud[dk])) {
                local[dk] = cloud[dk]; changed = true;
              }"""

A4_NEW = """              if (plBlank(cloud[dk]) && !plBlank(local[dk])) continue; /* install28 */
              if (JSON.stringify(local[dk]) !== JSON.stringify(cloud[dk])) {
                local[dk] = cloud[dk]; changed = true;
              }"""

EDITS = [
    ("move syncPush(K_TOP5) inside saveTop5", A1_OLD, A1_NEW),
    ("move syncPush(K_PLAN) inside savePlan", A2_OLD, A2_NEW),
    ("add plBlank() helper", A3_OLD, A3_NEW),
    ("guard the date-key overwrite", A4_OLD, A4_NEW),
]


def die(msg):
    print("ABORT: " + msg)
    print("File left byte-identical. Nothing changed.")
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die(TARGET + " not found. cd into the gh-pages clone first.")

    original = open(TARGET, "r", encoding="utf-8").read()
    sha_before = hashlib.sha256(original.encode("utf-8")).hexdigest()
    print("pre-image sha256: " + sha_before)

    if sha_before != PRE_SHA:
        print("expected:         " + PRE_SHA)
        die("pre-image does not match. The deployed planner is not the version "
            "this installer was built against. Do not force it.")

    # every anchor must appear exactly once BEFORE anything is written
    for label, old, _new in EDITS:
        n = original.count(old)
        if n != 1:
            die("anchor for '%s' found %d times, expected exactly 1." % (label, n))
    print("all 4 anchors unique: OK")

    patched = original
    for label, old, new in EDITS:
        patched = patched.replace(old, new, 1)
        print("  applied: " + label)

    # ---- post-conditions ----
    checks = [
        ("no stray syncPush(K_TOP5) below a brace",
         "}\n  syncPush(K_TOP5);" not in patched),
        ("no stray syncPush(K_PLAN) below a brace",
         "}\n  syncPush(K_PLAN);" not in patched),
        ("saveTop5 now pushes internally",
         "  syncPush(K_TOP5); /* install28" in patched),
        ("savePlan now pushes internally",
         "  syncPush(K_PLAN); /* install28" in patched),
        ("plBlank defined exactly once",
         patched.count("function plBlank(v) {") == 1),
        ("guard wired into the merge",
         patched.count("if (plBlank(cloud[dk]) && !plBlank(local[dk])) continue;") == 1),
        ("brace delta balanced",
         (patched.count("{") - original.count("{"))
         == (patched.count("}") - original.count("}"))),
        ("install21 timers intact", "install21" in patched),
        ("install22 reps intact", "K_REPS" in patched),
        ("relative planner link intact (install17)", "./" in patched),
    ]
    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("  OK   " if ok else "  FAIL ") + name)
    if bad:
        die("post-condition failed: " + "; ".join(bad))

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = TARGET + ".install28.bak-" + stamp
    shutil.copy2(TARGET, backup)
    print("backup written: " + backup)

    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(patched)

    written = open(TARGET, "r", encoding="utf-8").read()
    sha_after = hashlib.sha256(written.encode("utf-8")).hexdigest()
    print("")
    print("post-image sha256: " + sha_after)
    print("bytes: %d -> %d" % (len(original.encode("utf-8")),
                               len(written.encode("utf-8"))))
    print("")
    print("DONE. Now commit and push:")
    print("  git add planner.html forge_install28.py")
    print('  git commit -m "install28: planner pushes the five on save"')
    print("  git push")
    print("")
    print("NO workflow run needed - planner.html is hand-maintained.")
    print("")
    print("THEN, ORDER MATTERS: open the planner on your PHONE first and save")
    print("there, so the phone's fuller history is what reaches the cloud.")
    print("Only touch it on the Mac afterwards.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# forge_five_carryforward_20260830.py
# Adds a display-only carry-forward fallback to paintTodayFive() in forge_actions.py:
# when today's forge-top5 key is empty, the brief shows the most recent prior day's
# list (whole list, ticks and all) under a "Carried from <date>" header, instead of
# the "No five set" message. Writes NOTHING to storage. Real five replaces it on load.
# Target: forge_actions.py on gh-pages (the GENERATOR). A workflow run is required after.

import hashlib, sys, shutil, py_compile, datetime, os

TARGET   = "forge_actions.py"
PRE_SHA  = "a3a5ec277813d9032e78df375793dc7b1e27dbd58ff578cce62b7834a9c92b6c"
POST_SHA = "101d19a295f960914f240d701ec0cad519f5ff855c0ccaee7755e69466361c0f"

OLD_EMPTY = (
"  if (!real.length) {{\n"
"    host.innerHTML = '<div class=\"t5-empty\">No five set for today yet. Set them in the evening debrief or the planner &mdash; they appear here as soon as they exist.</div>';\n"
"    return;\n"
"  }}\n"
)
NEW_EMPTY = (
"  if (!real.length) {{\n"
"    var carriedFrom = null;\n"
"    for (var off = -1; off >= -60; off--) {{\n"
"      var cand = all[ymdOffset(off)];\n"
"      var cr = (cand || []).filter(function (i) {{ return i && i.t; }});\n"
"      if (cr.length) {{ real = cr; carriedFrom = ymdOffset(off); break; }}\n"
"    }}\n"
"    if (!carriedFrom) {{\n"
"      host.innerHTML = '<div class=\"t5-empty\">No five set for today yet. Set them in the evening debrief or the planner &mdash; they appear here as soon as they exist.</div>';\n"
"      return;\n"
"    }}\n"
"  }}\n"
)
OLD_TAIL = (
"  host.innerHTML = '<div class=\"t5-count\">' + done + ' of ' + real.length + ' closed</div>' + rows;\n"
)
NEW_TAIL = (
"  var t5hdr = '';\n"
"  if (carriedFrom) {{\n"
"    var _p = carriedFrom.split('-');\n"
"    var _d = new Date(+_p[0], +_p[1] - 1, +_p[2]);\n"
"    var _dn = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];\n"
"    var _mn = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];\n"
"    var _nice = _dn[_d.getDay()] + ' ' + _mn[_d.getMonth()] + ' ' + _d.getDate();\n"
"    t5hdr = '<div style=\"font-size:13px; font-weight:700; color:#7fd4e6; margin-bottom:8px; line-height:1.5;\">Carried from ' + _nice + ' &mdash; no five set for today yet.</div>';\n"
"  }}\n"
"  host.innerHTML = t5hdr + '<div class=\"t5-count\">' + done + ' of ' + real.length + ' closed</div>' + rows;\n"
)

def die(m): print("ABORT:", m); sys.exit(1)

if not os.path.exists(TARGET): die(TARGET + " not found - run me from inside the repo")
src = open(TARGET, encoding="utf-8").read()
cur = hashlib.sha256(src.encode()).hexdigest()
if cur == POST_SHA: die("already applied (file already at POST sha). Nothing to do.")
if cur != PRE_SHA:  die("PRE sha mismatch. Expected " + PRE_SHA + " got " + cur + ". NOT the deployed file - stopping, nothing written.")
if src.count(OLD_EMPTY) != 1: die("empty-state anchor not found exactly once (%d)" % src.count(OLD_EMPTY))
if src.count(OLD_TAIL)  != 1: die("tail anchor not found exactly once (%d)" % src.count(OLD_TAIL))

patched = src.replace(OLD_EMPTY, NEW_EMPTY).replace(OLD_TAIL, NEW_TAIL)
new_sha = hashlib.sha256(patched.encode()).hexdigest()
if new_sha != POST_SHA: die("POST sha mismatch after patch (%s). Stopping, nothing written." % new_sha)
for mk in ["function paintTodayFive","function paintYesterday","function ymdOffset","No five set for today yet"]:
    if mk not in patched: die("survivor marker missing: " + mk)

bak = TARGET + ".carryforward_20260830.bak"
shutil.copy2(TARGET, bak)
open(TARGET, "w", encoding="utf-8").write(patched)
py_compile.compile(TARGET, doraise=True)
print("OK - patched", TARGET)
print("backup:", bak)
print("new sha256:", new_sha, "(matches expected POST)")
print("Next: commit + push to gh-pages, then RUN THE WORKFLOW (this is the generator).")

#!/usr/bin/env python3
# forge_planner_keystone_star_20260825.py
# Adds a tappable keystone star to each of the planner's Today five, so the
# keystone can be marked (or changed) in the morning if it was not set in the
# evening debrief. Single-select and gold, matching the debrief. The brief and
# midday already render the star from the same k field, so it shows there at
# once. planner.html is hand-maintained: run locally, then push. No workflow.
import hashlib, os, sys, time

FILE = 'planner.html'
PRE_SHA = 'dbc7b5ba75eac1c38e1e7e07eb61ae46795ca6bfeb506ed7fcb63cf5638cd1fc'

CSS_OLD = "    .t5hr {"
CSS_NEW = (
    "    .t5star {\n"
    "      width: 26px; height: 26px; flex-shrink: 0; border: 2px solid #0d0d0d; border-radius: 6px;\n"
    "      background: rgba(255,255,255,0.6); font-size: 15px; line-height: 1; color: rgba(13,13,13,0.28);\n"
    "      cursor: pointer; touch-action: manipulation; padding: 0;\n"
    "    }\n"
    "    .t5star.on { background: #0d0d0d; color: #ffc107; border-color: #0d0d0d; }\n"
    "    .t5hr {"
)

JS_OLD = "      row.appendChild(num); row.appendChild(chk); row.appendChild(txt); row.appendChild(sel);"
JS_NEW = (
    "      var star = document.createElement('button');\n"
    "      star.type = 'button';\n"
    "      star.className = 't5star' + (it.k ? ' on' : '');\n"
    "      star.innerHTML = '\\u2605';\n"
    "      star.title = 'Keystone';\n"
    "      star.onclick = function(){ var a = loadTop5(); var was = !!(a[i] && a[i].k); for (var j = 0; j < 5; j++){ if (a[j]) a[j].k = false; } if (a[i]) a[i].k = !was; saveTop5(a); renderTop5(); };\n"
    "\n"
    "      row.appendChild(num); row.appendChild(chk); row.appendChild(star); row.appendChild(txt); row.appendChild(sel);"
)

def die(m):
    print("ABORT: " + m + "  (file left untouched)"); sys.exit(1)

if not os.path.exists(FILE):
    die(FILE + " not found. cd to the repo folder first.")

src = open(FILE, 'r', encoding='utf-8').read()
cur = hashlib.sha256(src.encode('utf-8')).hexdigest()
if cur != PRE_SHA:
    die("planner.html is not the expected version (already patched, or newer).\n"
        "       Expected " + PRE_SHA + "\n       Got      " + cur)

for name, old in [("CSS anchor", CSS_OLD), ("JS anchor", JS_OLD)]:
    n = src.count(old)
    if n != 1:
        die("%s found %d times, expected exactly 1: %r" % (name, n, old[:50]))

new = src.replace(CSS_OLD, CSS_NEW).replace(JS_OLD, JS_NEW)

checks = {
    "star CSS present":       ".t5star {" in new and ".t5star.on {" in new,
    "star element created":   "star.className = 't5star'" in new,
    "star appended in row":   "row.appendChild(star)" in new,
    "single-select handler":  "for (var j = 0; j < 5; j++){ if (a[j]) a[j].k = false; }" in new,
    "old append line gone":   "row.appendChild(chk); row.appendChild(txt); row.appendChild(sel);" not in new,
    "loadTop5 untouched":     new.count("function loadTop5(){") == 1,
    "saveTop5 untouched":     new.count("function saveTop5(arr){") == 1,
    "renderTop5 once":        new.count("function renderTop5(){") == 1,
    "style tags intact":      new.count("<style>") == src.count("<style>") and new.count("</style>") == src.count("</style>"),
}
for k, ok in checks.items():
    if not ok:
        die("post-check failed: " + k)

delta = len(new) - len(src)
if not (300 < delta < 900):
    die("unexpected size change of %d bytes" % delta)

bak = FILE + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
open(bak, 'w', encoding='utf-8').write(src)
open(FILE, 'w', encoding='utf-8').write(new)
print("OK  planner.html patched.")
print("    backup:   " + bak)
print("    POST-SHA: " + hashlib.sha256(new.encode('utf-8')).hexdigest())

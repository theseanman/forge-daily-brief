#!/usr/bin/env python3
# forge_cue_labels_bigger_20260825.py
# Bumps the four cue-card section labels (TODAY'S CUE, DEPTH, DECIDING,
# LIVE OR OVER) from 10px to 13px so they read as headers above the body text.
# That exact label style string is used ONLY by those four labels, so nothing
# else on the brief changes. forge_actions.py is the GENERATOR: run, push, then
# RUN THE WORKFLOW.
import hashlib, os, sys, time, ast

FILE = 'forge_actions.py'
PRE_SHA = 'b6292a182263c33ce29b93df86e9fb36727938515832119ef1a2e8c6c68dae33'

OLD = "font-size:10px; letter-spacing:0.16em; color:#1a5fa8; font-weight:700;"
NEW = "font-size:13px; letter-spacing:0.16em; color:#1a5fa8; font-weight:700;"

def die(m):
    print("ABORT: " + m + "  (file left untouched)"); sys.exit(1)

if not os.path.exists(FILE):
    die(FILE + " not found. cd to the repo folder first.")

src = open(FILE, 'r', encoding='utf-8').read()
cur = hashlib.sha256(src.encode('utf-8')).hexdigest()
if cur != PRE_SHA:
    die("forge_actions.py is not the expected version.\n       Expected " + PRE_SHA + "\n       Got      " + cur)

n = src.count(OLD)
if n != 4:
    die("expected the label style exactly 4 times, found %d (scope changed - stopping)" % n)

new = src.replace(OLD, NEW)

checks = {
    "new style x4":  new.count(NEW) == 4,
    "old style gone": new.count(OLD) == 0,
    "labels intact":  all(t in new for t in ["TODAY&rsquo;S CUE", ">DEPTH", ">DECIDING", ">LIVE OR OVER"]),
    "no brace change": new.count("{") == src.count("{") and new.count("}") == src.count("}"),
    "only the size changed": len(new) == len(src) + 4 * (len("13px") - len("10px")),
}
for k, ok in checks.items():
    if not ok:
        die("post-check failed: " + k)

try:
    ast.parse(new)
except SyntaxError as e:
    die("patched file does not parse: " + str(e))

bak = FILE + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
open(bak, 'w', encoding='utf-8').write(src)
open(FILE, 'w', encoding='utf-8').write(new)
print("OK  forge_actions.py patched.")
print("    backup:   " + bak)
print("    POST-SHA: " + hashlib.sha256(new.encode('utf-8')).hexdigest())

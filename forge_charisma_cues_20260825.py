#!/usr/bin/env python3
# forge_charisma_cues_20260825.py
# Generator pass: (A) adds two cues to the daily rotation (empathic statement,
# name+detail); (B) adds a standing daily DEPTH line under today's cue; (C) adds
# a button on the brief that opens the charisma reference page. All three edits
# are inside the brief f-string; none contain braces. forge_actions.py is the
# GENERATOR: run locally, push, then RUN THE WORKFLOW (index.html is generated).
import hashlib, os, sys, time

FILE = 'forge_actions.py'
PRE_SHA = '1d2fc2dd4079f083fb398236640104137bd6e56845b03f8b08a9fed74d9ef551'

A_OLD = "  'Pay attention to the person, not to how you are performing.'"
A_NEW = (
    "  'Pay attention to the person, not to how you are performing.',\n"
    "  'Name the emotion before your content &mdash; &ldquo;that must have been hard,&rdquo; &ldquo;you sound proud.&rdquo; They feel heard, not answered.',\n"
    "  'Learn one name and one detail about someone new. Use both next time &mdash; it is rare enough to be memorable.'"
)

B_OLD = "      '<div style=\"font-size:13px; font-weight:600; line-height:1.45; margin-bottom:12px;\">' + pfCue() + '</div>' +"
B_NEW = (
    B_OLD + "\n"
    "      '<div style=\"font-size:10px; letter-spacing:0.16em; color:#1a5fa8; font-weight:700; margin-bottom:3px;\">DEPTH</div>' +\n"
    "      '<div style=\"font-size:12px; line-height:1.5; margin-bottom:12px;\">Go one layer deeper with someone today &mdash; then match with your own at the same layer. That is how an acquaintance becomes a friend.</div>' +"
)

C_OLD = (
    "      '</div>' +\n"
    "    '</div>';"
)
C_NEW = (
    "      '</div>' +\n"
    "      '<a href=\"./charisma.html\" style=\"display:block; text-align:center; margin-top:13px; padding:11px; border-radius:10px; background:rgba(74,157,232,0.28); border:1px solid rgba(74,157,232,0.55); color:#eaf4ff; font-weight:800; letter-spacing:0.06em; text-decoration:none; font-size:13px;\">Charisma protocol &amp; drill &rarr;</a>' +\n"
    "    '</div>';"
)

def die(m):
    print("ABORT: " + m + "  (file left untouched)"); sys.exit(1)

if not os.path.exists(FILE):
    die(FILE + " not found. cd to the repo folder first.")

src = open(FILE, 'r', encoding='utf-8').read()
cur = hashlib.sha256(src.encode('utf-8')).hexdigest()
if cur != PRE_SHA:
    die("forge_actions.py is not the expected version (already patched, or newer).\n"
        "       Expected " + PRE_SHA + "\n       Got      " + cur)

# Anchor uniqueness (C_OLD must be scoped to the cue card, not the whole file).
if src.count(A_OLD) != 1: die("cue anchor not unique (%d)" % src.count(A_OLD))
if src.count(B_OLD) != 1: die("pfCue anchor not unique (%d)" % src.count(B_OLD))
if src.count(C_OLD) != 1: die("card-close anchor not unique (%d) - would edit the wrong div" % src.count(C_OLD))

new = src.replace(A_OLD, A_NEW).replace(B_OLD, B_NEW).replace(C_OLD, C_NEW)

checks = {
    "empathic cue added":  "Name the emotion before your content" in new,
    "name+detail cue added":"Learn one name and one detail about someone new" in new,
    "cue list closes ok":  "it is rare enough to be memorable.'\n];" in new,
    "old last-cue-no-comma gone": "not to how you are performing.'\n];" not in new,
    "depth label added":   ">DEPTH</div>" in new,
    "depth line added":    "Go one layer deeper with someone today" in new,
    "charisma link added": './charisma.html' in new and 'Charisma protocol' in new,
    "no brace leak in inserts": ('{' not in A_NEW+B_NEW+C_NEW) and ('}' not in A_NEW+B_NEW+C_NEW),
}
for k, ok in checks.items():
    if not ok:
        die("post-check failed: " + k)

# Python must still parse.
import ast
try:
    ast.parse(new)
except SyntaxError as e:
    die("patched file does not parse: " + str(e))

delta = len(new) - len(src)
if not (400 < delta < 1200):
    die("unexpected size change of %d bytes" % delta)

bak = FILE + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
open(bak, 'w', encoding='utf-8').write(src)
open(FILE, 'w', encoding='utf-8').write(new)
print("OK  forge_actions.py patched.")
print("    backup:   " + bak)
print("    POST-SHA: " + hashlib.sha256(new.encode('utf-8')).hexdigest())

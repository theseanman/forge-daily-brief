#!/usr/bin/env python3
# forge_recall_scrollfix_20260825.py
# Makes the Orientation Recall screen scrollable and stops the hidden answer
# block from reserving space, so the Reveal / Next buttons are reachable on
# every step (they were rendering below the bottom edge of a non-scrolling
# screen). CSS-only. recall.html is hand-maintained: run locally, then push.
# No workflow run.
import hashlib, os, sys, time

FILE = 'recall.html'
PRE_SHA = '47e3059c187fc7ae73387dd8f41b5c4b8453b23d7f6b82158f3e08fcdc35fc46'

REPLACEMENTS = [
    (
      "  .mid{ flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:24px 6px; }",
      "  .mid{ flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; text-align:center; padding:24px 6px; overflow-y:auto; -webkit-overflow-scrolling:touch; }\n"
      "  .mid::before, .mid::after{ content:''; margin:auto; flex:0 0 auto; }"
    ),
    (
      "  .reveal-wrap{ margin-top:22px; width:100%; max-width:640px; opacity:0; transform:translateY(6px); transition:opacity .35s ease, transform .35s ease; pointer-events:none; }",
      "  .reveal-wrap{ margin-top:0; width:100%; max-width:640px; opacity:0; transform:translateY(6px); max-height:0; overflow:hidden; transition:opacity .35s ease, transform .35s ease, max-height .4s ease, margin-top .35s ease; pointer-events:none; }"
    ),
    (
      "  .reveal-wrap.on{ opacity:1; transform:translateY(0); pointer-events:auto; }",
      "  .reveal-wrap.on{ opacity:1; transform:translateY(0); pointer-events:auto; max-height:60vh; overflow:auto; margin-top:22px; }"
    ),
]

def die(msg):
    print("ABORT: " + msg + "  (file left untouched)")
    sys.exit(1)

if not os.path.exists(FILE):
    die(FILE + " not found. cd to the repo folder first.")

src = open(FILE, 'r', encoding='utf-8').read()
cur = hashlib.sha256(src.encode('utf-8')).hexdigest()
if cur != PRE_SHA:
    die("recall.html is not the expected version (already patched, or a newer\n"
        "       build). Expected pre-SHA " + PRE_SHA + "\n"
        "       Got                      " + cur)

# Every anchor must be present exactly once BEFORE we touch anything.
for old, _ in REPLACEMENTS:
    n = src.count(old)
    if n != 1:
        die("anchor found %d times, expected exactly 1:\n       %r" % (n, old[:60]))

new = src
for old, rep in REPLACEMENTS:
    new = new.replace(old, rep)

# Post-conditions — fail closed if any is off.
checks = {
    "scroll enabled":        "overflow-y:auto; -webkit-overflow-scrolling:touch;" in new,
    "spacer centering":      ".mid::before, .mid::after{ content:''; margin:auto; flex:0 0 auto; }" in new,
    "wrap collapses hidden": "max-height:0; overflow:hidden;" in new,
    "wrap expands on reveal":"max-height:60vh; overflow:auto; margin-top:22px;" in new,
    "old .mid gone":         "justify-content:center; text-align:center; padding:24px 6px; }" not in new,
    "style block intact":    new.count("<style>") == src.count("<style>") == 1 and new.count("</style>") == src.count("</style>") == 1,
}
for k, ok in checks.items():
    if not ok:
        die("post-check failed: " + k)

# JS must be byte-identical — every edit is inside <style>, which precedes <script>.
if new[new.index("<script>"):] != src[src.index("<script>"):]:
    die("the <script> section changed — it must not. No JS was intended.")

# Only three lines' worth of CSS changed; sanity-bound the size delta.
delta = len(new) - len(src)
if not (0 < delta < 400):
    die("unexpected size change of %d bytes" % delta)

bak = FILE + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
open(bak, 'w', encoding='utf-8').write(src)
open(FILE, 'w', encoding='utf-8').write(new)
post = hashlib.sha256(new.encode('utf-8')).hexdigest()
print("OK  recall.html patched.")
print("    backup:   " + bak)
print("    POST-SHA: " + post)

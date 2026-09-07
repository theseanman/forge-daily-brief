#!/usr/bin/env python3
"""
forge_protocols_checklist_20260906.py

Adds The Daily Checklist as the third card in "The daily spine" section of the
protocols index, directly under The Evening Protocol.

  Edits    : protocols.html  (hand-maintained, live on push, NO workflow)
  Writes   : nothing else
  New keys : none

Placed in the spine rather than "Available protocols" because everything in that
second list is a page you read or drill; the checklist is a daily instrument and
the record surface.

The thumbnail needs no wiring. protocols.html's own boot script derives the image
key from the href, so ./checklist.html reads forge-img-checklist automatically --
the same route as every other card.

class="protocol gold" sets the left border colour only. It carries no meaning in
this page; it keeps the spine alternating gold / plain / gold.

Fails closed: any anchor problem leaves the file byte-identical.
"""

import hashlib
import os
import shutil
import sys

TARGET = "protocols.html"
PRE_SHA = "987811c9e5cd104140ef0d985bda2e358e90f2cb209840d23c684fb375c98dfb"

# End of the evening card + the close of the spine list + the next heading.
A1_OLD = """      <div class="p-arrow">&rarr;</div>
    </a>
  </div>

  <p class="count">Available protocols</p>"""

A1_NEW = """      <div class="p-arrow">&rarr;</div>
    </a>

    <a class="protocol gold" href="./checklist.html">
      <div class="p-thumb"></div>
      <div class="p-body">
        <div class="p-name">The Daily Checklist</div>
        <div class="p-desc">23 items across four weighted tiers, 61 points at the top end, five starred as current priorities &mdash; the score is computed at the end, not carried in your head.</div>
        <div class="p-modes">Log</div>
      </div>
      <div class="p-arrow">&rarr;</div>
    </a>
  </div>

  <p class="count">Available protocols</p>"""

EDITS = [
    ("daily spine card", A1_OLD, A1_NEW),
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

    if out.count('href="./checklist.html"') != 1:
        die("post-check failed: checklist card not present exactly once.")
    if out.count('a class="protocol') != src.count('a class="protocol') + 1:
        die("post-check failed: card count did not increase by exactly one.")

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

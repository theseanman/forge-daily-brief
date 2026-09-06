#!/usr/bin/env python3
"""
forge_threemoments_wording_20260906.py

Rewords the four tests inside the Sort flow so each question names what it is
asking about. "Would it change what you do now?" had no antecedent once you
reached it via the button - Sean caught it on the live page. Each test now names
the thought and carries a one-line subline; the entry button reads "Sort a
thought" rather than "A thought arrived".

  Rewrites : four-moments.html   (hand-maintained, live on push, NO workflow)
  Edits    : nothing else. protocols.html is untouched.
  New keys : none. No Cloudflare paste.

  four-moments.html pre  : fdef081fb640387c85d8ceaeb16f6363b8599e1e9ead4168806d6598cc3bbcb1
  four-moments.html post : 5e871b65b6e60710e8b9de95b4831646f8065ac464557e8d51b68b34dce37cce

Logic is unchanged - same three moments, same two gate questions, same four
tests and three disposals. Wording only.

Run from inside the repo, on gh-pages:
    python3 forge_threemoments_wording_20260906.py
"""

import base64
import gzip
import hashlib
import os
import shutil
import sys

TARGET = "four-moments.html"
PRE = "fdef081fb640387c85d8ceaeb16f6363b8599e1e9ead4168806d6598cc3bbcb1"
POST = "5e871b65b6e60710e8b9de95b4831646f8065ac464557e8d51b68b34dce37cce"
BACKUP = "four-moments.html.bak-wording-20260906"

B64 = """
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
"""


def die(m):
    print("ABORT: " + m)
    print("Nothing was written.")
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die(TARGET + " not found. Run this from inside the repo working directory.")
    src = open(TARGET, encoding="utf-8").read()
    cur = hashlib.sha256(src.encode("utf-8")).hexdigest()
    print("pre-image  : " + cur)
    if cur == POST:
        die("this wording fix has already been applied.")
    if cur != PRE:
        die("pre-image does not match. Expected " + PRE + ".\n"
            "       Rebuild against the current file - do not force it.")

    page = gzip.decompress(base64.b64decode("".join(B64.split()))).decode("utf-8")
    if hashlib.sha256(page.encode("utf-8")).hexdigest() != POST:
        die("carried page failed its integrity check - truncated or corrupted.")
    print("  ok  payload intact")

    for marker in ["Would this thought change", "just interrupted you",
                   "Sort a thought", "act on the thought right now",
                   "function startTests()", "one of three kinds"]:
        if marker not in page:
            die("payload missing expected marker: " + marker)
    for gone in ["A thought arrived", "Would it change <b>what you do now"]:
        if gone in page:
            die("payload still contains the old wording: " + gone)
    if page.count("<svg") != 2:
        die("payload should carry exactly two diagrams.")
    print("  ok  markers present, old wording absent")

    shutil.copy2(TARGET, BACKUP)
    open(TARGET, "w", encoding="utf-8").write(page)
    if hashlib.sha256(open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest() != POST:
        shutil.copy2(BACKUP, TARGET)
        die("bytes wrong on disk. Original restored from " + BACKUP + ".")
    print("  ok  written and verified")
    print("")
    print("WRITTEN   : " + TARGET)
    print("BACKUP    : " + BACKUP)
    print("")
    print("Hand-maintained page. Commit and push - NO workflow run needed.")


if __name__ == "__main__":
    main()

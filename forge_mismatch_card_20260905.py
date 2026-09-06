#!/usr/bin/env python3
"""
forge_mismatch_card_20260905.py

Adds the MISMATCH block to the top of the Practice card on the morning brief.

  Target      : forge_actions.py   (THE GENERATOR - needs a workflow run after push)
  Pre-image   : d78407ea01353f74a5d80e575de508b9f47ebcdc88a220a532a9b544995fdd9d
  Post-image  : 382c62c2aaf43ab36d284fdfdfa80fe9acbcb8132c6b10db19ef6baa66de8678
  New keys    : none
  Cloudflare  : nothing to do
  Network     : none

Reads only forge-mushin, forge-project and forge-reps, all of which the brief
already pulls. Renders three "days since" lines, flat when current and red when
past threshold, under the line:

    Good news is dangerous. Bad news is the only thing that saves you.

Aborts without touching anything if the pre-image SHA does not match, if an
anchor is missing or ambiguous, or if any post-check fails.

Run it from inside the repo, on gh-pages:
    python3 forge_mismatch_card_20260905.py
"""

import ast
import base64
import gzip
import hashlib
import os
import shutil
import sys

TARGET = "forge_actions.py"
PRE_SHA = "d78407ea01353f74a5d80e575de508b9f47ebcdc88a220a532a9b544995fdd9d"
POST_SHA = "382c62c2aaf43ab36d284fdfdfa80fe9acbcb8132c6b10db19ef6baa66de8678"
BACKUP = "forge_actions.py.bak-mismatch-20260905"

FUNC_ANCHOR = "\nfunction paintPractice() {{\n"
HTML_ANCHOR = "  host.innerHTML =\n"
HTML_NEW = "  host.innerHTML =\n    mmBlock() +\n"

STATEMENT = "Good news is dangerous. Bad news is the only thing that saves you."

PAYLOAD_B64 = """
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
"""


def die(msg):
    print("ABORT: " + msg)
    print("Nothing was written. " + TARGET + " is untouched.")
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die(TARGET + " not found. Run this from inside the repo working directory.")

    src = open(TARGET, encoding="utf-8").read()
    pre = hashlib.sha256(src.encode("utf-8")).hexdigest()
    print("pre-image  : " + pre)

    if pre == POST_SHA:
        die("this installer has already been applied to " + TARGET + ".")
    if pre != PRE_SHA:
        die("pre-image SHA does not match. Expected " + PRE_SHA + ".\n"
            "       The file has moved since this installer was built. It needs\n"
            "       rebuilding against the current file - do not force it.")

    if "mmBlock" in src:
        die("mmBlock already present in " + TARGET + ".")
    if src.count(FUNC_ANCHOR) != 1:
        die("paintPractice anchor matched " + str(src.count(FUNC_ANCHOR)) + " times, expected 1.")
    if src.count(HTML_ANCHOR) != 1:
        die("host.innerHTML anchor matched " + str(src.count(HTML_ANCHOR)) + " times, expected 1.")

    payload = gzip.decompress(base64.b64decode("".join(PAYLOAD_B64.split()))).decode("utf-8")
    if "mmBlock" not in payload or STATEMENT not in payload:
        die("payload failed its own integrity check - truncated or corrupted.")

    out = src.replace(FUNC_ANCHOR, "\n" + payload + "function paintPractice() {{\n", 1)
    out = out.replace(HTML_ANCHOR, HTML_NEW, 1)

    checks = [
        ("mmBlock defined and called", out.count("mmBlock") == 2),
        ("MISMATCH header present once", out.count("MISMATCH") == 1),
        ("statement present once", out.count(STATEMENT) == 1),
        ("limits footer present", "a clean reading is not an all-clear" in out),
        ("paintPractice survives", out.count("function paintPractice() {{") == 1),
        ("pullPractice survives", "function pullPractice() {{" in out),
        ("pullReps survives", "function pullReps() {{" in out),
        ("no single braces leaked in payload", "{{" in payload and payload.count("{") == payload.count("}")),
        ("brace balance unchanged", out.count("{") - out.count("}") == src.count("{") - src.count("}")),
    ]
    for name, passed in checks:
        if not passed:
            die("post-check failed: " + name)
        print("  ok  " + name)

    try:
        ast.parse(out)
    except SyntaxError as e:
        die("patched file is not valid Python: " + str(e))
    print("  ok  ast.parse")

    post = hashlib.sha256(out.encode("utf-8")).hexdigest()
    if post != POST_SHA:
        die("post-image SHA is " + post + ", expected " + POST_SHA + ".")
    print("  ok  post-image SHA matches")

    shutil.copy2(TARGET, BACKUP)
    open(TARGET, "w", encoding="utf-8").write(out)

    check = hashlib.sha256(open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest()
    if check != POST_SHA:
        shutil.copy2(BACKUP, TARGET)
        die("bytes on disk do not match after write. Original restored from " + BACKUP + ".")

    print("")
    print("WRITTEN   : " + TARGET + "  (" + str(len(src)) + " -> " + str(len(out)) + " chars)")
    print("BACKUP    : " + BACKUP)
    print("post-image: " + post)
    print("")
    print("This is the GENERATOR. Commit, push, then run the workflow.")
    print("index.html is generated output - do not edit it by hand.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
forge_rhs_calendar_20260912.py

Retires the Brighouse School ICS feed from SUBSCRIBED_ICS_URLS and adds the
Richmond Secondary School feed in its place.

Target : forge_actions.py  (the generator; a workflow run is required after)
PRE    : 678f385d5d02ed07a6bb95aec7734853af1c364409bfd9ff5c11f6fe5eb9f201
POST   : asserted after write

Aborts without writing if the pre-image does not match, if either anchor is
not found exactly once, or if the result does not parse. Backs up first.
"""

import ast
import hashlib
import os
import shutil
import sys

TARGET = "forge_actions.py"

PRE_SHA = "678f385d5d02ed07a6bb95aec7734853af1c364409bfd9ff5c11f6fe5eb9f201"

OLD_LINE = '    ("Brighouse School", "https://brighouse.sd38.bc.ca/calendar-feed.ics"),\n'
NEW_LINE = '    ("Richmond Secondary", "https://rhs.sd38.bc.ca/calendar-feed.ics"),\n'


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fail(msg):
    print("ABORTED - nothing was written.")
    print("  " + msg)
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        fail("%s is not in this directory. cd into the repo first." % TARGET)

    with open(TARGET, "r", encoding="utf-8") as f:
        src = f.read()

    got = sha(src)
    print("pre-image sha256 : %s" % got)

    if got == "":
        fail("empty file")

    if got != PRE_SHA:
        if NEW_LINE in src and OLD_LINE not in src:
            print("This patch is ALREADY APPLIED - Richmond Secondary is present")
            print("and Brighouse is gone. Nothing to do.")
            sys.exit(0)
        fail("pre-image mismatch. Expected %s\n  The file has changed since this "
             "installer was built - it must be rebuilt, not forced." % PRE_SHA)

    n_old = src.count(OLD_LINE)
    n_new = src.count(NEW_LINE)
    if n_old != 1:
        fail("Brighouse anchor found %d times, expected exactly 1" % n_old)
    if n_new != 0:
        fail("Richmond Secondary line already present %d times" % n_new)

    if "SUBSCRIBED_ICS_URLS = [" not in src:
        fail("SUBSCRIBED_ICS_URLS list not found")

    out = src.replace(OLD_LINE, NEW_LINE, 1)

    # post-conditions, all asserted before the write
    if out.count(NEW_LINE) != 1:
        fail("post-image does not carry exactly one Richmond Secondary line")
    if "brighouse" in out.lower():
        fail("post-image still mentions brighouse somewhere")
    if len(out.splitlines()) != len(src.splitlines()):
        fail("line count changed - the edit was not a clean swap")

    try:
        ast.parse(out)
    except SyntaxError as e:
        fail("patched file does not parse: %s" % e)

    # prior work must survive
    for marker in ("def fetch_ics_structured",
                   "def fetch_ics_events",
                   "def dedupe_events",
                   "expand=True",
                   "CALENDAR_ERRORS"):
        if marker not in out:
            fail("marker lost from patched file: %s" % marker)

    backup = TARGET + ".bak-rhscal-20260912"
    shutil.copy2(TARGET, backup)
    print("backup written    : %s" % backup)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(out)

    with open(TARGET, "r", encoding="utf-8") as f:
        check = f.read()

    if check != out:
        shutil.copy2(backup, TARGET)
        fail("write verification failed - original restored from backup")

    print("post-image sha256 : %s" % sha(check))
    print()
    print("DONE. Brighouse retired, Richmond Secondary added.")
    print("forge_actions.py is the generator - a workflow run is still required.")


if __name__ == "__main__":
    main()

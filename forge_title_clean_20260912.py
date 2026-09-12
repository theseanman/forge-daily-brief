#!/usr/bin/env python3
"""
forge_title_clean_20260912.py

Strips byte-order marks and zero-width characters out of calendar event
titles. These arrive in the Richmond Secondary feed because the events are
pasted into the school website from Word or PDF, and they defeat the
title-matching in dedupe_events().

Adds one helper, clean_title(), and routes all four title reads through it:
  - two iCloud CalDAV reads (fetch_events_for_range, fetch_events_structured)
  - one subscribed-feed read in fetch_ics_events
  - one subscribed-feed read in fetch_ics_structured

The two "summary = feed_name" fallbacks are deliberately left alone - they
carry no pasted text.

Target : forge_actions.py  (the generator; a workflow run is required after)
PRE    : 7295b8032f65b14a006ecf5622931edbc29e4dd993c6c61964dbdb4bf3e43309
POST   : asserted after write

Aborts without writing on any pre-image mismatch, anchor-count mismatch, or
parse failure. Backs up first.
"""

import ast
import hashlib
import os
import shutil
import sys

TARGET = "forge_actions.py"

PRE_SHA = "7295b8032f65b14a006ecf5622931edbc29e4dd993c6c61964dbdb4bf3e43309"

HELPER = '''ZERO_WIDTH_CHARS = "\\ufeff\\u200b\\u200c\\u200d\\u2060"


def clean_title(s):
    """Remove byte-order marks and zero-width characters from a calendar
    title, then trim surrounding whitespace. School feed events are pasted
    from Word/PDF and carry these invisibly; they break title matching in
    dedupe_events() and can render as stray glyphs."""
    if not s:
        return s
    s = str(s)
    for ch in ZERO_WIDTH_CHARS:
        s = s.replace(ch, "")
    return s.strip()


'''

# --- anchors, all extracted programmatically from the deployed file ---

A_HELPER_AT = "def fetch_events_for_range(calendars, start, end):"

A_CALDAV = "summary = str(vevent.summary.value)"
B_CALDAV = "summary = clean_title(vevent.summary.value)"

A_ICS_TEXT = "summary = line[8:].strip()"
B_ICS_TEXT = "summary = clean_title(line[8:])"

A_ICS_STRUCT = 'summary = line.split(":", 1)[-1].strip()'
B_ICS_STRUCT = 'summary = clean_title(line.split(":", 1)[-1])'


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

    if got != PRE_SHA:
        if "def clean_title(" in src:
            print("This patch is ALREADY APPLIED - clean_title is present.")
            print("Nothing to do.")
            sys.exit(0)
        fail("pre-image mismatch. Expected %s\n  The file has changed since this "
             "installer was built - it must be rebuilt, not forced." % PRE_SHA)

    # anchor counts, asserted before anything is changed
    checks = [
        (A_HELPER_AT, 1, "fetch_events_for_range definition"),
        (A_CALDAV, 2, "iCloud title reads"),
        (A_ICS_TEXT, 1, "fetch_ics_events title read"),
        (A_ICS_STRUCT, 1, "fetch_ics_structured title read"),
    ]
    for needle, want, label in checks:
        n = src.count(needle)
        if n != want:
            fail("%s: found %d, expected %d" % (label, n, want))

    if "def clean_title(" in src:
        fail("clean_title already defined - unexpected state")

    out = src
    out = out.replace(A_HELPER_AT, HELPER + A_HELPER_AT, 1)
    out = out.replace(A_CALDAV, B_CALDAV)          # both iCloud sites
    out = out.replace(A_ICS_TEXT, B_ICS_TEXT, 1)
    out = out.replace(A_ICS_STRUCT, B_ICS_STRUCT, 1)

    # post-conditions
    if out.count("def clean_title(") != 1:
        fail("clean_title not defined exactly once")
    if out.count("clean_title(") != 5:
        fail("expected 5 clean_title occurrences (1 def + 4 calls), found %d"
             % out.count("clean_title("))
    for needle, _, label in checks[1:]:
        if needle in out:
            fail("old title read survived: %s" % label)

    try:
        tree = ast.parse(out)
    except SyntaxError as e:
        fail("patched file does not parse: %s" % e)

    # clean_title must be defined at module level, above first use
    names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    if "clean_title" not in names:
        fail("clean_title is not a module-level function")
    order = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            order[n.name] = n.lineno
    if order["clean_title"] > order.get("fetch_events_for_range", 10 ** 9):
        fail("clean_title is defined after its first caller")

    # prior work must survive untouched
    for marker in ("def fetch_ics_structured",
                   "def fetch_ics_events",
                   "def dedupe_events",
                   "expand=True",
                   "CALENDAR_ERRORS",
                   'https://rhs.sd38.bc.ca/calendar-feed.ics'):
        if marker not in out:
            fail("marker lost from patched file: %s" % marker)
    if "brighouse" in out.lower():
        fail("brighouse reappeared - wrong base file")

    backup = TARGET + ".bak-titleclean-20260912"
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
    print("DONE. Titles are now cleaned at all four read sites.")
    print("forge_actions.py is the generator - a workflow run is still required.")


if __name__ == "__main__":
    main()

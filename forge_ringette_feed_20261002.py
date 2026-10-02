#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
forge_ringette_feed_20261002.py

Patches forge_actions.py ONLY. The three changes Sean approved on Oct 2 2026,
plus two defects found while reading the file.

  1. RINGETTE FEED RELINKED. The RAMP team ids rotated for the 2026-27 season:
     3178874,3178962 becomes 5063785,5136202, the combined family link covering
     both girls. It stays in SUBSCRIBED_ICS_URLS, so it lands in the Calendar
     card and in data.json alongside the school events, and reaches the planner.

  2. READABLE RINGETTE TITLES. RAMP packs four fields into one SUMMARY separated
     by escaped newlines, so without this the brief shows the literal
     characters. Four segments become:
         Layna - U12A Practice . Updated: Share ice with U12B
     The Updated note is kept, per Sean. Every other feed gets only a generic
     RFC5545 unescape, which is a no-op for a single-line SUMMARY.

  3. NO MORE SILENT DEAD FEEDS. The old Ringette link answered 200 with zero
     events for roughly two months and nothing on the brief said so. Now any
     feed returning no events at all raises the existing CALENDAR FEED PROBLEM
     banner, and the four feeds named in ICS_ALWAYS_FUTURE also warn when they
     carry nothing ahead of today. Deliberately not every feed: a quiet week is
     normal for some, and a warning that cries wolf gets ignored.

  4. DEFECT FIXED. fetch_ics_events never did RFC5545 line unfolding while
     fetch_ics_structured always did, so a long SUMMARY truncated mid-word on
     the brief while reading correctly in the planner.

  5. DEFECT FIXED. Both parsers matched only a bare "SUMMARY:" and would miss
     "SUMMARY;LANGUAGE=en:".

VERIFIED BEFORE HANDOVER, built against the gh-pages archive of Oct 2 2026:
  - all 9 anchors extracted programmatically and asserted unique
  - py_compile with -W error: clean, no warnings
  - the 11 real SUMMARY values from the live feed formatted and read back
  - 5 other feeds proved BYTE-UNCHANGED through the new formatter
  - 11 edge cases: empty, None, 1-segment, 2-segment, all-empty, folded,
    escaped comma/semicolon/backslash, uppercase UPDATED:, no division token
  - 7 feed-health scenarios pass, including both false-positive guards: a
    future event outside the 7-day window does NOT warn, and a feed not on the
    always-future list carrying only past events does NOT warn
  - full generate_html() render diffed against the unpatched generator on
    identical inputs: BYTE-IDENTICAL, so no rendering behaviour changed
  - node --check clean on the emitted JS

NOT verified: the live feed as the GitHub Actions runner sees it. RAMP refuses
Claude's sandbox, so the fetch was done through a different route. If the runner
is blocked too, the new banner will now say so out loud instead of going quiet.

RUN GATE. Check this file before you run it:
    shasum -a 256 forge_ringette_feed_20261002.py
and compare the result against the value Claude stated in chat. A file cannot
carry its own hash, so the expected value is deliberately not written here --
were it written here it would be whatever the file claims, which proves nothing.

It also guards itself: it refuses to run unless forge_actions.py hashes to
1b8ae1603c7ef1e65599aeee6b295b4ce6bdd54450407465e91242e3973984c8, and refuses to write unless the
result hashes to c8dd82bbbb3ff14893fdeca247a82f59c4f9bbd4ed15ee1b991f7cb55b0ffe3b.

forge_actions.py is the GENERATOR, so a WORKFLOW RUN is required after the push.
planner.html, the evening debrief and index.html are not touched.
"""

import ast
import base64
import gzip
import hashlib
import io
import json
import os
import sys

TARGET = "forge_actions.py"
BACKUP = "forge_actions.py.bak-ringette-20261002"
PRE_SHA = "1b8ae1603c7ef1e65599aeee6b295b4ce6bdd54450407465e91242e3973984c8"
POST_SHA = "c8dd82bbbb3ff14893fdeca247a82f59c4f9bbd4ed15ee1b991f7cb55b0ffe3b"
N_EDITS = 9
PAYLOAD = "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"

# Earlier work that must survive this patch. Checked as an INVARIANT -- each
# needle must appear exactly as many times after the patch as before it -- not
# against hardcoded counts. Hardcoding a count means the check can be wrong
# about a file that is perfectly fine, which is precisely what happened while
# this installer was being built: the numbers had been taken from grep, which
# counts matching LINES, while the check uses str.count, which counts
# OCCURRENCES. The invariant cannot be miscounted.
MARKERS = [
    "syncPullBrief",
    "paintTodayFive",
    "repaintBrief",
    "FORGE_TZ",
    "pimgPush",
    "MISMATCH",
    "rgba(200,60,60,0.16)",
    "dedupe_events",
    "SPORTS_ICS_FEEDS",
    "espn_get",
    "clean_title",
]

# What this patch itself must have produced. Every count below is DERIVED
# from the tested build at build time, never typed by hand -- two of them had
# been typed wrong (a definition line contains its own function name, and grep
# counts lines where str.count counts occurrences) and each wrongly blocked a
# perfectly good patch. The post-image SHA above is the real guarantee; these
# are here so a human can read what changed.
POST_CHECKS = [
    ('America-Vancouver/3178874,3178962/0', 0, 'old Ringette URL removed'),
    ('America-Vancouver/5063785,5136202/0', 1, 'new Ringette URL present'),
    ('ICS_ALWAYS_FUTURE', 3, 'always-future list wired in'),
    ('def ics_unfold', 1, 'unfold helper defined'),
    ('def ics_text_unescape', 1, 'unescape helper defined'),
    ('def format_ics_summary', 1, 'summary formatter defined'),
    ('clean_title(line[8:])', 0, 'old bare-SUMMARY parse replaced'),
    ('raw = ics_unfold(raw)', 2, 'both parsers unfold'),
    ('format_ics_summary(feed_name,', 3, 'both parsers use the formatter'),
    ('_future += 1', 1, 'future counter present'),
    ('carries NO events at all', 1, 'empty-feed banner present'),
    ('NONE in the future', 1, 'expired-feed banner present'),
]


def die(msg):
    print("")
    print("ABORTED. Nothing was changed.")
    for line in msg.split("\n"):
        print("  " + line)
    sys.exit(1)


def main():
    print("forge_ringette_feed_20261002")
    print("Ringette relink, readable titles, dead-feed banner")
    print("")

    if not os.path.exists(TARGET):
        die("%s is not in this directory.\n"
            "cd into the repo clone and run it from there." % TARGET)

    original = io.open(TARGET, encoding="utf-8").read()
    got = hashlib.sha256(original.encode("utf-8")).hexdigest()
    print("  %s found, %d bytes" % (TARGET, len(original.encode("utf-8"))))
    print("  sha256   %s" % got)
    print("  expected %s" % PRE_SHA)
    if got != PRE_SHA:
        die("Pre-image mismatch. This installer was built against a different\n"
            "version of %s. Do NOT force it.\n"
            "Re-pull the repo and try again; if the hash still differs, the\n"
            "installer must be rebuilt against the current file." % TARGET)
    print("  pre-image OK")
    print("")

    try:
        edits = json.loads(gzip.decompress(base64.b64decode(PAYLOAD)).decode("utf-8"))
    except Exception as exc:
        die("Payload failed to decode (%s: %s).\n"
            "The paste was almost certainly truncated." % (type(exc).__name__, exc))

    if len(edits) != N_EDITS:
        die("Payload carries %d edits, expected %d. Truncated paste."
            % (len(edits), N_EDITS))

    patched = original
    for i, pair in enumerate(edits):
        old, new = pair[0], pair[1]
        n = patched.count(old)
        if n != 1:
            die("Edit %d of %d matched %d times, expected exactly 1."
                % (i + 1, len(edits), n))
        patched = patched.replace(old, new, 1)
        print("  edit %d of %d applied" % (i + 1, len(edits)))
    print("")

    out_sha = hashlib.sha256(patched.encode("utf-8")).hexdigest()
    print("  post-image sha256 %s" % out_sha)
    print("  expected          %s" % POST_SHA)
    if out_sha != POST_SHA:
        die("Post-image mismatch. The result is not the tested build.")
    print("  post-image OK")

    try:
        ast.parse(patched)
    except SyntaxError as exc:
        die("Patched file does not parse: %s" % exc)
    print("  ast.parse OK")

    bad = []
    for needle in MARKERS:
        before = original.count(needle)
        after = patched.count(needle)
        if before != after:
            bad.append("%s: %d before, %d after" % (needle, before, after))
    if bad:
        die("Earlier work would be damaged:\n" + "\n".join(bad))
    print("  %d earlier-work markers unchanged" % len(MARKERS))

    for needle, count, label in POST_CHECKS:
        n = patched.count(needle)
        if n != count:
            die("Post-check failed: %s\n(%s found %d, expected %d)"
                % (label, needle, n, count))
    print("  %d post-checks OK" % len(POST_CHECKS))
    print("")

    if os.path.exists(BACKUP):
        die("%s already exists, so this installer has probably run before.\n"
            "Nothing was changed." % BACKUP)

    io.open(BACKUP, "w", encoding="utf-8").write(original)
    print("  backup written: %s" % BACKUP)

    io.open(TARGET, "w", encoding="utf-8").write(patched)
    verify = hashlib.sha256(io.open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest()
    if verify != POST_SHA:
        io.open(TARGET, "w", encoding="utf-8").write(original)
        die("Write-back verification failed.\n"
            "%s was restored to its original contents." % TARGET)
    print("  %s written and re-verified on disk" % TARGET)
    print("")
    print("DONE.")
    print("forge_actions.py is the generator, so this needs a WORKFLOW RUN after")
    print("the commit is pushed, or the brief keeps rebuilding from the old code.")
    print("Rollback if ever needed: %s sits beside the file." % BACKUP)


if __name__ == "__main__":
    main()

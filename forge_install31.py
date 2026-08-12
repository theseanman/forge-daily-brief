#!/usr/bin/env python3
"""
install31 — LIVE OR OVER on the Forge Daily Brief.

Adds a third labelled sub-section to install27's cue block: the monitor-vs-present
rule. Static, no rotation, no tick, no count, no streak, no storage key, no
Cloudflare paste. Text only.

TARGET   forge_actions.py   (THE GENERATOR — a workflow run is required after push)
MUST RUN AFTER install27. Aborts if install27's cue block is absent.

Run from the repo root:
    cd ~/Desktop/forge-daily-brief
    python3 forge_install31.py
"""

import ast
import hashlib
import os
import sys

TARGET = "forge_actions.py"
PRE_SHA = "e5b0a7e542e3280beee4c995b577f46601a6a65a3340a7b73e789cde93c782d7"
MARKER = "install31"

# The block being inserted. Deliberate constraints, each checked below:
#   - NO literal { or } — forge_actions.py holds the brief in a Python f-string,
#     so any literal brace would have to be doubled. Avoiding them entirely is safer.
#   - NO apostrophes — these are single-quoted JS string literals. Entities only.
#   - NO "high stakes" / "major decision" — install27 deliberately banned the stakes
#     axis from this block. This text says the opposite thing without the phrase.
NEW_BLOCK = (
    "      '<div style=\"font-size:10px; letter-spacing:0.16em; color:#1a5fa8; font-weight:700; margin-top:13px; margin-bottom:4px;\">LIVE OR OVER</div>' +\n"
    "      '<div style=\"font-size:12px; line-height:1.55;\">' +\n"
    "        '<strong style=\"color:#1a5fa8;\">Live</strong> &mdash; someone is in front of me, right now. A person talking. My daughters in the room. Attention goes outward: their face, their words. Not onto how I am doing.<br>' +\n"
    "        '<strong style=\"color:#1a5fa8;\">Over</strong> &mdash; it is finished. Driving home. Sunday. Kids asleep. Where could I have improved? The time to evaluate my performance is after the fact, not during, according to the experts.<br>' +\n"
    "        '<strong style=\"color:#1a5fa8;\">Never review while it is live.</strong> The more the moment matters, the more true this is &mdash; that is when monitoring does the most damage, not an exception to the rule.' +\n"
    "      '</div>' +\n"
)

BANNED_IN_REGION = ("high stakes", "high-stakes", "major decision")


def die(msg):
    print("ABORT: " + msg)
    print("Nothing was written. " + TARGET + " is unchanged.")
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die(TARGET + " not found. Run this from the repo root (cd ~/Desktop/forge-daily-brief).")

    src = open(TARGET, encoding="utf-8").read()
    sha = hashlib.sha256(src.encode("utf-8")).hexdigest()

    if MARKER in src:
        print("Already applied — " + MARKER + " marker is present. Nothing to do.")
        sys.exit(0)

    if sha != PRE_SHA:
        die(
            "pre-image mismatch.\n"
            "  expected " + PRE_SHA + "\n"
            "  found    " + sha + "\n"
            "The deployed file has changed since this installer was built. Do not force it."
        )

    # --- ordering guard: install27's cue block must exist ---
    if "install27" not in src:
        die("install27 marker absent — the cue block this patches does not exist yet.")
    for required in ("pfCue()", "DECIDING", "3 seconds", "7 breaths"):
        if required not in src:
            die("install27's cue block is incomplete (missing " + required + ").")

    # --- build the anchor programmatically; never typed by eye ---
    hag = "Seven breaths is from the Hagakure"
    if src.count(hag) != 1:
        die("expected exactly 1 Hagakure caveat, found " + str(src.count(hag)) + ".")
    hi = src.find(hag)
    line_start = src.rfind("\n", 0, hi) + 1
    close = src.find("'</div>';", hi)
    if close == -1:
        die("could not find the cue block terminator after the Hagakure caveat.")
    anchor = src[line_start:close + len("'</div>';")]
    if src.count(anchor) != 1:
        die("anchor is not unique (" + str(src.count(anchor)) + " matches).")

    hag_line = src[line_start:src.find("\n", hi) + 1]
    tail = anchor[len(hag_line):]          # the closing "    '</div>';"
    replacement = hag_line + NEW_BLOCK + tail

    # --- content guards, SCOPED TO THE INSERTED REGION ONLY ---
    low = NEW_BLOCK.lower()
    for bad in BANNED_IN_REGION:
        if bad in low:
            die("inserted text contains the banned stakes phrase '" + bad + "'.")
    if "{" in NEW_BLOCK or "}" in NEW_BLOCK:
        die("inserted text contains a literal brace — it would break the f-string.")
    # apostrophes: only the JS string delimiters may be single quotes.
    for ln in NEW_BLOCK.splitlines():
        body = ln.strip()
        if body.endswith("+"):
            body = body[:-1].strip()
        if not (body.startswith("'") and body.endswith("'")):
            die("inserted line is not a well-formed single-quoted JS literal: " + ln)
        if "'" in body[1:-1]:
            die("inserted line has an unescaped apostrophe inside the literal: " + ln)

    out = src.replace(anchor, replacement, 1)

    # --- post-conditions before anything touches disk ---
    if out == src:
        die("replacement produced no change.")
    if "LIVE OR OVER" not in out:
        die("post-check: LIVE OR OVER absent from the result.")
    if out.count("LIVE OR OVER") != 1:
        die("post-check: LIVE OR OVER appears " + str(out.count("LIVE OR OVER")) + " times.")
    if out.count("pfCue()") != src.count("pfCue()"):
        die("post-check: the daily cue was disturbed.")
    for keep in ("3 seconds", "7 breaths", "Sunday</strong>", hag, "pfReps()", "paintPractice", "pullPractice"):
        if out.count(keep) != src.count(keep):
            die("post-check: existing content changed unexpectedly (" + keep + ").")
    if out.count("'") % 2 != src.count("'") % 2:
        die("post-check: single-quote parity changed — a JS literal is unbalanced.")
    try:
        ast.parse(out)
    except SyntaxError as e:
        die("post-check: patched file is not valid Python — " + str(e))

    out = out.replace(
        "    /* install27: today's cue + the decision tiers. No tick, nothing to complete. */",
        "    /* install27: today's cue + the decision tiers. install31: LIVE OR OVER. */",
        1,
    )
    if MARKER not in out:
        die("post-check: marker comment was not written.")

    bak = TARGET + "." + MARKER + ".bak"
    with open(bak, "w", encoding="utf-8") as f:
        f.write(src)
    tmp = TARGET + ".tmp." + MARKER
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    os.replace(tmp, TARGET)

    post = hashlib.sha256(open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest()
    print("OK  " + TARGET + " patched.")
    print("    backup   " + bak)
    print("    pre-sha  " + PRE_SHA)
    print("    post-sha " + post)
    print("")
    print("This is the GENERATOR. Commit, push, then TRIGGER THE WORKFLOW.")
    print("Never hand-edit index.html.")


if __name__ == "__main__":
    main()

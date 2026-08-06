#!/usr/bin/env python3
"""
install27 - cue block + three-tier decision rule on the brief (forge_actions.py)

★ THIS SUPERSEDES install26. DELETE forge_install26.py. Do not run both.
   install27 targets install24's post-image directly, so if install26 was already
   applied this installer will refuse on the pre-image check (fails closed).

MUST RUN AFTER install24.

Changes from the install26 draft, all at Sean's direction:
  - all 7 cue strings rewritten for explicitness
  - NO SUNSET. Sean's reason beat Claude's: silent removal during a bad month is a
    real failure mode and he might not notice it gone. He can ask for it to be pulled.
  - blue #1a5fa8 rather than amber. NOTE: Claude had claimed blue would look bolted
    on here; that was wrong. The brief already carries a blue-gradient card (the
    Identityless Protocol), so blue is consistent with the existing design.
  - adds the THREE-TIER DECISION RULE

★ THE THREE TIERS, and why the axis is not "stakes":
   Sean first asked for "7 breaths for major/high-stakes, 3 seconds for minor".
   Claude flagged that this deletes the Sunday tier from install13 - and the Sunday
   tier exists precisely because Sean's failure mode is NOT hesitation, it is fast
   action on new projects to escape the important ones. Labelling the middle tier
   "high stakes" hands that failure mode a 30-second green light. Sean agreed to the
   loop-opening axis instead. DO NOT quietly revert this to a stakes-based split.

The seven-breaths line is genuinely from Hagakure (compiled from Yamamoto Tsunetomo,
1709-1716). It is a maxim from one retainer's reflections written a century into
peacetime, NOT documented samurai practice - the brief says so in one muted line,
deliberately, so the claim stays honest where Sean reads it.

Fails closed: any anchor problem leaves the file byte-identical.
"""
import ast
import hashlib
import os
import shutil
import sys

TARGET = "forge_actions.py"
PRE_SHA = "287e555d2a7dcfe61a0e9a326ca75e8bab5a57a00e5715ddf45c3dd675742f0e"
BLUE = "#1a5fa8"

A1_OLD = """function pfReps() {{"""
A1_NEW = """var CUES = [
  'The first half-second after they start talking &mdash; your reaction either shows or gets swallowed. Swallowed reads as withholding.',
  'Nod when they land a point, not on a steady beat. Steady nodding reads as waiting for your turn.',
  'Does your face react while they are talking, or only while you are?',
  'Stop for half a beat before your most important word. The silence does more than volume.',
  'In relation to magnetism, warmth lands before competence. Do not lead with what you know.',
  'One follow-up question deeper than the answer required.',
  'Pay attention to the person, not to how you are performing.'
];
function pfCue() {{
  var d = new Date();
  var doy = Math.floor((d - new Date(d.getFullYear(), 0, 1)) / 86400000);
  return CUES[((doy % CUES.length) + CUES.length) % CUES.length];
}}
function pfReps() {{"""

A2_OLD = """        '<div class="t5-meta">' + pfReps() + ' today &middot; conversations you started</div>' +
      '</div>' +
    '</div>';
}}"""
A2_NEW = """        '<div class="t5-meta">' + pfReps() + ' today &middot; conversations you started</div>' +
      '</div>' +
    '</div>' +
    /* install27: today's cue + the decision tiers. No tick, nothing to complete. */
    '<div style="border-top:2px solid BLUEHEX; margin-top:10px; padding-top:10px;">' +
      '<div style="font-size:10px; letter-spacing:0.16em; color:BLUEHEX; font-weight:700; margin-bottom:3px;">TODAY&rsquo;S CUE</div>' +
      '<div style="font-size:13px; font-weight:600; line-height:1.45; margin-bottom:12px;">' + pfCue() + '</div>' +
      '<div style="font-size:10px; letter-spacing:0.16em; color:BLUEHEX; font-weight:700; margin-bottom:4px;">DECIDING</div>' +
      '<div style="font-size:12px; line-height:1.55;">' +
        '<strong style="color:BLUEHEX;">3 seconds</strong> &mdash; minor, everyday, nothing survives the night. Which room, what to say, put the phone down. Auditing it <em>is</em> the problem.<br>' +
        '<strong style="color:BLUEHEX;">7 breaths</strong> &mdash; consequential, already in front of you, cannot be deferred. A deadline, an offer, a trip. Stewing adds nothing: decide and move.<br>' +
        '<strong style="color:BLUEHEX;">Sunday</strong> &mdash; anything that opens a new loop or commits future time, however urgent it feels. Especially the ones you generated yourself.' +
      '</div>' +
      '<div style="font-size:10px; opacity:0.65; margin-top:7px; line-height:1.5;">Seven breaths is from the Hagakure, c.1710 &mdash; a maxim from one retainer&rsquo;s reflections, not documented samurai practice. Roughly 30&ndash;45 seconds.</div>' +
    '</div>';
}}""".replace("BLUEHEX", BLUE)

EDITS = [
    ("cues + pfCue helper", A1_OLD, A1_NEW),
    ("cue and decision block", A2_OLD, A2_NEW),
]

MARKERS = ["install27", "pfCue", "TODAY&rsquo;S CUE", "DECIDING",
           "7 breaths", "Sunday", "Hagakure", BLUE, "first half-second"]


def main():
    if not os.path.exists(TARGET):
        sys.exit("FAIL: %s not found. Run this from the repo root." % TARGET)

    original = open(TARGET, "r", encoding="utf-8").read()
    sha = hashlib.sha256(original.encode("utf-8")).hexdigest()

    if "install27" in original:
        print("Already applied (install27 marker present). Nothing written.")
        return

    if "CUE_SUNSET" in original or "install26" in original:
        sys.exit("FAIL: install26 has been applied. install27 SUPERSEDES it and the two\n"
                 "cannot coexist. Restore forge_actions.py.install26.bak over the target,\n"
                 "then run this again. File not modified.")

    if "pfReps" not in original:
        sys.exit("FAIL: install24 has not been applied. Run forge_install24.py first.\n"
                 "File not modified.")

    if sha != PRE_SHA:
        sys.exit(
            "FAIL: pre-image mismatch.\n  expected %s\n  found    %s\n"
            "This must run on the install24 post-image.\n"
            "File not modified." % (PRE_SHA, sha)
        )

    text = original
    for name, old, new in EDITS:
        count = text.count(old)
        if count != 1:
            sys.exit("FAIL: anchor '%s' matched %d times, need exactly 1. "
                     "File not modified." % (name, count))
        text = text.replace(old, new, 1)
        print("  ok  %s" % name)

    for m in MARKERS:
        if m not in text:
            sys.exit("FAIL: marker '%s' missing after edit. File not modified." % m)

    block = text.split("TODAY&rsquo;S CUE")[1].split("Hagakure")[0]
    if "high stakes" in block or "high-stakes" in block or "major decision" in block:
        sys.exit("FAIL: a stakes-based tier label leaked into the cue block. The axis is\n"
                 "loop-opening, not stakes - see the header comment. File not modified.")

    try:
        ast.parse(text)
    except SyntaxError as e:
        sys.exit("FAIL: ast.parse rejected the result at line %s: %s\n"
                 "File not modified." % (e.lineno, e.msg))

    shutil.copy2(TARGET, TARGET + ".install27.bak")
    open(TARGET, "w", encoding="utf-8").write(text)

    post = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print("\nWrote %s" % TARGET)
    print("  pre  %s" % sha)
    print("  post %s" % post)
    print("  backup: %s.install27.bak" % TARGET)
    print("\nGENERATOR patch - needs a workflow run.")
    print("No sunset: the cue block renders indefinitely until you ask for it out.")


if __name__ == "__main__":
    main()

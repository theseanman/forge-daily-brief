#!/usr/bin/env python3
"""
forge_tally_body_items.py  -  add four body-awareness tally items to forge-tally.html.

New items: shoulders_back, pause_mouthfuls, breath_speak, feet_ground
New section: BODY (physical awareness cues), rendered in its own container.
Added to PROTO_ITEMS so they sync via forge-sync. The debrief's PROTO_ITEMS
will need a matching update separately (flagged, not done here).

Hand-maintained file -> deploys on push, NO workflow run.
Anchor-based (not SHA-gated, same reason as the last installer).
"""
import sys, os, datetime

TARGET = "forge-tally.html"

# 1. Add to PROTO_ITEMS
A_OLD = "var PROTO_ITEMS = ['boundary','warrior','opportunity','pause_speak','pause_reach',\n                   'pause_decide','pause_move','slow','fine','cal_ai'];"
A_NEW = "var PROTO_ITEMS = ['boundary','warrior','opportunity','pause_speak','pause_reach',\n                   'pause_decide','pause_move','slow','fine','cal_ai',\n                   'shoulders_back','pause_mouthfuls','breath_speak','feet_ground'];"

# 2. Add TILES.body after TILES.calai
B_OLD = """  calai: [
    { k:'cal_ai', icon:'\\uD83D\\uDCF1', label:'Meal logged', sub:'One tap per meal photographed' }
  ]
};"""
B_NEW = """  calai: [
    { k:'cal_ai', icon:'\\uD83D\\uDCF1', label:'Meal logged', sub:'One tap per meal photographed' }
  ],
  body: [
    { k:'shoulders_back',   icon:'\\uD83E\\uDDD8', label:'Shoulders Back',           sub:'Noticed and corrected posture' },
    { k:'pause_mouthfuls',  icon:'\\uD83C\\uDF7D\\uFE0F',  label:'Pause Between Mouthfuls', sub:'Put down the fork, then chew' },
    { k:'breath_speak',     icon:'\\uD83D\\uDCA8', label:'Breath Before Speaking',   sub:'One breath before the words' },
    { k:'feet_ground',      icon:'\\uD83E\\uDDB6', label:'Feet on the Ground',       sub:'Noticed feet, reset from there' }
  ]
};"""

# 3. Add HTML section before the presence note
C_OLD = """  <div class="note">
    Presence is not here on purpose."""
C_NEW = """  <div class="sec sec-body">
    <div class="sec-head" style="color:var(--body);">BODY</div>
    <div class="sec-sub" style="color:var(--body);">Notice the body. It knows before you do.</div>
    <div id="body-tiles"></div>
  </div>

  <div class="note">
    Presence is not here on purpose."""

# 4. Add buildTiles line for body
D_OLD = "  document.getElementById('calai-tiles').innerHTML   = TILES.calai.map(tileHtml).join('');"
D_NEW = "  document.getElementById('calai-tiles').innerHTML   = TILES.calai.map(tileHtml).join('');\n  document.getElementById('body-tiles').innerHTML    = TILES.body.map(tileHtml).join('');"

# 5. Add --body CSS var
E_OLD = "    --terrain: #4a9de8; --tempo: #e0a854; --calai: #4ae8a0;"
E_NEW = "    --terrain: #4a9de8; --tempo: #e0a854; --calai: #4ae8a0; --body: #8a9ad0;"

def die(m): print("ABORT:", m); sys.exit(1)

def main():
    if not os.path.exists(TARGET):
        die(f"{TARGET} not found - run from ~/Desktop/forge-daily-brief on gh-pages")
    orig = open(TARGET, encoding="utf-8").read()

    if 'shoulders_back' in orig:
        die("already patched (shoulders_back already present) - nothing to do")

    for nm, old in [("A",A_OLD),("B",B_OLD),("C",C_OLD),("D",D_OLD),("E",E_OLD)]:
        c = orig.count(old)
        if c != 1: die(f"anchor {nm} found {c}x (expected 1) - refusing to guess")

    new = orig.replace(A_OLD,A_NEW).replace(B_OLD,B_NEW).replace(C_OLD,C_NEW).replace(D_OLD,D_NEW).replace(E_OLD,E_NEW)

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{TARGET}.bodybak-{stamp}"
    open(bak,"w",encoding="utf-8").write(orig)
    open(TARGET,"w",encoding="utf-8").write(new)

    def restore(why):
        open(TARGET,"w",encoding="utf-8").write(orig)
        die(f"post-check failed ({why}) - {TARGET} restored, backup at {bak}")

    for m in ("shoulders_back","pause_mouthfuls","breath_speak","feet_ground","body-tiles","--body:"):
        if m not in new: restore(f"marker missing: {m}")
    if new.count("PROTO_ITEMS") < 3: restore("PROTO_ITEMS references look wrong")

    print("OK  forge-tally.html patched — four body-awareness items added.")
    print("    backup :", bak)
    print("    new items: shoulders_back, pause_mouthfuls, breath_speak, feet_ground")
    print("    new section: BODY (indigo, between Cal AI and the Presence note)")
    print("    bytes  :", len(orig.encode()), "->", len(new.encode()))
    print("\nNext: git pull --rebase ; git add forge-tally.html forge_tally_body_items.py ; commit ; push. NO workflow run.")
    print("NOTE: the debrief's PROTO_ITEMS needs a matching update separately so counts sync fully.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
forge_daytag_aug15.py  -  add a per-day CONTEXT TAG to the evening debrief.

WHY: context (travel / vacation / sick / night out) can only be captured on the day
it happens — it can't be reconstructed later. The analysis surface (a later build)
reads the daily-log record directly, so this stores tag on the record. It does NOT
touch the CSV export (which has a separate, pre-existing column-misalignment bug).

WHAT (patches forge-evening-debrief.html only — hand-maintained, NO workflow run):
  1. A "Day context" button row in the "01 · Day feel" step: Normal / Travel /
     Vacation / Sick / Night out. Its own .tag-btn class + selectTag() so it can
     never interfere with the mood buttons (which share #step-0).
  2. selectedTag defaults to 'normal'; collectDaily() writes tag onto the record.

SAFETY: refuses unless PRE hash matches; backs up first; restores on any post-check
failure; second run refuses (PRE hash no longer matches).
"""
import hashlib, sys, os, subprocess, datetime

TARGET  = "forge-evening-debrief.html"
PRE_SHA = "7fac57bd3401df1ea6234115f7168cec5d108065412f92c2402b45739ecfd0f7"

# 1. CSS — append a .tag-btn style after the existing .mood-btn.selected rule
A_OLD = "  .mood-btn.selected { background: rgba(74,157,232,0.15); border-color: var(--blue); color: var(--blue); font-weight: 600; }"
A_NEW = (
"  .mood-btn.selected { background: rgba(74,157,232,0.15); border-color: var(--blue); color: var(--blue); font-weight: 600; }\n"
"  .tag-btn { border: 1px solid var(--border); border-radius: var(--radius); padding: 8px 14px; background: transparent; color: var(--muted); font-size: 13px; cursor: pointer; font-family: inherit; transition: all 0.15s; }\n"
"  .tag-btn.selected { background: rgba(224,168,84,0.15); border-color: #e0a854; color: #e0a854; font-weight: 600; }"
)

# 2. HTML — insert the tag row before the day-note field
B_OLD = (
'      <div class="field">\n'
'        <div class="field-label">One-liner (optional)</div>\n'
'        <textarea id="day-note" placeholder="e.g. Got a lot done but the afternoon dragged..."></textarea>'
)
B_NEW = (
'      <div class="field-label" style="margin-top:4px;">Day context</div>\n'
'      <div class="mood-row" id="tag-row">\n'
'        <button class="tag-btn selected" onclick="selectTag(this,\'normal\')">Normal</button>\n'
'        <button class="tag-btn" onclick="selectTag(this,\'travel\')">Travel</button>\n'
'        <button class="tag-btn" onclick="selectTag(this,\'vacation\')">Vacation</button>\n'
'        <button class="tag-btn" onclick="selectTag(this,\'sick\')">Sick</button>\n'
'        <button class="tag-btn" onclick="selectTag(this,\'night out\')">Night out</button>\n'
'      </div>\n'
'      <div class="field">\n'
'        <div class="field-label">One-liner (optional)</div>\n'
'        <textarea id="day-note" placeholder="e.g. Got a lot done but the afternoon dragged..."></textarea>'
)

# 3. JS declaration
C_OLD = "let selectedMood = '';"
C_NEW = "let selectedMood = '';\nlet selectedTag = 'normal';"

# 4. selectTag function — add right after selectMood's closing brace
D_OLD = (
"function selectMood(btn, val) {\n"
"  selectedMood = val;\n"
"  document.querySelectorAll('#step-0 .mood-btn').forEach(b => b.classList.toggle('selected', b === btn));\n"
"}"
)
D_NEW = (
"function selectMood(btn, val) {\n"
"  selectedMood = val;\n"
"  document.querySelectorAll('#step-0 .mood-btn').forEach(b => b.classList.toggle('selected', b === btn));\n"
"}\n"
"function selectTag(btn, val) {\n"
"  selectedTag = val;\n"
"  document.querySelectorAll('#tag-row .tag-btn').forEach(b => b.classList.toggle('selected', b === btn));\n"
"}"
)

# 5. collectDaily — write tag onto the record
E_OLD = "    mood: selectedMood || '',"
E_NEW = "    mood: selectedMood || '',\n    tag: selectedTag || 'normal',"

def die(m): print("ABORT:", m); sys.exit(1)

def main():
    if not os.path.exists(TARGET): die(f"{TARGET} not found - run from ~/Desktop/forge-daily-brief on gh-pages")
    orig = open(TARGET, encoding="utf-8").read()
    got = hashlib.sha256(orig.encode()).hexdigest()
    if got != PRE_SHA:
        die(f"PRE hash mismatch.\n  expected {PRE_SHA}\n  got      {got}\nTargets the current live debrief only.")
    for nm, old in [("A",A_OLD),("B",B_OLD),("C",C_OLD),("D",D_OLD),("E",E_OLD)]:
        c = orig.count(old)
        if c != 1: die(f"anchor {nm} found {c}x (expected 1) - refusing to guess")
    new = (orig.replace(A_OLD,A_NEW).replace(B_OLD,B_NEW).replace(C_OLD,C_NEW)
              .replace(D_OLD,D_NEW).replace(E_OLD,E_NEW))

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{TARGET}.daytagbak-{stamp}"
    open(bak,"w",encoding="utf-8").write(orig)
    open(TARGET,"w",encoding="utf-8").write(new)

    def restore(why):
        open(TARGET,"w",encoding="utf-8").write(orig)
        die(f"post-check failed ({why}) - {TARGET} restored, backup at {bak}")

    for marker in ("function selectTag(", "id=\"tag-row\"", "tag: selectedTag || 'normal',", ".tag-btn.selected"):
        if marker not in new: restore(f"marker missing: {marker}")
    # selectMood must be UNCHANGED (tag must not have altered it)
    if new.count("document.querySelectorAll('#step-0 .mood-btn')") != 1: restore("selectMood selector changed unexpectedly")
    if new.count("class=\"tag-btn") != 5: restore("expected 5 tag buttons")

    post = hashlib.sha256(new.encode()).hexdigest()
    print("OK  forge-evening-debrief.html patched.")
    print("    backup :", bak)
    print("    PRE    :", PRE_SHA)
    print("    POST   :", post)
    print("    bytes  :", len(orig.encode()), "->", len(new.encode()))
    print("\nNext: git pull --rebase ; stage the debrief + this installer ; commit ; push. NO workflow run.")

if __name__ == "__main__":
    main()

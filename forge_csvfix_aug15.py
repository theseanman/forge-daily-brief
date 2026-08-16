#!/usr/bin/env python3
"""
forge_csvfix_aug15.py  -  fix the misaligned CSV export in the evening debrief,
and add the new day-context 'tag' column.

THE BUG: CSV_COLS declares 46 columns but each data row emitted only 34 values —
the 12 protocol columns (boundary..tempo_min) were in the header but never written,
so every value from 'weight' rightward sat under the wrong heading. The data is on
the record as rec.protocol; it just wasn't emitted.

THE FIX (patches forge-evening-debrief.html only — hand-maintained, NO workflow run):
  1. Emit the 12 protocol values (p.boundary..p.tempo_min) in the row, in header order,
     between stress and weight. Header and rows now both = 46.
  2. Add the 'tag' column (header + row) so the day-context tag exports too → 47/47.

SAFETY: refuses unless PRE hash matches; backs up first; a post-check asserts the
header and every row have equal column counts before it will keep the change;
restores on any failure; second run refuses.
"""
import hashlib, sys, os, subprocess, datetime, re

TARGET  = "forge-evening-debrief.html"
PRE_SHA = "f9f34a96f171e8f5ba5f902636ff0305cb830eaf7c495c922c7fb1fa1cd5cc55"

# 1. destructuring line: add p = r.protocol
A_OLD = "    var e1 = (r.esp && r.esp[0]) || {};"
A_NEW = "    var e1 = (r.esp && r.esp[0]) || {}, p = r.protocol || {};"

# 2. row head: insert the 12 protocol values after h.stress
B_OLD = ("      k, r.mood, h.sleep_score, h.sleep_dur, h.energy, h.health, h.stress,\n"
         "      h.weight, h.body_fat, t.total, t.done, t.keySet, t.keyDone,")
B_NEW = ("      k, r.mood, h.sleep_score, h.sleep_dur, h.energy, h.health, h.stress,\n"
         "      p.boundary, p.warrior, p.opportunity, p.pause_speak, p.pause_reach, p.pause_decide, p.pause_move, p.slow, p.fine, p.cal_ai, p.terrain_min, p.tempo_min,\n"
         "      h.weight, h.body_fat, t.total, t.done, t.keySet, t.keyDone,")

# 3. header: add 'tag'
C_OLD = "  'win','miss','carry','note'];"
C_NEW = "  'win','miss','carry','note','tag'];"

# 4. row tail: add r.tag
D_OLD = "      r.win, r.miss, r.carry, r.note"
D_NEW = "      r.win, r.miss, r.carry, r.note, r.tag"

def die(m): print("ABORT:", m); sys.exit(1)

def main():
    if not os.path.exists(TARGET): die(f"{TARGET} not found - run from ~/Desktop/forge-daily-brief on gh-pages")
    orig = open(TARGET, encoding="utf-8").read()
    got = hashlib.sha256(orig.encode()).hexdigest()
    if got != PRE_SHA:
        die(f"PRE hash mismatch.\n  expected {PRE_SHA}\n  got      {got}\n"
            "This targets the current live debrief (post day-tag). If you have not deployed the day-tag installer yet, do that first.")
    for nm, old in [("A",A_OLD),("B",B_OLD),("C",C_OLD),("D",D_OLD)]:
        c = orig.count(old)
        if c != 1: die(f"anchor {nm} found {c}x (expected 1) - refusing to guess")
    new = orig.replace(A_OLD,A_NEW).replace(B_OLD,B_NEW).replace(C_OLD,C_NEW).replace(D_OLD,D_NEW)

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{TARGET}.csvfixbak-{stamp}"
    open(bak,"w",encoding="utf-8").write(orig)
    open(TARGET,"w",encoding="utf-8").write(new)

    def restore(why):
        open(TARGET,"w",encoding="utf-8").write(orig)
        die(f"post-check failed ({why}) - {TARGET} restored, backup at {bak}")

    # header/row column-count parity check
    mh = re.search(r"var CSV_COLS = \[(.*?)\];", new, re.S)
    ncols = len([c for c in mh.group(1).split(',') if c.strip()])
    mb = re.search(r"rows\.push\(\[(.*?)\]\.map\(csvCell\)", new, re.S)
    row = mb.group(1); depth=0; cur=''; cells=[]
    for ch in row:
        if ch in '([{': depth+=1
        elif ch in ')]}': depth-=1
        if ch==',' and depth==0: cells.append(cur.strip()); cur=''
        else: cur+=ch
    if cur.strip(): cells.append(cur.strip())
    nrow = len([c for c in cells if c])
    if ncols != nrow: restore(f"header {ncols} != row {nrow} columns")
    if ncols != 47: restore(f"expected 47 columns, got {ncols}")
    if "p = r.protocol || {}" not in new: restore("protocol destructure missing")

    post = hashlib.sha256(new.encode()).hexdigest()
    print("OK  forge-evening-debrief.html patched.")
    print(f"    CSV columns now aligned: header {ncols} == row {nrow}")
    print("    backup :", bak)
    print("    PRE    :", PRE_SHA)
    print("    POST   :", post)
    print("    bytes  :", len(orig.encode()), "->", len(new.encode()))
    print("\nNext: git pull --rebase ; stage the debrief + this installer ; commit ; push. NO workflow run.")

if __name__ == "__main__":
    main()

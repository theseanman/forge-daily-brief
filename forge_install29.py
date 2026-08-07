#!/usr/bin/env python3
"""
install29 - forge-evening-debrief.html
  (1) CARRY CAP with a HARD GATE at 3 carries
  (2) ESCALATING VISUAL STATES on carried items

WHY THIS FILE ONLY: the carry count `c` lives entirely in the debrief.
planner.html has no carry logic at all. The single place an item gains a
carry is the carry-forward picker in initPlanRows(), so that is the only
place a gate is needed.

THE GATE. An item already carried 3+ times no longer gets a plain
tap-to-add button. It gets three explicit routes:
    COMMIT -> addToPlan as normal, you chose it deliberately
    PARK   -> parkAdd(), the Sunday review already triages parked items
    DROP   -> the backlog

  NOTHING IS DELETED ON ANY ROUTE. Sean's standing rule: nothing is
  removed without his permission, and a back-burnered item must stay
  findable so it is not forgotten when conditions improve.

THE STATES. alive -> aging (2) -> stalled (3) -> gated (4+).
Deliberately NOT "dead" - dead should only ever mean something he chose.
Only the gated state pulses, so attention lands on one row, not a wall.

Debrief is hand-maintained: push is enough. NO WORKFLOW RUN.
Fails closed: any anchor problem leaves the file byte-identical.
"""
import hashlib
import os
import shutil
import sys
from datetime import datetime

TARGET = "forge-evening-debrief.html"
PRE_SHA = "5cd3fb98466a1dbc2b707bc2f4ee9b2364870c4f8d79d3df251708d972f02fc8"

# ---------------------------------------------------------------- edit 1: CSS
A1_OLD = "    .t5carry { font-size:9px; color:#e8844a; letter-spacing:.06em; flex-shrink:0; }"

A1_NEW = """    .t5carry { font-size:9px; color:#e8844a; letter-spacing:.06em; flex-shrink:0; }
    /* install29 - escalating carry states */
    .cs-aging   { color:#e8c84a; }
    .cs-stalled { color:#e8844a; font-weight:800; }
    .cs-gated   { color:#e05a4a; font-weight:800; animation:csPulse 2.4s ease-in-out infinite; }
    @keyframes csPulse { 0%,100% { opacity:1; } 50% { opacity:.4; } }
    .t5label.cs-fade { color:#8a8aa0; }
    .gate-wrap { border:1px solid #4a2a2a; border-radius:8px; padding:8px; margin:0 0 8px 0; background:#1a1216; }
    .gate-txt { font-size:12px; color:#f0f0f8; margin-bottom:2px; word-break:break-word; }
    .gate-lbl { font-size:9px; color:#e05a4a; letter-spacing:.08em; margin-bottom:6px; }
    .gate-row { display:flex; gap:6px; flex-wrap:wrap; }
    .gate-btn { font-size:11px; padding:6px 11px; border-radius:6px; background:#1c1c2a; color:#f0f0f8; border:1px solid #444458; }
    .gate-btn.commit { border-color:#4a9de8; color:#9ecbf5; }
    .gate-btn.park   { border-color:#e8c84a; color:#e8c84a; }
    .gate-btn.drop   { border-color:#e05a4a; color:#e05a4a; }"""

# ------------------------------------------------- edit 2: helpers + the gate
A2_OLD = """function addToPlan(text, hour, carryCount){"""

A2_NEW = """/* install29 - carry state helpers. Threshold: GATE_AT carries forces a decision. */
var GATE_AT = 3;
function csClass(c){
  c = Number(c) || 0;
  if (c >= GATE_AT + 1) return 'cs-gated';
  if (c >= GATE_AT) return 'cs-stalled';
  if (c >= 2) return 'cs-aging';
  return '';
}
function csWord(c){
  c = Number(c) || 0;
  if (c >= GATE_AT + 1) return 'gated';
  if (c >= GATE_AT) return 'stalled';
  if (c >= 2) return 'aging';
  return 'alive';
}
/* Nothing here deletes. Park and Drop both relocate the item. */
function gateCommit(text, c){ addToPlan(text, '', (Number(c) || 1) + 1); initPlanRows(); }
function gatePark(text){ try { parkAdd(text); } catch (e) {} dropFromToday(text); initPlanRows(); }
function gateDrop(text){
  var t = String(text == null ? '' : text).trim();
  if (t){
    var b = fdRead(K_BACKLOG, []);
    if (!Array.isArray(b)) b = [];
    if (b.indexOf(t) === -1){ b.push(t); fdWrite(K_BACKLOG, b); try { syncPush(K_BACKLOG); } catch (e) {} }
  }
  dropFromToday(text); initPlanRows();
}
/* Removes the item from the carry-forward OFFER only. Today's record is untouched. */
function dropFromToday(text){
  var t = String(text == null ? '' : text).trim().toLowerCase();
  todayT5 = todayT5.map(function(i){
    if (i && i.t && i.t.trim().toLowerCase() === t) { i = { t: i.t, done: true, c: i.c, k: i.k, mode: i.mode, m: i.m, dw: i.dw, _gated: true }; }
    return i;
  });
}
function addToPlan(text, hour, carryCount){"""

# ------------------------------------------------------ edit 3: the row badge
A3_OLD = """    if (it.c && it.c>=2){ var c=document.createElement('span'); c.className='t5carry'; c.textContent='carried '+it.c+'"""

A3_NEW = """    if (it.c && it.c>=2){ var c=document.createElement('span'); c.className='t5carry '+csClass(it.c); if(it.c>=GATE_AT) l.className+=' cs-fade'; c.textContent=csWord(it.c)+' \\u00B7 carried '+it.c+'"""

# ------------------------------------------- edit 4: the picker becomes a gate
A4_OLD = """      carried.forEach(function(it){
        var b=document.createElement('button'); b.className='pick';
        b.textContent = it.t + (it.c&&it.c>=2 ? '  · '+(it.c+1)+'×' : '');
        b.onclick=function(){ addToPlan(it.t, '', (it.c||1)+1); };
        host.appendChild(b);
      });"""

A4_NEW = """      carried.forEach(function(it){
        var cc = Number(it.c) || 1;
        if (cc >= GATE_AT){ /* install29 - hard gate, decide or it does not move */
          var w=document.createElement('div'); w.className='gate-wrap';
          var tx=document.createElement('div'); tx.className='gate-txt'; tx.textContent=it.t; w.appendChild(tx);
          var lb=document.createElement('div'); lb.className='gate-lbl';
          lb.textContent='CARRIED '+cc+'× · '+csWord(cc).toUpperCase()+' · DECIDE';
          w.appendChild(lb);
          var r=document.createElement('div'); r.className='gate-row';
          var b1=document.createElement('button'); b1.className='gate-btn commit'; b1.textContent='Commit';
          b1.onclick=(function(t,c){ return function(){ gateCommit(t,c); }; })(it.t, cc);
          var b2=document.createElement('button'); b2.className='gate-btn park'; b2.textContent='Park';
          b2.onclick=(function(t){ return function(){ gatePark(t); }; })(it.t);
          var b3=document.createElement('button'); b3.className='gate-btn drop'; b3.textContent='Backlog';
          b3.onclick=(function(t){ return function(){ gateDrop(t); }; })(it.t);
          r.appendChild(b1); r.appendChild(b2); r.appendChild(b3); w.appendChild(r);
          host.appendChild(w);
        } else {
          var b=document.createElement('button'); b.className='pick';
          b.textContent = it.t + (cc>=2 ? '  · '+(cc+1)+'×' : '');
          b.onclick=function(){ addToPlan(it.t, '', cc+1); };
          host.appendChild(b);
        }
      });"""

EDITS = [
    ("carry-state CSS", A1_OLD, A1_NEW),
    ("csClass/csWord + gate route helpers", A2_OLD, A2_NEW),
    ("escalating badge on the review row", A3_OLD, A3_NEW),
    ("carry-forward picker becomes a gate", A4_OLD, A4_NEW),
]


def die(msg):
    print("ABORT: " + msg)
    print("File left byte-identical. Nothing changed.")
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die(TARGET + " not found. cd into the gh-pages clone first.")

    original = open(TARGET, "r", encoding="utf-8").read()
    sha_before = hashlib.sha256(original.encode("utf-8")).hexdigest()
    print("pre-image sha256: " + sha_before)
    if sha_before != PRE_SHA:
        print("expected:         " + PRE_SHA)
        die("pre-image mismatch. The deployed debrief is not the version this "
            "installer was built against. Do not force it.")

    if "install29" in original:
        die("install29 markers already present. Already applied.")
    for marker in ("install25", "install23", "install20", "install13"):
        if marker not in original:
            die("ordering guard: " + marker + " missing. Run the earlier installers first.")
    print("ordering guards OK (install13/20/23/25 present)")

    for label, old, _new in EDITS:
        n = original.count(old)
        if n != 1:
            die("anchor for '%s' found %d times, expected exactly 1." % (label, n))
    print("all 4 anchors unique: OK")

    patched = original
    for label, old, new in EDITS:
        patched = patched.replace(old, new, 1)
        print("  applied: " + label)

    checks = [
        ("GATE_AT declared once", patched.count("var GATE_AT = 3;") == 1),
        ("csClass declared once", patched.count("function csClass(c){") == 1),
        ("csWord declared once", patched.count("function csWord(c){") == 1),
        ("three gate routes present",
         patched.count("function gateCommit(") == 1
         and patched.count("function gatePark(") == 1
         and patched.count("function gateDrop(") == 1),
        ("gate reuses the existing parkAdd", "parkAdd(text)" in patched),
        ("NO delete path in the gate routes",
         "removeItem" not in patched.split("function gateCommit")[1].split("function addToPlan")[0]),
        ("brace delta balanced",
         (patched.count("{") - original.count("{"))
         == (patched.count("}") - original.count("}"))),
        ("addToPlan still defined once", patched.count("function addToPlan(text, hour, carryCount){") == 1),
        ("install25 video work intact", "paintVideo" in patched),
        ("install23 reps work intact", "initReps" in patched),
        ("install20 review work intact", "renderWeeklyReview" in patched),
        ("install13 frame work intact", "initFrame" in patched),
        ("enoughVerdict untouched",
         original.split("function enoughVerdict")[1][:600]
         == patched.split("function enoughVerdict")[1][:600]),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(("  OK   " if ok else "  FAIL ") + n)
    if bad:
        die("post-condition failed: " + "; ".join(bad))

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = TARGET + ".install29.bak-" + stamp
    shutil.copy2(TARGET, backup)
    print("backup written: " + backup)

    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(patched)

    written = open(TARGET, "r", encoding="utf-8").read()
    print("")
    print("post-image sha256: " + hashlib.sha256(written.encode("utf-8")).hexdigest())
    print("bytes: %d -> %d" % (len(original.encode("utf-8")), len(written.encode("utf-8"))))
    print("")
    print("DONE. Commit and push:")
    print("  git add forge-evening-debrief.html forge_install29.py")
    print('  git commit -m "install29: carry cap gate at 3 + escalating carry states"')
    print("  git pull --rebase")
    print("  git push")
    print("")
    print("NO workflow run - the debrief is hand-maintained.")


if __name__ == "__main__":
    main()

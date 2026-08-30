#!/usr/bin/env python3
# forge_twostar_planner_20260830.py
# Two-keystone cap (planner star selector allows up to 2 keystones + hint). Push-only, NO workflow run.
import hashlib, sys, shutil, os

TARGET   = 'planner.html'
PRE_SHA  = '9a7c5d42a3628d7f7eed8b6fe709cdff588722674d8c8a7246405458a732f468'
POST_SHA = 'aaf2cd97fefe7e19f2e78cec4d6bc06be29265388d2caa9ce61d73a394ef14a9'
SURVIVORS = ['function renderTop5(', 'loadTop5', 'saveTop5', 'ksMax']
EDITS = [('      star.onclick = function(){ var a = loadTop5(); var was = !!(a[i] && a[i].k); for (var j = 0; j < 5; j++){ if (a[j]) a[j].k = false; } if (a[i]) a[i].k = !was; saveTop5(a); renderTop5(); };', '      star.onclick = function(){ var a = loadTop5(); var was = !!(a[i] && a[i].k); if (!was){ var kc = a.filter(function(x){ return x && x.k; }).length; if (kc >= 2){ ksMax(); return; } } if (a[i]) a[i].k = !was; saveTop5(a); renderTop5(); };'), ('function renderTop5(', "function ksMax(){ var el=document.getElementById('ksmax-toast'); if(!el){ el=document.createElement('div'); el.id='ksmax-toast'; el.style.cssText='position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#0d0d0d;color:#ffc107;font-weight:800;font-size:13px;letter-spacing:.03em;padding:9px 15px;border-radius:9px;z-index:99999;opacity:0;transition:opacity .18s;box-shadow:0 4px 14px rgba(0,0,0,.4);pointer-events:none;'; document.body.appendChild(el); } el.textContent='2 keystones max'; el.style.opacity='1'; clearTimeout(el._t); el._t=setTimeout(function(){ el.style.opacity='0'; },1500); }\n\nfunction renderTop5(")]

def die(m): print("ABORT:", m); sys.exit(1)

if not os.path.exists(TARGET): die(TARGET + " not found - run me from inside the repo (gh-pages branch)")
src = open(TARGET, encoding="utf-8").read()
cur = hashlib.sha256(src.encode()).hexdigest()
if cur == POST_SHA: die("already applied (file at POST sha). Nothing to do.")
if cur != PRE_SHA:  die("PRE sha mismatch. Expected " + PRE_SHA + " got " + cur + ". Wrong file/branch - stopping, nothing written.")
for old, new in EDITS:
    c = src.count(old)
    if c != 1: die("anchor not found exactly once (count=%d): %r" % (c, old[:70]))
    src = src.replace(old, new)
new_sha = hashlib.sha256(src.encode()).hexdigest()
if new_sha != POST_SHA: die("POST sha mismatch after patch (%s). Stopping, nothing written." % new_sha)
for mk in SURVIVORS:
    if mk not in src: die("survivor marker missing: " + mk)
bak = TARGET + ".twostar_20260830.bak"
shutil.copy2(TARGET, bak)
open(TARGET, "w", encoding="utf-8").write(src)
print("OK - patched", TARGET)
print("backup:", bak)
print("new sha256:", new_sha, "(matches expected POST)")
print("Next: git add " + TARGET + ", commit, git pull --rebase, git push. NO workflow run needed.")

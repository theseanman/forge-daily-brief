#!/usr/bin/env python3
# forge_twostar_debrief_20260830.py
# Two-keystone cap (debrief star selector allows up to 2 keystones + hint + all-closed keystone stat). Push-only, NO workflow run.
import hashlib, sys, shutil, os

TARGET   = 'forge-evening-debrief.html'
PRE_SHA  = 'ff92278b7605f5dc40c57afadede485bf16a0c0edd27fb84b9d92a16c8e9df1f'
POST_SHA = '9ec4f782a2b527b114f0abb2d932e18c102490a5f8a5324e03a710d717b0c90d'
SURVIVORS = ['function recordHistory(', 'function collectDaily(', 'function keystoneStats(', 'GATE_AT', 'ksMax']
EDITS = [('    st.onclick=function(){ planRows.forEach(function(r,j){ r.k = (j===i && !it.k); }); renderPlanRows(); checkPlan(); };', '    st.onclick=function(){ var cur=!!(planRows[i]&&planRows[i].k); if(!cur){ var kc=planRows.filter(function(x){ return x&&x.k; }).length; if(kc>=2){ ksMax(); return; } } if(planRows[i]) planRows[i].k=!cur; renderPlanRows(); checkPlan(); };'), ("    var key = real.filter(function(i){ return i.k; })[0];\n    var msg = done+' of '+real.length+' closed.';\n    if (key) msg += key.done ? '  Keystone done — that is the day won.' : '  Keystone still open: '+key.t;\n    note.textContent = msg;\n", "    var keys = real.filter(function(i){ return i.k; });\n    var msg = done+' of '+real.length+' closed.';\n    if (keys.length){ var kopen = keys.filter(function(i){ return !i.done; }); msg += kopen.length ? '  Keystone still open: '+kopen.map(function(i){ return i.t; }).join('; ') : '  Keystone'+(keys.length>1?'s':'')+' done — that is the day won.'; }\n    note.textContent = msg;\n"), ('  var keyItem = real.filter(function(i){ return i.k; })[0];\n  h[fdToday()] = { done: real.filter(function(i){ return i.done; }).length, total: real.length,\n                   debriefed: true,\n                   key: keyItem ? 1 : 0, keyDone: (keyItem && keyItem.done) ? 1 : 0 };', '  var keyItems = real.filter(function(i){ return i.k; });\n  h[fdToday()] = { done: real.filter(function(i){ return i.done; }).length, total: real.length,\n                   debriefed: true,\n                   key: keyItems.length ? 1 : 0, keyDone: (keyItems.length && keyItems.every(function(i){ return i.done; })) ? 1 : 0 };'), ('function collectDaily(){\n  var real = todayT5.filter(function(i){ return i && i.t; });\n  var keyItem = real.filter(function(i){ return i.k; })[0];', 'function collectDaily(){\n  var real = todayT5.filter(function(i){ return i && i.t; });\n  var keyItems = real.filter(function(i){ return i.k; });'), ('      keySet: keyItem ? 1 : 0,\n      keyDone: (keyItem && keyItem.done) ? 1 : 0,', '      keySet: keyItems.length ? 1 : 0,\n      keyDone: (keyItems.length && keyItems.every(function(i){ return i.done; })) ? 1 : 0,'), ('function recordHistory(', "function ksMax(){ var el=document.getElementById('ksmax-toast'); if(!el){ el=document.createElement('div'); el.id='ksmax-toast'; el.style.cssText='position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#0d0d0d;color:#ffc107;font-weight:800;font-size:13px;letter-spacing:.03em;padding:9px 15px;border-radius:9px;z-index:99999;opacity:0;transition:opacity .18s;box-shadow:0 4px 14px rgba(0,0,0,.4);pointer-events:none;'; document.body.appendChild(el); } el.textContent='2 keystones max'; el.style.opacity='1'; clearTimeout(el._t); el._t=setTimeout(function(){ el.style.opacity='0'; },1500); }\n\nfunction recordHistory(")]

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

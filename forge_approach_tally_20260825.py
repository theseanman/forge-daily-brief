#!/usr/bin/env python3
# forge_approach_tally_20260825.py
# Adds an "Approaches" daily-number tally to the planner's PRACTICE card:
# type the day's count, weekly total (Monday-start) climbs toward 200. New key
# forge-approach {date:{n}}, synced max-wins so a stale copy never lowers it,
# 60-day prune. Practice-only - never counted toward "enough". planner.html is
# hand-maintained: run locally, then push. No workflow. REQUIRES the Worker
# allowlist to already accept forge-approach (verified: returns {}).
import hashlib, os, sys, time, re

FILE = 'planner.html'
PRE_SHA = 'e11174f3108a027b766c74eb4b85aaa3df5e95dff754d4b4dc9c5dbc3e641d0d'

A1_OLD = "var K_REPS = 'forge-reps'; /* install22 */"
A1_NEW = A1_OLD + "\nvar K_APPROACH = 'forge-approach'; /* approach mechanic tally */"

A2_OLD = "var SYNC_KEYS = [K_TOP5, K_PLAN, K_BACKLOG, K_FUN, 'forge-week-rocks', K_MUSHIN, K_PROJ, K_PARKED, K_REPS, K_FRAME]; /* install22, install30 */"
A2_NEW = "var SYNC_KEYS = [K_TOP5, K_PLAN, K_BACKLOG, K_FUN, 'forge-week-rocks', K_MUSHIN, K_PROJ, K_PARKED, K_REPS, K_FRAME, K_APPROACH]; /* install22, install30, approach */"

A3_OLD = "                changed = true;\n                }\n                continue;\n              }"
A3_NEW = A3_OLD + (
    "\n"
    "              if (key === K_APPROACH) { /* approach counts only ever go up */\n"
    "                var la = local[dk], ca = cloud[dk];\n"
    "                var laN = (la && typeof la.n === 'number') ? la.n : -1;\n"
    "                var caN = (ca && typeof ca.n === 'number') ? ca.n : -1;\n"
    "                var wantAN = caN > laN ? caN : (laN > 0 ? laN : 0);\n"
    "                if (wantAN !== (laN > 0 ? laN : 0)) { local[dk] = { n: wantAN }; changed = true; }\n"
    "                continue;\n"
    "              }"
)

A4_OLD = "          'background:#ffc107;color:#0d0d0d;\">+1</button>' +\n      '</div>' +\n    '</div>';"
A4_NEW = (
    "          'background:#ffc107;color:#0d0d0d;\">+1</button>' +\n"
    "      '</div>' +\n"
    "      '<div style=\"display:flex;align-items:center;gap:10px;padding:9px 0;border-top:1px solid rgba(255,201,7,0.25);\">' +\n"
    "        '<div style=\"flex:1;min-width:0;\">' +\n"
    "          '<div style=\"font-size:10px;letter-spacing:0.16em;opacity:0.75;\">\\u2197 APPROACHES</div>' +\n"
    "          '<div style=\"font-size:19px;font-weight:800;line-height:1.25;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;\">' +\n"
    "            '<input id=\"p-appr-in\" type=\"number\" inputmode=\"numeric\" min=\"0\" value=\"' + apprEntry(pDayKey()).n + '\" onchange=\"apprSet(this.value)\" style=\"width:66px;background:rgba(255,201,7,0.12);border:1px solid rgba(255,201,7,0.4);border-radius:6px;color:#ffc107;font-size:18px;font-weight:800;padding:3px 6px;text-align:center;-webkit-appearance:none;\" />' +\n"
    "            '<span style=\"font-size:12px;font-weight:600;opacity:0.6;\">today &middot; <span id=\"p-appr-wk\">' + apprWeek() + '</span> / 200 this week</span>' +\n"
    "          '</div>' +\n"
    "          '<div style=\"font-size:10px;opacity:0.7;margin-top:2px;\">eye contact \\u2192 eyebrow flash \\u2192 head tilt \\u2192 smile</div>' +\n"
    "        '</div>' +\n"
    "      '</div>' +\n"
    "    '</div>';"
)

A5_OLD = "function paintReps(){\n  var el = document.getElementById('p-reps-n');\n  if (el) el.textContent = repsEntry(pDayKey()).n;\n}"
A5_NEW = A5_OLD + (
    "\n\n"
    "/* approach mechanic tally (daily number; weekly total, Monday-start, toward 200) */\n"
    "var APPR_KEEP = 60;\n"
    "function apprAll(){ var o = readJSON(K_APPROACH, {}); return (o && typeof o === 'object' && !Array.isArray(o)) ? o : {}; }\n"
    "function apprEntry(dk){ var e = apprAll()[dk]; var n = (e && typeof e.n === 'number' && e.n > 0) ? Math.floor(e.n) : 0; return { n: n }; }\n"
    "function apprWeek(){ var all = apprAll(), sum = 0, now = new Date(), dow = (now.getDay() + 6) % 7, d, e; for (var i = 0; i <= dow; i++){ d = new Date(now); d.setDate(now.getDate() - i); e = all[ymd(d)]; if (e && typeof e.n === 'number' && e.n > 0) sum += Math.floor(e.n); } return sum; }\n"
    "function apprSet(v){ var dk = pDayKey(), all = apprAll(); var n = parseInt(v, 10); if (isNaN(n) || n < 0) n = 0; all[dk] = { n: n }; var ks = Object.keys(all).sort(); if (ks.length > APPR_KEEP){ var t = {}; ks.slice(-APPR_KEEP).forEach(function(x){ t[x] = all[x]; }); all = t; } writeJSON(K_APPROACH, all); syncPush(K_APPROACH); paintAppr(); }\n"
    "function paintAppr(){ var w = document.getElementById('p-appr-wk'); if (w) w.textContent = apprWeek(); var inp = document.getElementById('p-appr-in'); if (inp && document.activeElement !== inp) inp.value = apprEntry(pDayKey()).n; }"
)

EDITS = [("K_APPROACH const", A1_OLD, A1_NEW), ("SYNC_KEYS", A2_OLD, A2_NEW),
         ("merge branch", A3_OLD, A3_NEW), ("practice row", A4_OLD, A4_NEW),
         ("helpers", A5_OLD, A5_NEW)]

def die(m):
    print("ABORT: " + m + "  (file left untouched)"); sys.exit(1)

if not os.path.exists(FILE):
    die(FILE + " not found. cd to the repo folder first.")

src = open(FILE, 'r', encoding='utf-8').read()
cur = hashlib.sha256(src.encode('utf-8')).hexdigest()
if cur != PRE_SHA:
    die("planner.html is not the expected version.\n       Expected " + PRE_SHA + "\n       Got      " + cur)

for name, old, _ in EDITS:
    if src.count(old) != 1:
        die("anchor '%s' found %d times, expected 1" % (name, src.count(old)))

new = src
for _, old, rep in EDITS:
    new = new.replace(old, rep)

checks = {
    "K_APPROACH defined":  "var K_APPROACH = 'forge-approach'" in new,
    "in SYNC_KEYS":        "K_FRAME, K_APPROACH]" in new,
    "merge branch":        "if (key === K_APPROACH)" in new,
    "row input":           'id="p-appr-in"' in new and "APPROACHES" in new,
    "weekly readout":      'id="p-appr-wk"' in new and "/ 200 this week" in new,
    "helpers":             all(h in new for h in ["function apprAll(", "function apprEntry(", "function apprWeek(", "function apprSet(", "function paintAppr("]),
    "reps intact":         "function repsBump(" in new and 'id="p-reps-n"' in new,
    "braces balanced":     new.count("{") == new.count("}"),
}
for k, ok in checks.items():
    if not ok:
        die("post-check failed: " + k)

delta = len(new) - len(src)
if not (1200 < delta < 3000):
    die("unexpected size change of %d bytes" % delta)

bak = FILE + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
open(bak, 'w', encoding='utf-8').write(src)
open(FILE, 'w', encoding='utf-8').write(new)
print("OK  planner.html patched.")
print("    backup:   " + bak)
print("    POST-SHA: " + hashlib.sha256(new.encode('utf-8')).hexdigest())

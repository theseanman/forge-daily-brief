#!/usr/bin/env python3
"""
debrief_protocol_review_aug14.py

Patches forge-evening-debrief.html on gh-pages.

WHAT IT DOES
  1. Inserts a new "Protocol Review" step between Wins & Misses (step-5)
     and Tomorrow's Five (step-6 → step-7).
  2. Three themed sections (Terrain / Tempo / Presence) matching the
     morning brief's Paramount Protocol card, plus Cal AI standalone.
  3. Each countable item gets a +/- tap counter. Each section (Terrain,
     Tempo) gets a "minutes" input. Presence has NO counter — Protocol 5
     is unscored by design.
  4. Four separate pause sub-cue counters: speaking, reaching, deciding,
     getting up and moving.
  5. Counts are date-keyed in localStorage as forge-protocol-counts,
     synced to forge-sync, and folded into collectDaily() for the
     daily log.
  6. Step count goes from 7 → 8; old step-6 becomes step-7; the
     initPlanRows trigger and display headers are renumbered.

SAFE: refuses to run unless the file matches the expected SHA.
Writes a timestamped .bak before touching anything.
"""

import hashlib, os, shutil, sys, datetime, gzip, base64, json

TARGET = "forge-evening-debrief.html"
PRE_SHA = "c01b69dca6668151bf456bece56248c004bdc35849a131dd6375d063c0408201"

def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def die(msg):
    print("ABORTED: " + msg)
    sys.exit(1)

# --------------------------------------------------------------------------
# The new CSS
# --------------------------------------------------------------------------
NEW_CSS = """
    /* --- protocol review step --- */
    .proto-sec { border-radius:10px; padding:0 0 10px 0; margin-bottom:14px; overflow:hidden; }
    .proto-head { font-size:14px; font-weight:800; letter-spacing:.12em; padding:10px 12px 0; }
    .proto-sub { font-size:11px; opacity:.7; padding:2px 12px 8px; font-style:italic; }
    .proto-row { display:flex; align-items:center; justify-content:space-between;
                 padding:8px 12px; margin:0 8px 6px; background:rgba(255,255,255,.08);
                 border-radius:6px; gap:8px; }
    .proto-label { font-size:13px; font-weight:600; flex:1; line-height:1.35; }
    .proto-label small { font-weight:400; opacity:.65; font-size:11px; display:block; margin-top:1px; }
    .proto-ctr { display:flex; align-items:center; gap:6px; }
    .proto-btn { width:36px; height:36px; border-radius:6px; border:1px solid var(--border);
                 background:var(--surface); color:var(--text); font-size:18px; font-weight:700;
                 cursor:pointer; touch-action:manipulation; display:flex; align-items:center;
                 justify-content:center; }
    .proto-btn:active { background:rgba(255,255,255,.15); }
    .proto-val { min-width:28px; text-align:center; font-size:15px; font-weight:700; }
    .proto-min-row { display:flex; align-items:center; gap:8px; padding:4px 12px 6px;
                     margin:0 8px; }
    .proto-min-label { font-size:11px; color:var(--muted); }
    .proto-min-input { width:60px; text-align:center; padding:6px 4px; font-size:14px; }
    .proto-presence-note { font-size:11px; color:#8a9ad0; opacity:.8; padding:4px 12px 6px;
                           margin:0 8px; line-height:1.5; }
"""

CSS_ANCHOR = "    .badge-pop.show { display:block; }\n</style>"

# --------------------------------------------------------------------------
# The new step HTML
# --------------------------------------------------------------------------
STEP_HTML = """
    <div class="step" id="step-6">
      <div class="step-header">07 &middot; Protocol review</div>
      <div class="step-title">How did the practice land?</div>
      <div class="step-sub">Tap to count. Each section tracks instances and minutes separately.</div>

      <!-- TERRAIN -->
      <div class="proto-sec" style="background:linear-gradient(135deg,rgba(26,95,168,.22),rgba(18,58,108,.10)); border:1px solid #4a9de8;">
        <div class="proto-head" style="color:#4a9de8;">TERRAIN</div>
        <div class="proto-sub" style="color:#4a9de8;">Choose the ground. Refuse what you cannot hold.</div>
        <div class="proto-row"><div class="proto-label">&#x2694;&#xFE0F; Boundary Rep<small>Stated a preference or declined something</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('boundary',-1)">&minus;</button><div class="proto-val" id="pv-boundary">0</div><button class="proto-btn" onclick="protoInc('boundary',1)">+</button></div></div>
        <div class="proto-row"><div class="proto-label">&#x1F5E1;&#xFE0F; Warrior Promise<small>Named the hard thing and did it first</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('warrior',-1)">&minus;</button><div class="proto-val" id="pv-warrior">0</div><button class="proto-btn" onclick="protoInc('warrior',1)">+</button></div></div>
        <div class="proto-row"><div class="proto-label">&#x1F3D4;&#xFE0F; Opportunity Scanning<small>&ldquo;What opportunity does this present?&rdquo;</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('opportunity',-1)">&minus;</button><div class="proto-val" id="pv-opportunity">0</div><button class="proto-btn" onclick="protoInc('opportunity',1)">+</button></div></div>
        <div class="proto-min-row"><span class="proto-min-label">Minutes practised</span><input type="number" inputmode="numeric" class="proto-min-input" id="pm-terrain" value="0" min="0"></div>
      </div>

      <!-- TEMPO -->
      <div class="proto-sec" style="background:linear-gradient(135deg,rgba(200,140,60,.22),rgba(150,95,35,.10)); border:1px solid #e0a854;">
        <div class="proto-head" style="color:#e0a854;">TEMPO</div>
        <div class="proto-sub" style="color:#e0a854;">Nothing hurried. Nothing anxious.</div>
        <div class="proto-row"><div class="proto-label">&#x23F8;&#xFE0F; Pause &mdash; speaking<small>Breathed out before the word</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('pause_speak',-1)">&minus;</button><div class="proto-val" id="pv-pause_speak">0</div><button class="proto-btn" onclick="protoInc('pause_speak',1)">+</button></div></div>
        <div class="proto-row"><div class="proto-label">&#x23F8;&#xFE0F; Pause &mdash; reaching<small>Caught the hand before it moved</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('pause_reach',-1)">&minus;</button><div class="proto-val" id="pv-pause_reach">0</div><button class="proto-btn" onclick="protoInc('pause_reach',1)">+</button></div></div>
        <div class="proto-row"><div class="proto-label">&#x23F8;&#xFE0F; Pause &mdash; deciding<small>Noticed deciding and held the gate</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('pause_decide',-1)">&minus;</button><div class="proto-val" id="pv-pause_decide">0</div><button class="proto-btn" onclick="protoInc('pause_decide',1)">+</button></div></div>
        <div class="proto-row"><div class="proto-label">&#x23F8;&#xFE0F; Pause &mdash; getting up<small>Paused before standing or moving</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('pause_move',-1)">&minus;</button><div class="proto-val" id="pv-pause_move">0</div><button class="proto-btn" onclick="protoInc('pause_move',1)">+</button></div></div>
        <div class="proto-row"><div class="proto-label">&#x1F422; Slow Movements &amp; Speech<small>Moved or spoke 20% slower than impulse</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('slow',-1)">&minus;</button><div class="proto-val" id="pv-slow">0</div><button class="proto-btn" onclick="protoInc('slow',1)">+</button></div></div>
        <div class="proto-row"><div class="proto-label">&#x1F91D; I&rsquo;m Fine Either Way<small>Said it before the tense moment</small></div><div class="proto-ctr"><button class="proto-btn" onclick="protoInc('fine',-1)">&minus;</button><div class="proto-val" id="pv-fine">0</div><button class="proto-btn" onclick="protoInc('fine',1)">+</button></div></div>
        <div class="proto-min-row"><span class="proto-min-label">Minutes practised</span><input type="number" inputmode="numeric" class="proto-min-input" id="pm-tempo" value="0" min="0"></div>
      </div>

      <!-- PRESENCE -->
      <div class="proto-sec" style="background:linear-gradient(135deg,rgba(90,105,160,.22),rgba(52,62,105,.10)); border:1px solid #8a9ad0;">
        <div class="proto-head" style="color:#8a9ad0;">PRESENCE</div>
        <div class="proto-sub" style="color:#8a9ad0;">No performance in this one.</div>
        <div class="proto-presence-note">Were you there? No count, no score, no tick. The practice is noticing the narrative and letting it pass. If you find yourself wanting a number here, that impulse is the thing this section exists to catch.</div>
        <div style="padding:6px 12px;">
          <textarea id="proto-presence-note" placeholder="Anything worth noting about presence today. Optional — blank is fine." style="min-height:50px; font-size:13px;"></textarea>
        </div>
      </div>

      <!-- CAL AI -->
      <div class="proto-row" style="border:1px solid var(--border); border-radius:8px; margin:0 0 14px;">
        <div class="proto-label">&#x1F4F1; Cal AI meals logged</div>
        <div class="proto-ctr"><button class="proto-btn" onclick="protoInc('cal_ai',-1)">&minus;</button><div class="proto-val" id="pv-cal_ai">0</div><button class="proto-btn" onclick="protoInc('cal_ai',1)">+</button></div>
      </div>

      <div class="btn-row">
        <button class="btn" onclick="prev()"><i class="ti ti-arrow-left"></i></button>
        <button class="btn primary" onclick="next()">Tomorrow&rsquo;s five <i class="ti ti-arrow-right"></i></button>
      </div>
    </div>
"""

# --------------------------------------------------------------------------
# The new JS (protocol counter functions)
# --------------------------------------------------------------------------
NEW_JS = """
/* --- protocol review counters (debrief_protocol_review_aug14) --- */
var K_PROTO = 'forge-protocol-counts';
var PROTO_ITEMS = ['boundary','warrior','opportunity','pause_speak','pause_reach',
                   'pause_decide','pause_move','slow','fine','cal_ai'];
var protoCounts = {};

function protoToday() {
  var all = fdRead(K_PROTO, {});
  var t = fdToday();
  if (!all[t]) all[t] = {};
  return all;
}
function protoLoad() {
  var all = protoToday();
  var t = fdToday();
  var day = all[t] || {};
  protoCounts = {};
  PROTO_ITEMS.forEach(function(k) {
    protoCounts[k] = day[k] || 0;
    var el = document.getElementById('pv-' + k);
    if (el) el.textContent = protoCounts[k];
  });
  var tm = document.getElementById('pm-terrain');
  if (tm) tm.value = day.terrain_min || 0;
  var tp = document.getElementById('pm-tempo');
  if (tp) tp.value = day.tempo_min || 0;
  var pn = document.getElementById('proto-presence-note');
  if (pn) pn.value = day.presence_note || '';
}
function protoSave() {
  var all = protoToday();
  var t = fdToday();
  var day = all[t] || {};
  PROTO_ITEMS.forEach(function(k) { day[k] = protoCounts[k] || 0; });
  day.terrain_min = parseInt(document.getElementById('pm-terrain')?.value) || 0;
  day.tempo_min = parseInt(document.getElementById('pm-tempo')?.value) || 0;
  day.presence_note = (document.getElementById('proto-presence-note')?.value || '').trim();
  all[t] = day;
  /* prune to 120 days */
  var keys = Object.keys(all).sort();
  if (keys.length > 120) {
    var o = {}; keys.slice(-120).forEach(function(k) { o[k] = all[k]; }); all = o;
  }
  fdWrite(K_PROTO, all);
  syncPush(K_PROTO);
}
function protoInc(k, d) {
  if (!protoCounts[k]) protoCounts[k] = 0;
  protoCounts[k] += d;
  if (protoCounts[k] < 0) protoCounts[k] = 0;
  var el = document.getElementById('pv-' + k);
  if (el) el.textContent = protoCounts[k];
  protoSave();
}
function protoCollect() {
  var all = fdRead(K_PROTO, {});
  return all[fdToday()] || {};
}
"""


def main():
    if not os.path.exists(TARGET):
        die("%s not found. Run this from ~/Desktop/forge-daily-brief on gh-pages." % TARGET)

    actual = sha(TARGET)
    if actual != PRE_SHA:
        die("%s is not the expected version.\n  expected %s\n  found    %s\n"
            "  Nothing was changed." % (TARGET, PRE_SHA, actual))

    with open(TARGET, "r", encoding="utf-8") as f:
        src = f.read()

    original = src

    # --- 1. Inject CSS before </style> ---
    if src.count(CSS_ANCHOR) != 1:
        die("CSS anchor matched %d times" % src.count(CSS_ANCHOR))
    src = src.replace(CSS_ANCHOR, NEW_CSS + CSS_ANCHOR, 1)

    # --- 2. Inject the step-6 HTML before the old step-6 ---
    old_step6_anchor = '    <div class="step" id="step-6">\n      <div class="step-header">07 &middot; Tomorrow&rsquo;s five</div>'
    if src.count(old_step6_anchor) != 1:
        die("old step-6 anchor matched %d times" % src.count(old_step6_anchor))

    # Renumber old step-6 to step-7, header 07 to 08
    new_step7 = '    <div class="step" id="step-7">\n      <div class="step-header">08 &middot; Tomorrow&rsquo;s five</div>'
    src = src.replace(old_step6_anchor, STEP_HTML + "\n" + new_step7, 1)

    # --- 3. Update STEPS constant from 7 to 8 ---
    if src.count("const STEPS = 7;") != 1:
        die("STEPS constant not found exactly once")
    src = src.replace("const STEPS = 7;", "const STEPS = 8;", 1)

    # --- 4. Update showStep's initPlanRows trigger from 6 to 7 ---
    if src.count("if (n === 6) initPlanRows();") != 1:
        die("initPlanRows trigger not found exactly once")
    src = src.replace("if (n === 6) initPlanRows();",
                       "if (n === 6) protoLoad();\n  if (n === 7) initPlanRows();", 1)

    # --- 5. Inject JS before the init() call ---
    init_anchor = "\ninit();\n"
    if src.count(init_anchor) != 1:
        die("init() anchor not found exactly once")
    src = src.replace(init_anchor, NEW_JS + init_anchor, 1)

    # --- 6. Add K_PROTO to the key declarations ---
    key_anchor = "var K_VIDEO='forge-video'; /* install25 */"
    if src.count(key_anchor) != 1:
        die("K_VIDEO key anchor not found exactly once")
    src = src.replace(key_anchor, key_anchor + "\nvar K_PROTO='forge-protocol-counts'; /* debrief_protocol_review_aug14 */", 1)

    # --- 7. Add protocol data to collectDaily ---
    collect_anchor = "    health: null,"
    if src.count(collect_anchor) != 1:
        die("collectDaily health:null anchor not found exactly once")
    src = src.replace(collect_anchor, "    protocol: protoCollect(),\n    health: null,", 1)

    # --- 8. Add protoSave() to finishDebrief ---
    finish_anchor = "function finishDebrief() {\n  saveTomorrow();"
    if src.count(finish_anchor) != 1:
        die("finishDebrief anchor not found exactly once")
    src = src.replace(finish_anchor, "function finishDebrief() {\n  protoSave();\n  saveTomorrow();", 1)

    # --- 9. Add protocol summary to the closing scorecard ---
    summary_anchor = "    {label:'ESP events', val:espCount+''},"
    if src.count(summary_anchor) != 1:
        die("summary grid ESP anchor not found exactly once")
    proto_summary = (
        "    {label:'ESP events', val:espCount+''},\n"
        "    {label:'Pause reps', val:(protoCollect().pause_speak||0)+(protoCollect().pause_reach||0)+(protoCollect().pause_decide||0)+(protoCollect().pause_move||0)+''},"
    )
    src = src.replace(summary_anchor, proto_summary, 1)

    # --- 10. Add protocol to CSV_COLS ---
    csv_anchor = "'sleep_score','sleep_dur','energy','health','stress',"
    if src.count(csv_anchor) != 1:
        die("CSV_COLS anchor not found exactly once")
    src = src.replace(csv_anchor,
        "'sleep_score','sleep_dur','energy','health','stress',\n"
        "  'boundary','warrior','opportunity','pause_speak','pause_reach','pause_decide','pause_move','slow','fine','cal_ai','terrain_min','tempo_min',", 1)

    # --- post-conditions ---
    checks = [
        ("const STEPS = 8;", 1),
        ('id="step-7"', 1),
        ('id="step-6"', 1),
        ("protoLoad()", 2),  # showStep trigger + function def
        ("protoSave()", 3),  # in protoInc, finishDebrief, and the function def
        ("protoCollect()", 6),  # function def + collectDaily + 4x in summary line
        ("K_PROTO", 6),  # key const decl, var decl, protoToday fdRead, protoSave fdWrite, protoSave syncPush, protoCollect fdRead
        ("forge-protocol-counts", 2),  # K_PROTO const + var decl
        ("proto-presence-note", 5),  # HTML id + placeholder, CSS class, load, save
        ("Pause reps", 1),
        ("protocol: protoCollect()", 1),
    ]
    # survival checks — at least N occurrences
    survival = [
        ("saveTomorrow", 2),
        ("recordHistory", 2),
        ("saveDailyLog", 2),
        ("K_MUSHIN", 2),
        ("K_REPS", 2),
        ("K_FRAME", 3),
    ]
    for needle, want in checks:
        got = src.count(needle)
        if got != want:
            die("post-check: '%s' appears %d times, expected %d" % (needle, got, want))

    for needle, minimum in survival:
        got = src.count(needle)
        if got < minimum:
            die("survival check: '%s' appears %d times, expected >= %d" % (needle, got, minimum))

    # --- write ---
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = TARGET + ".bak-" + stamp
    shutil.copy2(TARGET, backup)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(src)

    print("OK  debrief_protocol_review_aug14 applied")
    print("    backup   " + backup)
    print("    bytes    %d -> %d" % (len(original.encode()), len(src.encode())))
    print("    post SHA " + sha(TARGET))
    print("")
    print("    Next: git add forge-evening-debrief.html debrief_protocol_review_aug14.py")
    print("          commit, pull --rebase, push.")
    print("          NO workflow run needed — the debrief is hand-maintained.")


if __name__ == "__main__":
    main()

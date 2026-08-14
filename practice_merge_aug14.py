#!/usr/bin/env python3
"""
practice_merge_aug14.py

Patches forge_actions.py (the Forge Daily Brief generator).

WHAT IT DOES
  1. Merges "Five Paramount Goals" + "Summer Protocol" into ONE card,
     de-duplicated, split into three themed sections:
        TERRAIN  (Highland)  - Boundary Rep, Warrior Promise, Opportunity Scanning
        TEMPO    (Wayne)     - Pause, Slow Movements & Speech, I'm Fine Either Way
        PRESENCE (Musashi)   - Not Relevant
     plus Cal AI standing alone, unthemed.
  2. Each section carries an image band fed from on-device localStorage.
     Images are NEVER committed to the repo. Tap a band to choose one; it is
     downscaled to 640px wide JPEG before storing, to protect the storage quota.
  3. Removes the brief's +/- goal counters and the dead g0-g4 code path.
     Counting moves to the evening debrief.
  4. PARKS three cards - Identityless Protocol, Future Self Protocol, SBOS
     Betting Intel. The HTML is NOT deleted. It moves into variables gated by
     a PARKED_CARDS set. Restoring one = removing one string from that set.

SAFE: refuses to run unless forge_actions.py matches the expected pre-image.
Writes a timestamped .bak beside the file before touching it.
"""

import hashlib
import os
import shutil
import sys
import datetime

TARGET = "forge_actions.py"

PRE_SHA = "c888ab079a28a634a3315a25806eeb15ef7e6ca489ac51e9e54706e440621e35"


# --------------------------------------------------------------------------
# ANCHOR 1 - the Five Paramount Goals card + the {protocol_block} placeholder.
# Replaced wholesale by a single {practice_card} placeholder.
# --------------------------------------------------------------------------

A1_OLD_START = '  <div class="card" style="background: linear-gradient(135deg, rgba(255,215,0,0.25), rgba(255,140,0,0.15)); border: 3px double var(--text-bright);">\n    <div class="card-header"><span class="card-icon">\U0001F3AF\U0001F334</span><span>Five Paramount Goals</span></div>'
A1_OLD_END = '{protocol_block}\n'
A1_NEW = '{practice_card}\n'


# --------------------------------------------------------------------------
# ANCHOR 2/3/4 - the three cards to park. Each inline block is swapped for a
# placeholder; the HTML itself is relocated, not destroyed.
# --------------------------------------------------------------------------

A2_START = '  <div class="card" style="background: linear-gradient(135deg, rgba(100,150,200,0.2), rgba(70,120,170,0.1)); border: 3px solid var(--text-bright);">\n    <div class="card-header"><span class="card-icon">\U0001F3AD\U0001F334</span><span>Identityless Protocol</span></div>'
A3_START = '  <div class="card" style="background: linear-gradient(135deg, rgba(150,100,200,0.2), rgba(120,70,170,0.1)); border: 3px solid var(--text-bright);">\n    <div class="card-header"><span class="card-icon">\u23F0\U0001F334</span><span>Future Self Protocol</span></div>'
A4_START = '  <div class="card">\n    <div class="card-header"><span class="card-icon">&#x1F3B0;&#x1F334;</span><span>SBOS Betting Intel</span></div>'

CARD_END = '\n  </div>\n'


# --------------------------------------------------------------------------
# ANCHOR 5 - the goal counter JS. Removed; image-band JS put in its place.
# --------------------------------------------------------------------------

A5_OLD = """var counts = [0,0,0,0,0];
function loadCounts() {{
  var today = new Date().toDateString();
  try {{
    if (localStorage.getItem('forge-date') === today) {{
      for (var i = 0; i < 5; i++) {{
        var v = localStorage.getItem('g' + i);
        if (v) counts[i] = parseInt(v);
      }}
    }} else {{
      for (var i = 0; i < 5; i++) localStorage.removeItem('g' + i);
      localStorage.setItem('forge-date', today);
    }}
  }} catch(e) {{}}
  for (var i = 0; i < 5; i++) {{
    var el = document.getElementById('goal-' + i + '-counter');
    if (el) el.textContent = counts[i];
  }}
}}
function incrementGoal(i) {{
  counts[i]++;
  try {{ localStorage.setItem('g' + i, counts[i]); }} catch(e) {{}}
  document.getElementById('goal-' + i + '-counter').textContent = counts[i];
}}
function decrementGoal(i) {{
  if (counts[i] > 0) counts[i]--;
  try {{ localStorage.setItem('g' + i, counts[i]); }} catch(e) {{}}
  document.getElementById('goal-' + i + '-counter').textContent = counts[i];
}}
"""

A5_NEW = """var PIMG_SLOTS = ['terrain','tempo','presence'];
function pimgKey(k) {{ return 'forge-img-' + k; }}
function pimgPaint() {{
  for (var i = 0; i < PIMG_SLOTS.length; i++) {{
    var k = PIMG_SLOTS[i];
    var el = document.getElementById('pimg-' + k);
    if (!el) continue;
    var v = null;
    try {{ v = localStorage.getItem(pimgKey(k)); }} catch(e) {{}}
    if (v) {{
      el.style.backgroundImage = 'url(' + v + ')';
      el.className = 'pimg-band has-img';
    }} else {{
      el.style.backgroundImage = '';
      el.className = 'pimg-band';
    }}
  }}
}}
function pimgPick(k) {{
  var inp = document.getElementById('pimg-file');
  if (!inp) return;
  inp.setAttribute('data-slot', k);
  inp.value = '';
  inp.click();
}}
function pimgStore(slot, dataUrl) {{
  try {{
    localStorage.setItem(pimgKey(slot), dataUrl);
  }} catch(e) {{
    var n = document.getElementById('pimg-note');
    if (n) n.textContent = 'Image too large for storage. Try a smaller photo.';
    return;
  }}
  var n2 = document.getElementById('pimg-note');
  if (n2) n2.textContent = '';
  pimgPaint();
}}
function pimgLoad(ev) {{
  var inp = ev.target;
  var slot = inp.getAttribute('data-slot');
  var f = inp.files && inp.files[0];
  if (!f || !slot) return;
  var fr = new FileReader();
  fr.onload = function() {{
    var img = new Image();
    img.onload = function() {{
      try {{
        var MAXW = 640;
        var w = img.width, h = img.height;
        if (w > MAXW) {{ h = Math.round(h * (MAXW / w)); w = MAXW; }}
        var c = document.createElement('canvas');
        c.width = w; c.height = h;
        c.getContext('2d').drawImage(img, 0, 0, w, h);
        pimgStore(slot, c.toDataURL('image/jpeg', 0.72));
      }} catch(e) {{
        var n = document.getElementById('pimg-note');
        if (n) n.textContent = 'Could not process that image.';
      }}
    }};
    img.onerror = function() {{
      var n = document.getElementById('pimg-note');
      if (n) n.textContent = 'Could not read that image.';
    }};
    img.src = fr.result;
  }};
  fr.onerror = function() {{
    var n = document.getElementById('pimg-note');
    if (n) n.textContent = 'Could not read that file.';
  }};
  fr.readAsDataURL(f);
}}
"""

A6_OLD = "  loadCounts(); setInterval(tick, 1000);"
A6_NEW = "  pimgPaint(); setInterval(tick, 1000);"


# --------------------------------------------------------------------------
# The new renderer, inserted ahead of render_summer_protocol().
# render_summer_protocol() itself is LEFT INTACT - parked, not deleted.
# --------------------------------------------------------------------------

RENDERER = '''
# --- practice_merge_aug14: parked cards -------------------------------------
# Remove a name from this set to bring that card back on the next workflow run.
# The HTML for each still exists, in generate_html(). Nothing was deleted.
PARKED_CARDS = {"identityless", "future_self", "sbos"}


def render_practice_card():
    """The merged practice card: Five Paramount Goals + Summer Protocol,
    de-duplicated, in three themed sections plus Cal AI standing alone.

    Camera Off, The Second Question and Warmth Rep are deliberately ABSENT.
    They are already carried by the daily cue rotation in the decision-rule
    card, and printing them here would duplicate the same instruction on one
    screen. Posture Reset is folded into PAUSE as the content of the pause.
    """
    sections = [
        {
            "slot": "terrain",
            "label": "TERRAIN",
            "sub": "Choose the ground. Refuse what you cannot hold.",
            "accent": "#4a9de8",
            "grad": "linear-gradient(135deg, rgba(26,95,168,0.30), rgba(18,58,108,0.14))",
            "items": [
                ("\\u2694\\uFE0F BOUNDARY REP",
                 "State one preference or decline one small thing. No qualifier, no apology. Let the silence sit.",
                 "Cue: once daily"),
                ("\\U0001F5E1\\uFE0F WARRIOR PROMISE",
                 "Name the one hard thing you are avoiding. Do it first, before the easy stuff.",
                 "Cue: morning"),
                ("\\U0001F3D4\\uFE0F OPPORTUNITY SCANNING",
                 "Every setback or new environment: \\u201cWhat opportunity does this situation present me with?\\u201d",
                 "Cue: the first setback of the day"),
            ],
        },
        {
            "slot": "tempo",
            "label": "TEMPO",
            "sub": "Nothing hurried. Nothing anxious.",
            "accent": "#e0a854",
            "grad": "linear-gradient(135deg, rgba(200,140,60,0.30), rgba(150,95,35,0.14))",
            "items": [
                ("\\u23F8\\uFE0F PAUSE BEFORE MOVING, DECIDING OR ACTING",
                 "When I catch myself drawing breath to speak \\u2014 let it out without words, shoulders down, then speak.<br>"
                 "<span style=\\"font-weight:400; font-size:13px;\\">Four places it applies: <strong>speaking</strong> \\u00b7 <strong>reaching</strong> \\u00b7 <strong>deciding</strong> \\u00b7 <strong>getting up and moving</strong>. "
                 "Each is counted separately at the debrief, so you can see where it lands and where it does not.</span>",
                 "Three today. Not all day. Raise it when three is boring."),
                ("\\U0001F422 SLOW MOVEMENTS & SPEECH",
                 "Deliberate, slower pace in all physical and verbal communication. Move 20% slower than your impulse \\u2014 reach, turn, walk slower.",
                 "Cue: all day"),
                ("\\U0001F91D I\\u2019M FINE EITHER WAY",
                 "Before the first tense interaction, say it silently and mean it. You would like it to go well; you do not need it to.",
                 "Cue: before tension"),
            ],
        },
        {
            "slot": "presence",
            "label": "PRESENCE",
            "sub": "No performance in this one.",
            "accent": "#8a9ad0",
            "grad": "linear-gradient(135deg, rgba(90,105,160,0.30), rgba(52,62,105,0.14))",
            "items": [
                ("\\U0001F9D8 NOT RELEVANT",
                 "When the optimizing narrative starts \\u2014 how to improve this, what it should become \\u2014 name it and take away its authority: "
                 "<em>not relevant to being present with my family.</em> It can stay. It does not get a vote.<br>"
                 "<span style=\\"font-weight:400; font-size:13px;\\">Scope: optimization thoughts only. Not a general silencer \\u2014 some internal signal is load-bearing. Two seconds, then back to one sense channel.</span>",
                 "Cue: the moment it starts"),
            ],
        },
    ]

    blocks = ""
    for s in sections:
        rows = ""
        for name, body, trigger in s["items"]:
            rows += (
                '<div class="pr-item" style="border-left:4px solid %s;">\\n'
                '      <div class="pr-name">%s</div>\\n'
                '      <div class="pr-body">%s</div>\\n'
                '      <div class="pr-trigger">%s</div>\\n'
                '    </div>\\n    ' % (s["accent"], name, body, trigger)
            )
        blocks += (
            '<div class="pr-section" style="background:%s; border:2px solid %s;">\\n'
            '    <div id="pimg-%s" class="pimg-band" onclick="pimgPick(\\'%s\\')">'
            '<span class="pimg-hint">tap to add your %s image</span></div>\\n'
            '    <div class="pr-head" style="color:%s;">%s</div>\\n'
            '    <div class="pr-sub">%s</div>\\n'
            '    %s</div>\\n  '
            % (s["grad"], s["accent"], s["slot"], s["slot"], s["label"],
               s["accent"], s["label"], s["sub"], rows)
        )

    cal_ai = (
        '<div class="pr-item" style="border-left:4px solid var(--text-bright); margin-top:4px;">\\n'
        '      <div class="pr-name">\\U0001F4F1 CAL AI BEFORE MEALS</div>\\n'
        '      <div class="pr-body">Log nutrition in Cal AI before eating. Every meal. Non-negotiable.</div>\\n'
        '      <div class="pr-trigger">Cue: every meal</div>\\n'
        '    </div>\\n  '
    )

    return (
        '  <div class="card" style="background: linear-gradient(135deg, rgba(255,215,0,0.16), rgba(255,140,0,0.08)); border: 3px double var(--text-bright);">\\n'
        '    <div class="card-header"><span class="card-icon">\\U0001F3AF</span><span>Paramount Protocol</span></div>\\n'
        '    <div class="pr-intro">Train where it is easy. Groove the reflex. It shows up when it matters.</div>\\n  '
        + blocks
        + cal_ai
        + '<div id="pimg-note" class="pr-note"></div>\\n'
        '    <div class="pr-note">Counts are recorded in the evening debrief, not here. Images stay on this device and are never uploaded.</div>\\n'
        '    <input type="file" id="pimg-file" accept="image/*" style="display:none;" onchange="pimgLoad(event)">\\n'
        '  </div>'
    )


'''


CSS_START = '    .paramount-goal {{'
CSS_END_RULE = '    .goal-counter {{'
CSS_NEW = '''    .pr-intro {{ font-size:13px; color:var(--text-light); opacity:0.85; margin-bottom:12px; line-height:1.6; }}
    .pr-section {{ border-radius:10px; padding:0 0 12px 0; margin-bottom:14px; overflow:hidden; }}
    .pimg-band {{ height:104px; background-size:cover; background-position:center 28%; background-color:rgba(0,0,0,0.22); display:flex; align-items:center; justify-content:center; cursor:pointer; }}
    .pimg-band.has-img .pimg-hint {{ display:none; }}
    .pimg-hint {{ font-size:11px; letter-spacing:0.08em; text-transform:uppercase; color:var(--text-light); opacity:0.6; }}
    .pr-head {{ font-size:15px; font-weight:800; letter-spacing:0.14em; padding:12px 14px 0 14px; }}
    .pr-sub {{ font-size:12px; color:var(--text-light); opacity:0.75; padding:2px 14px 10px 14px; font-style:italic; }}
    .pr-item {{ background:rgba(255,255,255,0.14); border-radius:6px; padding:11px 13px; margin:0 12px 9px 12px; }}
    .pr-name {{ font-size:14px; font-weight:700; color:var(--text-bright); margin-bottom:6px; }}
    .pr-body {{ font-size:13.5px; color:var(--text-light); line-height:1.65; font-weight:600; }}
    .pr-trigger {{ font-size:11.5px; color:var(--text-light); opacity:0.72; margin-top:6px; }}
    .pr-note {{ font-size:11px; color:var(--muted); margin-top:8px; line-height:1.5; }}'''


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def die(msg):
    print("ABORTED: " + msg)
    sys.exit(1)


def cut(src, start_anchor, end_marker, what):
    """Return (before, block, after) for a block beginning at start_anchor and
    ending at the first end_marker after it."""
    if src.count(start_anchor) != 1:
        die("anchor for %s matched %d times, expected 1" % (what, src.count(start_anchor)))
    i = src.index(start_anchor)
    j = src.index(end_marker, i)
    if j < 0:
        die("could not find the end of the %s block" % what)
    j += len(end_marker)
    return src[:i], src[i:j], src[j:]


def main():
    if not os.path.exists(TARGET):
        die("%s not found. Run this from ~/Desktop/forge-daily-brief on gh-pages." % TARGET)

    actual = sha(TARGET)
    if actual != PRE_SHA:
        die("%s is not the expected version.\n  expected %s\n  found    %s\n"
            "  Nothing was changed. The live generator may have moved on." % (TARGET, PRE_SHA, actual))

    with open(TARGET, "r", encoding="utf-8") as f:
        src = f.read()

    original = src

    # --- park the three cards, relocating their HTML into variables ---------
    pre, ident_html, post = cut(src, A2_START, CARD_END, "Identityless card")
    src = pre + "{identityless_card}\n" + post

    pre, future_html, post = cut(src, A3_START, CARD_END, "Future Self card")
    src = pre + "{future_self_card}\n" + post

    pre, sbos_html, post = cut(src, A4_START, CARD_END, "SBOS Betting card")
    src = pre + "{sbos_card}\n" + post

    for name, blob in (("Identityless", ident_html), ("Future Self", future_html)):
        if "{" in blob or "}" in blob:
            die("%s block contains braces; relocation would need escaping. Nothing written." % name)
    if sbos_html.count("{sbos_signals_html}") != 1:
        die("SBOS block did not contain exactly one {sbos_signals_html} placeholder. Nothing written.")

    # --- merge the goals + protocol cards -----------------------------------
    if src.count(A1_OLD_START) != 1:
        die("Five Paramount Goals anchor matched %d times, expected 1" % src.count(A1_OLD_START))
    i = src.index(A1_OLD_START)
    j = src.index(A1_OLD_END, i)
    if j < 0:
        die("could not find {protocol_block} after the goals card")
    j += len(A1_OLD_END)
    goals_span = src[i:j]
    if "Five Paramount Goals" not in goals_span or "{protocol_block}" not in goals_span:
        die("the span to replace does not look like the goals card. Nothing written.")
    if "card-header" in goals_span.replace(
            '<div class="card-header"><span class="card-icon">\U0001F3AF\U0001F334</span><span>Five Paramount Goals</span></div>', "", 1):
        die("the span to replace reaches into a second card. Nothing written.")
    src = src[:i] + A1_NEW + src[j:]

    # --- CSS: drop the orphaned goal/paramount rules, add the new ones ------
    if src.count(CSS_START) != 1:
        die("CSS start anchor matched %d times, expected 1" % src.count(CSS_START))
    if src.count(CSS_END_RULE) != 1:
        die("CSS end anchor matched %d times, expected 1" % src.count(CSS_END_RULE))
    ci = src.index(CSS_START)
    cj = src.index(CSS_END_RULE, ci)
    cj = src.index("\n", cj) + 1
    css_span = src[ci:cj]
    for cls in ("paramount-goal", "paramount-num", "goal-controls", "goal-btn", "goal-counter"):
        if cls not in css_span:
            die("CSS span is missing .%s; refusing to guess at its bounds. Nothing written." % cls)
    if css_span.count("{{") != 6:
        die("CSS span holds %d rules, expected 6. Nothing written." % css_span.count("{{"))
    src = src[:ci] + CSS_NEW + "\n" + src[cj:]

    # --- counter JS out, image JS in ---------------------------------------
    if src.count(A5_OLD) != 1:
        die("goal-counter JS block matched %d times, expected 1" % src.count(A5_OLD))
    src = src.replace(A5_OLD, A5_NEW, 1)

    if src.count(A6_OLD) != 1:
        die("window.onload anchor matched %d times, expected 1" % src.count(A6_OLD))
    src = src.replace(A6_OLD, A6_NEW, 1)

    # --- renderer + parked-card assignments ---------------------------------
    if src.count("\ndef render_summer_protocol():") != 1:
        die("render_summer_protocol definition not found exactly once")
    src = src.replace("\ndef render_summer_protocol():", RENDERER + "\ndef render_summer_protocol():", 1)

    assign_anchor = "    protocol_block = render_summer_protocol()\n"
    if src.count(assign_anchor) != 1:
        die("protocol_block assignment matched %d times, expected 1" % src.count(assign_anchor))

    ident_lit = repr(ident_html)
    future_lit = repr(future_html)
    sbos_tmpl = sbos_html.replace("{sbos_signals_html}", "@@SBOS@@")
    sbos_lit = repr(sbos_tmpl)

    assign_new = (
        "    protocol_block = render_summer_protocol()\n"
        "    practice_card = render_practice_card()\n"
        "    identityless_card = '' if 'identityless' in PARKED_CARDS else " + ident_lit + "\n"
        "    future_self_card = '' if 'future_self' in PARKED_CARDS else " + future_lit + "\n"
        "    sbos_card = '' if 'sbos' in PARKED_CARDS else " + sbos_lit + ".replace('@@SBOS@@', sbos_signals_html)\n"
    )
    src = src.replace(assign_anchor, assign_new, 1)

    # --- post-conditions ----------------------------------------------------
    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        die("patched file does not parse as Python: %s. Nothing written." % e)

    checks = [
        ("PARKED_CARDS = {", 1),
        ("def render_practice_card():", 1),
        ("{practice_card}", 1),
        ("{identityless_card}", 1),
        ("{future_self_card}", 1),
        ("{sbos_card}", 1),
        ("pimgPaint()", 3),
        ("incrementGoal", 0),
        ("decrementGoal", 0),
        ("loadCounts", 0),
        ("goal-counter", 0),
        ("def render_summer_protocol():", 1),
    ]
    for needle, want in checks:
        got = src.count(needle)
        if got != want:
            die("post-check failed: '%s' appears %d times, expected %d. Nothing written." % (needle, got, want))

    for marker, label in (("_cs", "sleepfix"), ("CALENDAR_ERRORS", "calfix")):
        if marker not in src:
            die("post-check failed: the %s work is missing from the patched file. Nothing written." % label)

    # --- write --------------------------------------------------------------
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = TARGET + ".bak-" + stamp
    shutil.copy2(TARGET, backup)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(src)

    print("OK  practice_merge_aug14 applied")
    print("    backup   " + backup)
    print("    bytes    %d -> %d" % (len(original.encode()), len(src.encode())))
    print("    post SHA " + sha(TARGET))
    print("")
    print("    Next: git add forge_actions.py practice_merge_aug14.py")
    print("          commit, pull --rebase, push, then RUN THE WORKFLOW.")


if __name__ == "__main__":
    main()

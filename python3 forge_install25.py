#!/usr/bin/env python3
"""
install25 - video audit logging + Sunday review checklist (forge-evening-debrief.html)

MUST RUN AFTER install23. Pre-image is install23's post-image.

Two additions:
  1. A tick in the step-5 reps card so an audit can be logged on ANY day. This is
     what makes the twice-weekly front-load work without a scheduler.
  2. A three-item checklist in the EXISTING Sunday review section (install20), with
     a count of audits done this week.

NEW KEY: forge-video {date: {done: true}}, 60-day prune.
  Needs one more Cloudflare allowlist paste. A dedicated key was chosen over
  piggybacking on forge-reps because piggybacking would have meant amending
  install22 AND install23 to preserve a third field, and both are already tested.

THE CHECKLIST IS REVIEW-ONLY. The copy says so explicitly and must keep saying so.
A checklist run DURING a conversation is the self-monitoring loop this whole build
exists to remove (Beilock/Carr - attending to components degrades automated skill).

Fails closed: any anchor problem leaves the file byte-identical.
"""
import hashlib
import os
import shutil
import sys

TARGET = "forge-evening-debrief.html"
PRE_SHA = "8518f9f1f7222eb3013cb3d971e1b84a55a31696df7b41a47a80cfa2fe1de76c"

A1_OLD = "var K_REPS='forge-reps'; /* install23 */"
A1_NEW = ("var K_REPS='forge-reps'; /* install23 */\n"
          "var K_VIDEO='forge-video'; /* install25 */")

A2_OLD = ("var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, "
          "K_PARKED, K_PROJ, K_REPS]; /* install23 */")
A2_NEW = ("var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, "
          "K_PARKED, K_PROJ, K_REPS, K_VIDEO]; /* install25 */")

# OR-wins: a completed audit can never be un-completed by a stale cloud copy.
A3_OLD = "  if (key === K_REPS) {                        /* install23: n only goes up, att is preserved */"
A3_NEW = """  if (key === K_VIDEO) {                       /* install25: done is sticky, never un-ticked */
    var lDone = !!(localVal && localVal.done === true);
    var cDone = !!(cloudVal && cloudVal.done === true);
    if (lDone || !cDone) return false;
    local[dk] = { done: true };
    return true;
  }

  if (key === K_REPS) {                        /* install23: n only goes up, att is preserved */"""

# the daily tick, appended inside install23's reps card
A4_OLD = """        <div class="field-label" style="margin:0 0 4px;">Where did your attention sit?</div>
        <div class="note-line" style="margin:0 0 6px;">On them, or on how you were coming across. No right answer &mdash; the noticing is the whole exercise.</div>
        <div class="pick-wrap" id="reps-att-picks"></div>
      </div>"""
A4_NEW = """        <div class="field-label" style="margin:0 0 4px;">Where did your attention sit?</div>
        <div class="note-line" style="margin:0 0 6px;">On them, or on how you were coming across. No right answer &mdash; the noticing is the whole exercise.</div>
        <div class="pick-wrap" id="reps-att-picks"></div>

        <!-- install25 -->
        <div style="border-top:1px solid rgba(74,157,232,.25); margin-top:14px; padding-top:12px;">
          <div class="field-label" style="margin:0 0 6px;">Video audit</div>
          <div class="pick-wrap" id="video-pick"></div>
          <div class="note-line" style="margin:6px 0 0;">Sixty seconds of yourself talking about something you care about, watched back. Twice a week for the first three weeks, then weekly.</div>
        </div>
      </div>"""

A5_OLD = "/* ---------- install23: social reps ---------- */"
A5_NEW = """/* ---------- install25: video audit ---------- */
function videoAll(){
  var v = fdRead(K_VIDEO, {});
  return (v && typeof v === 'object' && !Array.isArray(v)) ? v : {};
}
function videoDone(dk){
  var e = videoAll()[dk];
  return !!(e && typeof e === 'object' && e.done === true);
}
function videoToggle(){
  var dk = fdToday(), all = videoAll();
  if (videoDone(dk)) { delete all[dk]; }
  else { all[dk] = { done: true }; }
  var keys = Object.keys(all).sort();
  if (keys.length > 60){ var o = {}; keys.slice(-60).forEach(function(k){ o[k] = all[k]; }); all = o; }
  fdWrite(K_VIDEO, all);
  syncPush(K_VIDEO);
  paintVideo();
  try { renderWeeklyReview(); } catch (e) {}
}
function videoThisWeek(){
  var all = videoAll(), start = wkStart(new Date()), n = 0;
  for (var i = 0; i < 7; i++){
    var d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
    if (videoDone(fdYmd(d))) n++;
  }
  return n;
}
function paintVideo(){
  var host = document.getElementById('video-pick');
  if (!host) return;
  var on = videoDone(fdToday());
  host.innerHTML = '';
  var b = document.createElement('button');
  b.className = 'pick' + (on ? ' fam' : '');
  b.textContent = on ? '\\u2713 recorded and watched back' : 'did one today';
  b.onclick = videoToggle;
  host.appendChild(b);
}

/* ---------- install23: social reps ---------- */"""

A6_OLD = "  try { initReps(); } catch(e) {} /* install23 */"
A6_NEW = ("  try { initReps(); } catch(e) {} /* install23 */\n"
          "  try { paintVideo(); } catch(e) {} /* install25 */")

# checklist into the existing Sunday review card, above the note line
A7_OLD = """  h += '<div id="wr-note" style="font-size:11px; color:#ffc107; margin-top:8px;"></div>';
  h += '</div>';
  host.innerHTML = h;"""
A7_NEW = """  /* install25: the video audit checklist. REVIEW-ONLY - see the header comment. */
  var vw = videoThisWeek();
  h += '<div style="font-size:10px; letter-spacing:.1em; color:#8a93a8; margin:14px 0 6px;">VIDEO AUDIT &middot; ' + vw + ' THIS WEEK</div>';
  h += '<div style="font-size:12px; color:#f0f0f8; line-height:1.6;">';
  h += '1 &middot; Does your face move while you are <strong>listening</strong>? Most people only ever watch their talking face.<br>';
  h += '2 &middot; The first half-second after they start talking. That is where the reaction escapes or gets caught.<br>';
  h += '3 &middot; Vocal pitch range. A flat voice reads as flat affect whatever the face is doing.';
  h += '</div>';
  h += '<div style="font-size:11px; color:#ffc107; margin-top:8px; line-height:1.5;">Watch the tape against these. Never run them during a conversation &mdash; a list you carry into the room is the auditor, not the fix.</div>';

  h += '<div id="wr-note" style="font-size:11px; color:#ffc107; margin-top:8px;"></div>';
  h += '</div>';
  host.innerHTML = h;"""

EDITS = [
    ("K_VIDEO declaration", A1_OLD, A1_NEW),
    ("PULL_KEYS", A2_OLD, A2_NEW),
    ("fdMergeEntry OR-wins branch", A3_OLD, A3_NEW),
    ("daily tick markup", A4_OLD, A4_NEW),
    ("video functions", A5_OLD, A5_NEW),
    ("paintVideo call", A6_OLD, A6_NEW),
    ("Sunday review checklist", A7_OLD, A7_NEW),
]

MARKERS = ["install25", "K_VIDEO", "videoToggle", "videoThisWeek", "video-pick",
           "VIDEO AUDIT", "Never run them during a conversation"]


def main():
    if not os.path.exists(TARGET):
        sys.exit("FAIL: %s not found. Run this from the repo root." % TARGET)

    original = open(TARGET, "r", encoding="utf-8").read()
    sha = hashlib.sha256(original.encode("utf-8")).hexdigest()

    if "install25" in original:
        print("Already applied (install25 marker present). Nothing written.")
        return

    if "install23" not in original:
        sys.exit("FAIL: install23 has not been applied. Run forge_install23.py first.\n"
                 "File not modified.")

    if sha != PRE_SHA:
        sys.exit(
            "FAIL: pre-image mismatch.\n  expected %s\n  found    %s\n"
            "This must run on the install23 post-image, before any other edit.\n"
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

    body = text.split("function enoughVerdict")[1].split("\n}")[0]
    if "video" in body.lower():
        sys.exit("FAIL: video leaked into enoughVerdict(). File not modified.")

    shutil.copy2(TARGET, TARGET + ".install25.bak")
    open(TARGET, "w", encoding="utf-8").write(text)

    post = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print("\nWrote %s" % TARGET)
    print("  pre  %s" % sha)
    print("  post %s" % post)
    print("  backup: %s.install25.bak" % TARGET)


if __name__ == "__main__":
    main()

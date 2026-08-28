#!/usr/bin/env python3
"""
forge_logical_day_20260828.py

Fixes the after-midnight day-offset in the evening debrief.

Adds fdNow(): before 4 AM the clock is treated as still the previous night,
so a debrief done in the small hours reviews the day that just ended and
plans the day you are about to wake into - instead of jumping a day forward.
Also surfaces the planned date in the "Tomorrow's five" step so a wrong day
is visible before you sleep, never silent.

Debrief only. Hand-maintained file - NO workflow run needed after this.

PRE  (must match the live file): 3608d4bd9a0ca1c5ea937257acefa9c51b5a4c3c5e6ef7c89fd740fc496fe998
POST (verified build):           ff92278b7605f5dc40c57afadede485bf16a0c0edd27fb84b9d92a16c8e9df1f
"""

import hashlib, sys, os, datetime, shutil

TARGET   = "forge-evening-debrief.html"
PRE_SHA  = "3608d4bd9a0ca1c5ea937257acefa9c51b5a4c3c5e6ef7c89fd740fc496fe998"
POST_SHA = "ff92278b7605f5dc40c57afadede485bf16a0c0edd27fb84b9d92a16c8e9df1f"


def die(msg):
    print("ABORT:", msg)
    print("Nothing was written. Your file is untouched.")
    sys.exit(1)


if not os.path.exists(TARGET):
    die(TARGET + " not found. Run this from inside ~/Desktop/forge-daily-brief.")

with open(TARGET, "r", encoding="utf-8") as f:
    orig = f.read()

cur = hashlib.sha256(orig.encode("utf-8")).hexdigest()
if cur == POST_SHA:
    die("this patch is already applied (file already matches the POST image).")
if cur != PRE_SHA:
    die("the live file is not the expected base.\n"
        "  expected " + PRE_SHA + "\n"
        "  found    " + cur + "\n"
        "The debrief has changed since this patch was built. Do not force it - tell Clyde.")


def rep(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("anchor '" + label + "' matched " + str(n) + " times (need exactly 1). "
            "Likely a truncated paste of this installer - re-copy it whole.")
    return text.replace(old, new)


s = orig

# Edit 1 - fdNow() + logical fdToday/fdTomorrow
old1 = ("function fdToday(){ return fdYmd(new Date()); }\n"
        "function fdTomorrow(){ var d=new Date(); d.setDate(d.getDate()+1); return fdYmd(d); }")
new1 = ("function fdNow(){ /* debrief bleeds past midnight: before 4am counts as still the previous night */ var d=new Date(); if(d.getHours() < 4){ d.setDate(d.getDate()-1); } return d; }\n"
        "function fdToday(){ return fdYmd(fdNow()); }\n"
        "function fdTomorrow(){ var d=fdNow(); d.setDate(d.getDate()+1); return fdYmd(d); }")
s = rep(s, old1, new1, "fdToday/fdTomorrow helpers")

# Edit 2 - header date -> fdNow, and set the visible planning-target label
old2 = ("  document.getElementById('today-date').textContent = new Date().toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'});")
new2 = ("  document.getElementById('today-date').textContent = fdNow().toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'});\n"
        "  var _ptd=document.getElementById('plan-target-date'); if(_ptd){ var _pd=new Date(fdTomorrow()+'T00:00:00'); _ptd.textContent='Planning tomorrow: '+_pd.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'}); }")
s = rep(s, old2, new2, "init header date")

# Edit 3 - setTomorrowWorkout -> fdNow
old3 = ("  const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate()+1);")
new3 = ("  const tomorrow = fdNow(); tomorrow.setDate(tomorrow.getDate()+1);")
s = rep(s, old3, new3, "setTomorrowWorkout")

# Edit 4 - inject the visible planning-target element into step 08
old4 = ('      <div class="field-label" style="margin-bottom:2px;">Tomorrow&rsquo;s five</div>')
new4 = ('      <div id="plan-target-date" style="font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:#4a9de8; margin-bottom:8px;"></div>\n'
        '      <div class="field-label" style="margin-bottom:2px;">Tomorrow&rsquo;s five</div>')
s = rep(s, old4, new4, "plan-target-date element")

# Invariants
if (s.count("{") - s.count("}")) != (orig.count("{") - orig.count("}")):
    die("brace balance changed - internal error, not writing.")
if (s.count("(") - s.count(")")) != (orig.count("(") - orig.count(")")):
    die("paren balance changed - internal error, not writing.")
if s.count("function init()") != 1:
    die("init() invariant broke - internal error, not writing.")
for mk in ["GATE_AT", "saveDailyLog", "collectDaily", "saveTomorrow", "loadTodayTop5",
           "selectTag", "stressState", "domainState", "forge-daily-log"]:
    if mk not in s:
        die("a prior-install marker vanished: " + mk)

new_sha = hashlib.sha256(s.encode("utf-8")).hexdigest()
if new_sha != POST_SHA:
    die("result did not match the verified build.\n"
        "  expected " + POST_SHA + "\n"
        "  got      " + new_sha)

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
bak = TARGET + ".bak-" + stamp
shutil.copy2(TARGET, bak)

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(s)

check = hashlib.sha256(open(TARGET, "r", encoding="utf-8").read().encode("utf-8")).hexdigest()
if check != POST_SHA:
    shutil.copy2(bak, TARGET)
    die("post-write verification failed; restored your original from the backup.")

print("OK. Patched " + TARGET)
print("   backup : " + bak)
print("   new SHA: " + new_sha)
print("After-midnight debriefs (before 4 AM) now target the correct day.")

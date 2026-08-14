#!/usr/bin/env python3
"""
calfix_loud_errors_aug14.py  —  CALENDAR LOUD-FAILURE SAFEGUARD for the Forge brief.

WHAT IT DOES: patches forge_actions.py (the generator) so calendar failures that
were being silently swallowed now surface in the existing red CALENDAR FEED
PROBLEM banner. Three changes, both fetch functions + the banner:
  - a per-calendar lookup failure is logged with the calendar name + error type
  - unparseable events are counted and reported as one summary line per calendar
  - the banner de-duplicates repeats (same calendar hit across today/week/month/structured)
On the happy path the brief is byte-identical -- this only adds text when a
calendar actually fails.

WHAT IT DOES NOT DO: it does not touch the sleep logic, the debrief, or data.json,
it does not print a salary, and it needs NO Cloudflare paste. It BUILDS ON TOP of
the sleep fix (sleepfix_computed_aug14) -- its post-check asserts that fix survives.

This is NOT part of the forge_installNN.py series. Verify by SHA before running:
    shasum -a 256 calfix_loud_errors_aug14.py
must match the value given in chat.
"""

import hashlib, sys, os, py_compile, datetime

TARGET   = "forge_actions.py"
# PRE = the live generator AFTER the sleep fix. If yours differs, the sleep fix
# is not deployed or something else changed -- installer will refuse and say so.
PRE_SHA  = "8e09fe2dd9c87ebe12f84746b71c300c9fe8eba25a3c7495bb0c488104652c0d"
POST_SHA = "c888ab079a28a634a3315a25806eeb15ef7e6ca489ac51e9e54706e440621e35"

OLD1 = '''    for calendar in calendars:
        try:
            events = calendar.date_search(start=start, end=end, expand=True)
            for event in events:
                try:
                    vevent = event.vobject_instance.vevent
                    summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "Event"
                    dtstart = vevent.dtstart.value
                    if hasattr(dtstart, 'hour'):
                        all_events.append((str(dtstart), f"{summary} @ {dtstart.strftime('%a %b %d, %I:%M %p')}"))
                    else:
                        all_events.append((str(dtstart), f"{summary} — {dtstart.strftime('%a %b %d')} (All Day)"))
                except:
                    continue
        except:
            continue
    all_events.sort(key=lambda x: x[0])'''

NEW1 = '''    for calendar in calendars:
        _calname = getattr(calendar, "name", None) or "unknown"
        _bad_events = 0
        try:
            events = calendar.date_search(start=start, end=end, expand=True)
            for event in events:
                try:
                    vevent = event.vobject_instance.vevent
                    summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "Event"
                    dtstart = vevent.dtstart.value
                    if hasattr(dtstart, 'hour'):
                        all_events.append((str(dtstart), f"{summary} @ {dtstart.strftime('%a %b %d, %I:%M %p')}"))
                    else:
                        all_events.append((str(dtstart), f"{summary} — {dtstart.strftime('%a %b %d')} (All Day)"))
                except Exception:
                    _bad_events += 1
                    continue
        except Exception as e:
            CALENDAR_ERRORS.append(f"iCloud calendar '{_calname}': {type(e).__name__} {e}")
            continue
        if _bad_events:
            CALENDAR_ERRORS.append(f"iCloud calendar '{_calname}': {_bad_events} event(s) unparseable")
    all_events.sort(key=lambda x: x[0])'''

OLD2 = '''    for calendar in calendars:
        try:
            events = calendar.date_search(start=start, end=end, expand=True)
            for event in events:
                try:
                    vevent = event.vobject_instance.vevent
                    summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "Event"
                    dtstart = vevent.dtstart.value
                    if hasattr(dtstart, 'hour'):
                        all_events.append({
                            "sort_key": str(dtstart),
                            "date": dtstart.strftime('%a %b %d'),
                            "time": dtstart.strftime('%I:%M %p'),
                            "title": summary
                        })
                    else:
                        all_events.append({
                            "sort_key": str(dtstart),
                            "date": dtstart.strftime('%a %b %d'),
                            "time": "All day",
                            "title": summary
                        })
                except:
                    continue
        except:
            continue
    all_events.sort(key=lambda x: x["sort_key"])'''

NEW2 = '''    for calendar in calendars:
        _calname = getattr(calendar, "name", None) or "unknown"
        _bad_events = 0
        try:
            events = calendar.date_search(start=start, end=end, expand=True)
            for event in events:
                try:
                    vevent = event.vobject_instance.vevent
                    summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "Event"
                    dtstart = vevent.dtstart.value
                    if hasattr(dtstart, 'hour'):
                        all_events.append({
                            "sort_key": str(dtstart),
                            "date": dtstart.strftime('%a %b %d'),
                            "time": dtstart.strftime('%I:%M %p'),
                            "title": summary
                        })
                    else:
                        all_events.append({
                            "sort_key": str(dtstart),
                            "date": dtstart.strftime('%a %b %d'),
                            "time": "All day",
                            "title": summary
                        })
                except Exception:
                    _bad_events += 1
                    continue
        except Exception as e:
            CALENDAR_ERRORS.append(f"iCloud calendar '{_calname}': {type(e).__name__} {e}")
            continue
        if _bad_events:
            CALENDAR_ERRORS.append(f"iCloud calendar '{_calname}': {_bad_events} event(s) unparseable")
    all_events.sort(key=lambda x: x["sort_key"])'''

OLD3 = '''        _crows = "".join(f"<div>&#9888; {e}</div>" for e in CALENDAR_ERRORS)'''
NEW3 = '''        _crows = "".join(f"<div>&#9888; {e}</div>" for e in dict.fromkeys(CALENDAR_ERRORS))'''

def die(msg):
    print("ABORT:", msg)
    sys.exit(1)

if not os.path.exists(TARGET):
    die(f"{TARGET} not found. Are you in ~/Desktop/forge-daily-brief on gh-pages?")

with open(TARGET, encoding="utf-8") as f:
    src = f.read()

sha = hashlib.sha256(src.encode("utf-8")).hexdigest()
if sha == POST_SHA:
    die("Already installed (forge_actions.py matches the post-image). Nothing to do.")
if sha != PRE_SHA:
    die(f"Pre-image mismatch. Expected {PRE_SHA[:12]}..., got {sha[:12]}.... "
        "Either the sleep fix isn't deployed, or the generator changed. "
        "STOP -- tell Claude to rebuild from the current file.")

# The sleep fix must be present -- we build on top of it.
for marker, label in [("_cs_sitrep", "sleep fix (sitrep)"),
                      ("_cs_card", "sleep fix (card)"),
                      ("CALENDAR_ERRORS", "calendar error list")]:
    if src.count(marker) < 1:
        die(f"Expected marker missing: {label} ({marker}). Wrong base generator.")

for i, o in enumerate((OLD1, OLD2, OLD3), 1):
    if src.count(o) != 1:
        die(f"Anchor {i} found {src.count(o)} times, expected 1.")

patched = src.replace(OLD1, NEW1).replace(OLD2, NEW2).replace(OLD3, NEW3)

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = f"{TARGET}.calfix.bak-{stamp}"
with open(backup, "w", encoding="utf-8") as f:
    f.write(src)

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(patched)

try:
    py_compile.compile(TARGET, doraise=True)
except py_compile.PyCompileError as e:
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(src)
    die(f"Patched file failed to compile; restored original. {e}")

new_sha = hashlib.sha256(open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest()

problems = []
if patched.count("event(s) unparseable") != 2: problems.append("per-event logging not in both functions")
if patched.count("dict.fromkeys(CALENDAR_ERRORS)") != 1: problems.append("banner dedupe missing")
if "_cs_sitrep" not in patched or "_cs_card" not in patched: problems.append("sleep fix was lost")
if new_sha != POST_SHA: problems.append(f"post-image SHA mismatch (got {new_sha[:12]}...)")

if problems:
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(src)
    die("Post-check failed; restored original. " + "; ".join(problems))

print("calfix OK.")
print(f"  backup   : {backup}")
print(f"  post SHA : {new_sha}")
print("  sleep fix intact; calendar failures now surface in the red banner.")
print("")
print("NEXT (one command per line):")
print("  git add forge_actions.py calfix_loud_errors_aug14.py")
print("  git commit -m \"calfix: surface silent calendar failures in the error banner\"")
print("  git pull --rebase")
print("  git push")
print("Then GitHub -> Actions -> the workflow -> Run workflow -> branch gh-pages -> Run.")

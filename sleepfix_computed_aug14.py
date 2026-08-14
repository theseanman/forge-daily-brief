#!/usr/bin/env python3
"""
sleepfix_computed_aug14.py  —  SLEEP SCORE FIX for the Forge Daily Brief.

WHAT IT DOES: patches forge_actions.py (the generator) so the Sleep card, the
SITREP readiness line, and the red sleep banner PREFER sleep.computed_score
(from Health Auto Export) when it is present, falling back to the manual
sleep.score exactly as before. Output is byte-identical when no HAE data is
present. It does NOT touch the stored data.json field.

WHAT IT DOES NOT DO: it does not touch forge-evening-debrief.html, it does not
print a salary, it does not write forge-health-daily, and it needs NO Cloudflare
paste. If any of those appear when you run it, you are running the WRONG file.

This is NOT part of the forge_installNN.py series. Verify by SHA before running:
    shasum -a 256 sleepfix_computed_aug14.py
must match the value given in chat.
"""

import hashlib, sys, os, py_compile, datetime

TARGET   = "forge_actions.py"
PRE_SHA  = "13bb27058787c76ea95a11561aebb5f39f277f6dbc48e42f16ed9325e9d093ba"
POST_SHA = "8e09fe2dd9c87ebe12f84746b71c300c9fe8eba25a3c7495bb0c488104652c0d"

OLD1 = '    sleep_score = sleep.get("score", 80)\n'
NEW1 = (
    '    # sleepfix: prefer HAE computed_score when present; fall back to manual score.\n'
    '    _cs_sitrep = sleep.get("computed_score")\n'
    '    if isinstance(_cs_sitrep, (int, float)) and not sleep_is_missing(_cs_sitrep):\n'
    '        sleep_score = _cs_sitrep\n'
    '    else:\n'
    '        sleep_score = sleep.get("score", 80)\n'
)

OLD2 = '    _ss, _sd, _sh = sleep.get("score"), sleep.get("duration"), sleep.get("hr_range")\n'
NEW2 = (
    '    # sleepfix: prefer HAE computed_score for the card + banner; fall back to manual.\n'
    '    _cs_card = sleep.get("computed_score")\n'
    '    if isinstance(_cs_card, (int, float)) and not sleep_is_missing(_cs_card):\n'
    '        _ss = _cs_card\n'
    '    else:\n'
    '        _ss = sleep.get("score")\n'
    '    _sd, _sh = sleep.get("duration"), sleep.get("hr_range")\n'
)

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
        "The deployed generator is not the version this fix was built against. "
        "STOP -- do not proceed; tell Claude to rebuild from the current file.")

for marker, label in [("def sleep_is_missing", "sleep_is_missing helper"),
                      ("SLEEP_THRESHOLD = 90", "alert threshold")]:
    if src.count(marker) < 1:
        die(f"Expected pre-existing marker missing: {label} ({marker}).")

if src.count(OLD1) != 1:
    die(f"SITREP anchor found {src.count(OLD1)} times, expected 1.")
if src.count(OLD2) != 1:
    die(f"Card anchor found {src.count(OLD2)} times, expected 1.")

patched = src.replace(OLD1, NEW1).replace(OLD2, NEW2)

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = f"{TARGET}.sleepfix.bak-{stamp}"
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
if "_cs_sitrep" not in patched: problems.append("SITREP preference missing")
if "_cs_card" not in patched:   problems.append("card preference missing")
if patched.count("def sleep_is_missing") < 1: problems.append("sleep_is_missing helper lost")
if patched.count("SLEEP_THRESHOLD = 90") < 1: problems.append("alert threshold lost")
if new_sha != POST_SHA: problems.append(f"post-image SHA mismatch (got {new_sha[:12]}...)")

if problems:
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(src)
    die("Post-check failed; restored original. " + "; ".join(problems))

print("sleepfix OK.")
print(f"  backup   : {backup}")
print(f"  post SHA : {new_sha}")
print("  sleep_is_missing + alert threshold intact.")
print("")
print("NEXT (one command per line):")
print("  git add forge_actions.py sleepfix_computed_aug14.py")
print("  git commit -m \"sleepfix: prefer HAE computed_score on sleep card + sitrep\"")
print("  git pull --rebase")
print("  git push")
print("Then GitHub -> Actions -> the workflow -> Run workflow -> branch gh-pages -> Run.")

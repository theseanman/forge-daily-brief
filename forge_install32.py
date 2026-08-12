#!/usr/bin/env python3
"""
install32 — Sleep score alert on the Forge Daily Brief.

When today's sleep score is below SLEEP_THRESHOLD (90), a single plain line
renders above the SITREP card. When the score is 90+, or not recorded, nothing
shows. No new key, no Cloudflare paste, no storage.

TARGET   forge_actions.py   (THE GENERATOR — a workflow run is required after push)
MUST RUN AFTER install31. Aborts if install31 marker is absent.

Run from the repo root:
    cd ~/Desktop/forge-daily-brief
    python3 forge_install32.py
"""

import ast
import hashlib
import os
import sys

TARGET = "forge_actions.py"
PRE_SHA = "dc88d58067aee69e62621b98e22b8a2a522f445c004ee80d2c60df218d193de5"
MARKER = "install32"

# --- the Python-side variable, inserted after sleep_score_disp ---
PYTHON_BLOCK = (
    "\n"
    "    # install32: sleep alert above the SITREP when score < threshold.\n"
    "    SLEEP_THRESHOLD = 90\n"
    "    if (not _ss_missing) and isinstance(_ss, (int, float)) and _ss < SLEEP_THRESHOLD:\n"
    "        _sleep_alert = f'<div style=\"padding:10px 14px; margin-bottom:10px; border-radius:8px; background:rgba(200,60,60,0.15); border:1px solid rgba(200,60,60,0.35); font-size:14px; font-weight:600; color:var(--text-bright);\">Sleep score {_ss}% last night</div>'\n"
    "    else:\n"
    "        _sleep_alert = ''\n"
)

# --- the HTML-side injection, right above the SITREP card ---
HTML_INJECTION = "\n  {_sleep_alert}\n"


def die(msg):
    print("ABORT: " + msg)
    print("Nothing was written. " + TARGET + " is unchanged.")
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die(TARGET + " not found. Run this from the repo root (cd ~/Desktop/forge-daily-brief).")

    src = open(TARGET, encoding="utf-8").read()
    sha = hashlib.sha256(src.encode("utf-8")).hexdigest()

    if MARKER in src:
        print("Already applied — " + MARKER + " marker is present. Nothing to do.")
        sys.exit(0)

    if sha != PRE_SHA:
        die(
            "pre-image mismatch.\n"
            "  expected " + PRE_SHA + "\n"
            "  found    " + sha + "\n"
            "The deployed file has changed since this installer was built. Do not force it."
        )

    # --- ordering guard ---
    if "install31" not in src:
        die("install31 marker absent — run install31 first.")
    if "LIVE OR OVER" not in src:
        die("install31's LIVE OR OVER block is missing.")

    # --- EDIT 1: Python variable after sleep_score_disp ---
    py_anchor = '    sleep_score_disp = "NOT RECORDED" if _ss_missing else f"{_ss}%"'
    if src.count(py_anchor) != 1:
        die("Python anchor (sleep_score_disp) not unique: " + str(src.count(py_anchor)))

    out = src.replace(py_anchor, py_anchor + PYTHON_BLOCK, 1)

    # --- EDIT 2: HTML injection above the SITREP card ---
    html_anchor = (
        '\n  <div class="card" style="background: linear-gradient(135deg, rgba(0,0,0,0.25), rgba(30,10,0,0.2)); border: 3px solid var(--text-bright);">'
        '\n    <div class="card-header"><span class="card-icon">&#x1F4CB;&#x1F334;</span><span>FORGE SITREP</span></div>'
    )
    if out.count(html_anchor) != 1:
        die("HTML anchor (SITREP card) not unique: " + str(out.count(html_anchor)))

    out = out.replace(html_anchor, HTML_INJECTION + html_anchor, 1)

    # --- post-conditions ---
    if out == src:
        die("replacement produced no change.")
    if "SLEEP_THRESHOLD = 90" not in out:
        die("post-check: SLEEP_THRESHOLD not in output.")
    if out.count("_sleep_alert") < 3:
        die("post-check: _sleep_alert variable used fewer than 3 times (def + assign + template).")
    if "{_sleep_alert}" not in out:
        die("post-check: {_sleep_alert} not injected into the HTML template.")

    # Verify nothing else was disturbed
    for keep in ("FORGE SITREP", "LIVE OR OVER", "DECIDING", "pfCue()", "paintPractice",
                 "pullPractice", "pfReps()", "3 seconds", "7 breaths", "Hagakure"):
        if out.count(keep) != src.count(keep):
            die("post-check: existing content changed (" + keep + ").")

    try:
        ast.parse(out)
    except SyntaxError as e:
        die("post-check: patched file is not valid Python — " + str(e))

    # Write
    bak = TARGET + "." + MARKER + ".bak"
    with open(bak, "w", encoding="utf-8") as f:
        f.write(src)
    tmp = TARGET + ".tmp." + MARKER
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    os.replace(tmp, TARGET)

    post = hashlib.sha256(open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest()
    print("OK  " + TARGET + " patched.")
    print("    backup   " + bak)
    print("    pre-sha  " + PRE_SHA)
    print("    post-sha " + post)
    print("    threshold " + str(90))
    print("")
    print("This is the GENERATOR. Commit, push, then TRIGGER THE WORKFLOW.")
    print("Never hand-edit index.html.")


if __name__ == "__main__":
    main()

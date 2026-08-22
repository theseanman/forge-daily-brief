#!/usr/bin/env python3
"""
forge_anchors_card_20260821.py

Adds a "Today's Anchors" reminder card near the top of the brief.

Two bolded lines:
  - Breath before standing — hands on knees, one breath, then rise.
  - Breath before phone pickup — pause, breathe, then touch.

Auto-hides after 2026-09-04 (check-in date). No storage, no counter.

Placement: between the sleep alert and the Today's Five card.

SHA-gated against the post-brief-changes forge_actions.py.
Backs up, verifies compile, prints post-SHA.
"""

import hashlib
import ast
import shutil
import sys
import os
from datetime import datetime

TARGET = "forge_actions.py"
PRE_SHA256 = "09042bc10ecc108986ddf3b29abd8492373076eb17db30e14550133173f672ac"


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def die(msg):
    print(f"\n✗ ABORT: {msg}\n")
    sys.exit(1)


def replace_once(text, needle, repl, label):
    n = text.count(needle)
    if n != 1:
        die(f"anchor '{label}' matched {n} times (need exactly 1)")
    return text.replace(needle, repl, 1)


# ── EDIT 1 — build anchors_card variable in generate_html ─────────────────────
# Placed right after the CAD/JPY block, before the stoic pick.
EDIT_1_OLD = (
    "    else:\n"
    "        cad_jpy_html = f'\u00a5{_cadjpy_rate:.2f} <span style=\"opacity:0.55;\">(trigger \u2265\u00a5{CADJPY_TRIGGER:.0f})</span>'\n"
    "\n"
    "    stoic = STOIC_QUOTES[get_daily_index(len(STOIC_QUOTES))]\n"
)
EDIT_1_NEW = (
    "    else:\n"
    "        cad_jpy_html = f'\u00a5{_cadjpy_rate:.2f} <span style=\"opacity:0.55;\">(trigger \u2265\u00a5{CADJPY_TRIGGER:.0f})</span>'\n"
    "\n"
    "    # ── Today's Anchors card (auto-hides after 2026-09-04) ──────────────\n"
    "    ANCHORS_END = date(2026, 9, 4)\n"
    "    if now_pt().date() <= ANCHORS_END:\n"
    "        anchors_card = (\n"
    "            '<div class=\"card\" style=\"background:linear-gradient(135deg, rgba(74,157,232,0.22), rgba(74,157,232,0.08)); '\n"
    "            'border:2px solid #4a9de8; padding:14px 16px;\">'\n"
    "            '<div style=\"font-size:11px; letter-spacing:0.18em; text-transform:uppercase; '\n"
    "            'font-weight:800; color:#4a9de8; margin-bottom:10px;\">Today\\u2019s Anchors</div>'\n"
    "            '<div style=\"font-size:15px; line-height:1.6; color:var(--text-bright); margin-bottom:6px;\">'\n"
    "            '<b>Breath before standing</b> \\u2014 hands on knees, one breath, then rise.'\n"
    "            '</div>'\n"
    "            '<div style=\"font-size:15px; line-height:1.6; color:var(--text-bright);\">'\n"
    "            '<b>Breath before phone pickup</b> \\u2014 pause, breathe, then touch.'\n"
    "            '</div>'\n"
    "            '</div>'\n"
    "        )\n"
    "    else:\n"
    "        anchors_card = ''\n"
    "\n"
    "    stoic = STOIC_QUOTES[get_daily_index(len(STOIC_QUOTES))]\n"
)

# ── EDIT 2 — insert {anchors_card} into the template ─────────────────────────
EDIT_2_OLD = (
    "  {_sleep_alert}\n"
    "\n"
    "\n"
    "  <div class=\"card\">\n"
    "    <div class=\"card-header\"><span class=\"card-icon\">&#x1F3AF;&#x1F334;</span><span>Today&rsquo;s Five</span></div>\n"
)
EDIT_2_NEW = (
    "  {_sleep_alert}\n"
    "\n"
    "  {anchors_card}\n"
    "\n"
    "  <div class=\"card\">\n"
    "    <div class=\"card-header\"><span class=\"card-icon\">&#x1F3AF;&#x1F334;</span><span>Today&rsquo;s Five</span></div>\n"
)


def main():
    if not os.path.exists(TARGET):
        die(f"{TARGET} not found. cd into ~/Desktop/forge-daily-brief first.")

    got_sha = sha256_file(TARGET)
    if got_sha != PRE_SHA256:
        die(
            f"{TARGET} SHA mismatch.\n"
            f"     expected: {PRE_SHA256}\n"
            f"     got:      {got_sha}\n"
            f"     Ask for a rebuild against the current file."
        )

    with open(TARGET, "r", encoding="utf-8") as f:
        src = f.read()

    print(f"✓ SHA verified: {got_sha[:16]}\u2026")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{TARGET}.anchors_card_20260821.bak-{stamp}"
    shutil.copy2(TARGET, backup)
    print(f"✓ Backup: {backup}")

    out = src
    out = replace_once(out, EDIT_1_OLD, EDIT_1_NEW, "1: anchors_card variable")
    print("✓ Edit 1 applied: anchors_card built in generate_html")
    out = replace_once(out, EDIT_2_OLD, EDIT_2_NEW, "2: template insertion")
    print("✓ Edit 2 applied: {anchors_card} placed below sleep alert")

    try:
        ast.parse(out)
    except SyntaxError as e:
        die(f"POST syntax check failed: {e}")
    print("✓ ast.parse clean")

    open_b = out.count("{{") - src.count("{{")
    close_b = out.count("}}") - src.count("}}")
    if open_b != close_b:
        die(f"f-string brace balance drifted: {{{{ {open_b}, }}}} {close_b}")
    print(f"✓ f-string brace balance holds (delta {open_b}/{close_b})")

    assert "anchors_card" in out, "anchors_card not present"
    assert "ANCHORS_END" in out, "ANCHORS_END not present"
    assert "Today\\u2019s Anchors" in out or "Today\u2019s Anchors" in out, "card title missing"
    assert "{anchors_card}" in out, "template placeholder missing"

    for prior in ("computed_score", "CALENDAR_ERRORS", "syncPullBrief",
                  "install32", "FORGE_TZ", "week_structured",
                  "PARKED_CARDS", "repaintBrief", "fetch_cad_jpy",
                  "CADJPY_TRIGGER"):
        if prior not in out:
            die(f"prior install marker '{prior}' vanished")
    print("✓ Prior install markers intact (incl. CAD/JPY)")

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(out)
    new_sha = sha256_file(TARGET)
    print(f"\n✓ {TARGET} written: {len(out)} bytes")
    print(f"✓ POST SHA256: {new_sha}")
    print("\nNEXT:")
    print(f"  1. git add {TARGET} forge_anchors_card_20260821.py")
    print(f"  2. git commit -m 'brief: anchors reminder card (auto-hides Sept 5)'")
    print(f"  3. git pull --rebase")
    print(f"  4. git push")
    print(f"  5. Actions -> workflow -> Run workflow (gh-pages)")


if __name__ == "__main__":
    main()

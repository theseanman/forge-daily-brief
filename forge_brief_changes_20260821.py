#!/usr/bin/env python3
"""
forge_brief_changes_20260821.py

Four changes to forge_actions.py (the brief generator):

  1. REMOVE the FORGE SITREP card entirely.
  2. REFORMAT calendar event lines:
        old:  "Team meeting @ Wed Aug 22, 09:00 AM"
        new:  "Wed Aug 22 · 9:00 AM — Team meeting"
     and separate events with a blank line (join on "\\n\\n").
  3. ADD a CAD/JPY daily rate line, small standalone card
     placed right below the Sleep Report card. Bolded blue
     with a TRIGGER flag when the rate is >= 112.
  4. (concerts left alone per Sean's call)

SHA-gated: refuses to run against any forge_actions.py other
than the one this was built against. Backs up before writing,
verifies post-image compiles, prints a diff summary.

RUN: cd ~/Desktop/forge-daily-brief && python3 forge_brief_changes_20260821.py
"""

import hashlib
import ast
import shutil
import sys
import os
from datetime import datetime

TARGET = "forge_actions.py"
PRE_SHA256 = "eb424fd3739dc2836ed319d46afe721ceb7acc73dc327616a3f0f84e0e753cc3"


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def die(msg):
    print(f"\n✗ ABORT: {msg}\n")
    sys.exit(1)


def replace_once(text, needle, repl, label):
    """Assert exactly one match, then replace."""
    n = text.count(needle)
    if n != 1:
        die(f"anchor '{label}' matched {n} times (need exactly 1)")
    return text.replace(needle, repl, 1)


# ── EDIT A — calendar event format ────────────────────────────────────────────
# Turn "{summary} @ {Wed Aug 22, 09:00 AM}" into
#      "{Wed Aug 22} · {9:00 AM} — {summary}"
# All-day: "{Wed Aug 22} — {summary} (all day)"
EDIT_A_OLD = (
    "                    if hasattr(dtstart, 'hour'):\n"
    "                        all_events.append((str(dtstart), f\"{summary} @ {dtstart.strftime('%a %b %d, %I:%M %p')}\"))\n"
    "                    else:\n"
    "                        all_events.append((str(dtstart), f\"{summary} \u2014 {dtstart.strftime('%a %b %d')} (All Day)\"))\n"
)
EDIT_A_NEW = (
    "                    if hasattr(dtstart, 'hour'):\n"
    "                        all_events.append((str(dtstart), f\"{dtstart.strftime('%a %b %-d')} \u00b7 {dtstart.strftime('%-I:%M %p')} \u2014 {summary}\"))\n"
    "                    else:\n"
    "                        all_events.append((str(dtstart), f\"{dtstart.strftime('%a %b %-d')} \u2014 {summary} (all day)\"))\n"
)

# ── EDIT B — blank line between events ────────────────────────────────────────
# Join on "\n\n" so events render with one blank line between them in the
# <pre style="white-space:pre-wrap"> blocks that host cal_today / cal_week /
# cal_month.
EDIT_B_OLD = (
    '            "today": "\\n".join(today_events) if today_events else "No events today.",\n'
    '            "week": "\\n".join(week_events) if week_events else "No events this week.",\n'
    '            "month": "\\n".join(month_events) if month_events else "No events this month.",\n'
)
EDIT_B_NEW = (
    '            "today": "\\n\\n".join(today_events) if today_events else "No events today.",\n'
    '            "week": "\\n\\n".join(week_events) if week_events else "No events this week.",\n'
    '            "month": "\\n\\n".join(month_events) if month_events else "No events this month.",\n'
)

# ── EDIT E — subscribed ICS labels use same new format ───────────────────────
EDIT_E_OLD = (
    "                    if _re.match(r\"^\\d{8}$\", dtstart_raw):\n"
    "                        dt = datetime.strptime(dtstart_raw, \"%Y%m%d\").date()\n"
    "                        dt_sort = datetime.combine(dt, datetime.min.time()).replace(tzinfo=PT)\n"
    "                        label = f\"{summary} -- {dt.strftime('%a %b %d')} (All Day) [{feed_name}]\"\n"
    "                    elif dtstart_raw.endswith(\"Z\"):\n"
    "                        dt_sort = datetime.strptime(dtstart_raw, \"%Y%m%dT%H%M%SZ\").replace(tzinfo=_tz.utc).astimezone(PT)\n"
    "                        label = f\"{summary} @ {dt_sort.strftime('%a %b %d, %I:%M %p')} [{feed_name}]\"\n"
    "                    elif \"T\" in dtstart_raw and len(dtstart_raw) >= 15:\n"
    "                        dt_sort = datetime.strptime(dtstart_raw[:15], \"%Y%m%dT%H%M%S\").replace(tzinfo=PT)\n"
    "                        label = f\"{summary} @ {dt_sort.strftime('%a %b %d, %I:%M %p')} [{feed_name}]\"\n"
)
EDIT_E_NEW = (
    "                    if _re.match(r\"^\\d{8}$\", dtstart_raw):\n"
    "                        dt = datetime.strptime(dtstart_raw, \"%Y%m%d\").date()\n"
    "                        dt_sort = datetime.combine(dt, datetime.min.time()).replace(tzinfo=PT)\n"
    "                        label = f\"{dt.strftime('%a %b %-d')} \u2014 {summary} (all day) [{feed_name}]\"\n"
    "                    elif dtstart_raw.endswith(\"Z\"):\n"
    "                        dt_sort = datetime.strptime(dtstart_raw, \"%Y%m%dT%H%M%SZ\").replace(tzinfo=_tz.utc).astimezone(PT)\n"
    "                        label = f\"{dt_sort.strftime('%a %b %-d')} \u00b7 {dt_sort.strftime('%-I:%M %p')} \u2014 {summary} [{feed_name}]\"\n"
    "                    elif \"T\" in dtstart_raw and len(dtstart_raw) >= 15:\n"
    "                        dt_sort = datetime.strptime(dtstart_raw[:15], \"%Y%m%dT%H%M%S\").replace(tzinfo=PT)\n"
    "                        label = f\"{dt_sort.strftime('%a %b %-d')} \u00b7 {dt_sort.strftime('%-I:%M %p')} \u2014 {summary} [{feed_name}]\"\n"
)

# ── EDIT C — remove SITREP card ──────────────────────────────────────────────
# The whole card block. sleep_alert stays above it; today's-five stays below.
# sitrep_text is still computed upstream — harmless, and touching that would
# widen the blast radius unnecessarily.
EDIT_C_OLD = (
    '  <div class="card" style="background: linear-gradient(135deg, rgba(0,0,0,0.25), rgba(30,10,0,0.2)); border: 3px solid var(--text-bright);">\n'
    '    <div class="card-header"><span class="card-icon">&#x1F4CB;&#x1F334;</span><span>FORGE SITREP</span></div>\n'
    '    <div style="display:flex; flex-direction:row; gap:16px; align-items:flex-start;">\n'
    '      <img src="https://theseanman.github.io/forge-daily-brief/hannibal.jpg"\n'
    '           alt="Hannibal Smith"\n'
    '           style="width:90px; min-width:90px; border-radius:8px; border:3px solid var(--text-bright); object-fit:cover;"\n'
    '           onerror="this.style.display=\'none\'; this.nextElementSibling.style.marginLeft=\'0\'">\n'
    '      <div style="font-size:15px; color:var(--text-bright); line-height:1.9; font-weight:600; flex:1; min-width:0;">{sitrep_text}</div>\n'
    '    </div>\n'
    '  </div>\n'
)
EDIT_C_NEW = ""  # remove entirely

# ── EDIT D1 — fetch_cad_jpy() helper, inserted just before generate_sitrep ───
# Primary source: fawazahmed0's currency-api (free, no key, CDN-hosted).
# Fallback: open.er-api.com. If both fail, returns (None, "unavailable").
EDIT_D1_OLD = 'def generate_sitrep(welltory, sleep, calendar_events, weather, reminders=None):\n'
EDIT_D1_NEW = (
    'def fetch_cad_jpy():\n'
    '    """Return (rate_float, source_label) or (None, "unavailable").\n'
    '    Rate is JPY per 1 CAD. Two independent sources, quiet fallback.\n'
    '    """\n'
    '    _urls = [\n'
    '        ("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/cad.json",\n'
    '         lambda d: d.get("cad", {}).get("jpy")),\n'
    '        ("https://open.er-api.com/v6/latest/CAD",\n'
    '         lambda d: d.get("rates", {}).get("JPY")),\n'
    '    ]\n'
    '    for url, extract in _urls:\n'
    '        try:\n'
    '            req = urllib.request.Request(url, headers={"User-Agent": "forge-brief/1.0"})\n'
    '            with urllib.request.urlopen(req, timeout=8) as r:\n'
    '                data = json.loads(r.read().decode("utf-8"))\n'
    '            rate = extract(data)\n'
    '            if isinstance(rate, (int, float)) and rate > 0:\n'
    '                return (float(rate), url.split("/")[2])\n'
    '        except Exception as e:\n'
    '            print(f"  CAD/JPY fetch failed for {url.split(\'/\')[2]}: {type(e).__name__} {e}")\n'
    '            continue\n'
    '    return (None, "unavailable")\n'
    '\n'
    'def generate_sitrep(welltory, sleep, calendar_events, weather, reminders=None):\n'
)

# ── EDIT D2 — build cad_jpy_html in generate_html ────────────────────────────
# Insert right after the sbos_signals_html block, before the stoic pick.
EDIT_D2_OLD = (
    "        sbos_signals_html = '<div class=\"mini-card\"><div class=\"mini-detail\">No EV signals in next 48h. Check Telegram for CFL alerts.</div></div>'\n"
    "\n"
    "    stoic = STOIC_QUOTES[get_daily_index(len(STOIC_QUOTES))]\n"
)
EDIT_D2_NEW = (
    "        sbos_signals_html = '<div class=\"mini-card\"><div class=\"mini-detail\">No EV signals in next 48h. Check Telegram for CFL alerts.</div></div>'\n"
    "\n"
    "    # ── CAD/JPY daily rate ──────────────────────────────────────────────\n"
    "    _cadjpy_rate, _cadjpy_src = fetch_cad_jpy()\n"
    "    CADJPY_TRIGGER = 112.0\n"
    "    if _cadjpy_rate is None:\n"
    "        cad_jpy_html = '<span style=\"opacity:0.6;\">unavailable</span>'\n"
    "    elif _cadjpy_rate >= CADJPY_TRIGGER:\n"
    "        cad_jpy_html = (\n"
    "            f'<strong style=\"color:#4a9de8; font-size:16px;\">'\n"
    "            f'\u00a5{_cadjpy_rate:.2f} \u00b7 \U0001F3AF TRIGGER (\u2265\u00a5{CADJPY_TRIGGER:.0f})'\n"
    "            f'</strong>'\n"
    "        )\n"
    "    else:\n"
    "        cad_jpy_html = f'\u00a5{_cadjpy_rate:.2f} <span style=\"opacity:0.55;\">(trigger \u2265\u00a5{CADJPY_TRIGGER:.0f})</span>'\n"
    "\n"
    "    stoic = STOIC_QUOTES[get_daily_index(len(STOIC_QUOTES))]\n"
)

# ── EDIT D3 — CAD/JPY card in HTML, right below Sleep Report ─────────────────
# Anchor: the Sleep Report card's closing pattern (sleep_missing_note + </div>),
# followed by the blank line and {practice_card}.
EDIT_D3_OLD = (
    "    {sleep_missing_note}\n"
    "  </div>\n"
    "\n"
    "{practice_card}\n"
)
EDIT_D3_NEW = (
    "    {sleep_missing_note}\n"
    "  </div>\n"
    "\n"
    "  <div class=\"card\" style=\"padding:12px 16px;\">\n"
    "    <div style=\"font-size:14px; color:var(--text-light);\">CAD/JPY: {cad_jpy_html}</div>\n"
    "  </div>\n"
    "\n"
    "{practice_card}\n"
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
            f"     The generator has moved since this installer was built. "
            f"Do not run — ask for a rebuild against the current file."
        )

    with open(TARGET, "r", encoding="utf-8") as f:
        src = f.read()

    print(f"✓ SHA verified: {got_sha[:16]}\u2026")
    print(f"✓ Source: {len(src)} bytes")

    # Backup
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{TARGET}.brief_changes_20260821.bak-{stamp}"
    shutil.copy2(TARGET, backup)
    print(f"✓ Backup: {backup}")

    # Apply edits in order
    out = src
    out = replace_once(out, EDIT_A_OLD, EDIT_A_NEW, "A: calendar event format")
    print("✓ Edit A applied: calendar event format")
    out = replace_once(out, EDIT_B_OLD, EDIT_B_NEW, "B: join separator")
    print("✓ Edit B applied: blank line between events")
    out = replace_once(out, EDIT_E_OLD, EDIT_E_NEW, "E: ICS labels new format")
    print("✓ Edit E applied: subscribed ICS labels reformatted")
    out = replace_once(out, EDIT_C_OLD, EDIT_C_NEW, "C: remove SITREP card")
    print("✓ Edit C applied: SITREP card removed")
    out = replace_once(out, EDIT_D1_OLD, EDIT_D1_NEW, "D1: fetch_cad_jpy helper")
    print("✓ Edit D1 applied: fetch_cad_jpy() added")
    out = replace_once(out, EDIT_D2_OLD, EDIT_D2_NEW, "D2: build cad_jpy_html")
    print("✓ Edit D2 applied: cad_jpy_html built in generate_html")
    out = replace_once(out, EDIT_D3_OLD, EDIT_D3_NEW, "D3: CAD/JPY card in HTML")
    print("✓ Edit D3 applied: CAD/JPY card placed below Sleep Report")

    # Post-checks
    try:
        ast.parse(out)
    except SyntaxError as e:
        die(f"POST syntax check failed: {e}")
    print("✓ ast.parse clean")

    # Invariant: brace balance in the entire file didn't drift
    open_b = out.count("{{") - src.count("{{")
    close_b = out.count("}}") - src.count("}}")
    if open_b != close_b:
        die(f"f-string brace balance drifted: {{{{ delta {open_b}, }}}} delta {close_b}")
    print(f"✓ f-string brace balance holds (delta {open_b}/{close_b})")

    # Marker checks (fail loudly if any target didn't take)
    # SITREP card is gone; the generate_sitrep() docstring stays (harmless).
    assert "<span>FORGE SITREP</span>" not in out, "SITREP card header still present"
    assert '{sitrep_text}' not in out, "SITREP text placeholder still present"
    assert "fetch_cad_jpy" in out, "fetch_cad_jpy not present"
    assert "cad_jpy_html" in out, "cad_jpy_html not present"
    assert "CADJPY_TRIGGER" in out, "CADJPY_TRIGGER not present"
    # New event format present in fetch_events_for_range
    assert "%-I:%M %p" in out, "new time format not present"
    # Old brief-text format is gone from fetch_events_for_range (the tuple appender).
    # fetch_events_structured LEGITIMATELY keeps %a %b %d / %I:%M %p — it feeds the
    # planner's date/time/title dicts, which are a separate concern.
    assert "{summary} @ {dtstart.strftime" not in out, "old brief-text timed format still present"
    assert "(All Day)" not in out, "old (All Day) suffix still present somewhere"
    assert "{summary} -- {" not in out, "old '--' separator still present in ICS labels"
    print("✓ All markers verified")

    # Prior installs' fingerprints preserved (markers that live in this file)
    for prior in ("computed_score", "CALENDAR_ERRORS", "syncPullBrief",
                  "install32", "FORGE_TZ", "week_structured",
                  "PARKED_CARDS", "repaintBrief"):
        if prior not in out:
            die(f"prior install marker '{prior}' vanished")
    print("✓ Prior install markers intact")

    # Write
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(out)
    new_sha = sha256_file(TARGET)
    print(f"\n✓ {TARGET} written: {len(out)} bytes")
    print(f"✓ POST SHA256: {new_sha}")
    print("\nNEXT:")
    print(f"  1. git status --short    (should show M {TARGET})")
    print(f"  2. git add {TARGET}")
    print(f"  3. git pull --rebase")
    print(f"  4. git commit -m 'brief: drop sitrep, reformat calendar, add cad/jpy'")
    print(f"  5. git push")
    print(f"  6. Actions tab -> workflow -> Run workflow (branch: gh-pages)")
    print(f"  7. After the run, curl the gh-pages archive and check that:")
    print(f"     - index.html has no 'FORGE SITREP' string")
    print(f"     - index.html has 'CAD/JPY:'")


if __name__ == "__main__":
    main()

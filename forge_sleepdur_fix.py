#!/usr/bin/env python3
"""
forge_sleepdur_fix.py  -  the Sleep card's Duration line falls back to duration_min,
shown as hours and minutes, when the old `duration` string field is null.

WHY: /sleep-import writes duration_min (e.g. 708) but leaves the legacy `duration`
string null, so the card's Duration reads "—" even though the data is present.
The stage rows (REM/Core/Deep) already format as "Xh Ym"; this makes Duration match.

WHAT (patches forge_actions.py, the GENERATOR -> needs a workflow run):
  one line changed; nothing else touched. No effect on any night that already has a
  real `duration` string (that value still wins).

SAFETY: refuses unless PRE hash matches; backs up first; restores on any post-check
failure; second run refuses.
"""
import hashlib, sys, os, subprocess, datetime

TARGET  = "forge_actions.py"
PRE_SHA = "791f99d0bc4e87337d90dbdc07fe7b5053b51bdb089c7166aca86c56e63a0caa"

A_OLD = '    sleep_dur_disp = "—" if (_sd is None or str(_sd).strip() in ("", "-")) else str(_sd)'
A_NEW = (
'    _dm = sleep.get("duration_min")\n'
'    if _sd is not None and str(_sd).strip() not in ("", "-"):\n'
'        sleep_dur_disp = str(_sd)\n'
'    elif isinstance(_dm, (int, float)) and _dm > 0:\n'
'        _dh, _dmm = divmod(int(round(float(_dm))), 60)\n'
'        sleep_dur_disp = f"{_dh}h {_dmm}m" if _dh else f"{_dmm}m"\n'
'    else:\n'
'        sleep_dur_disp = "—"'
)

def die(m): print("ABORT:", m); sys.exit(1)

def main():
    if not os.path.exists(TARGET): die(f"{TARGET} not found - run from ~/Desktop/forge-daily-brief on gh-pages")
    orig = open(TARGET, encoding="utf-8").read()
    got = hashlib.sha256(orig.encode()).hexdigest()
    if got != PRE_SHA:
        die(f"PRE hash mismatch.\n  expected {PRE_SHA}\n  got      {got}\nTargets the current live generator only.")
    if orig.count(A_OLD) != 1: die(f"anchor found {orig.count(A_OLD)}x (expected 1) - refusing to guess")
    new = orig.replace(A_OLD, A_NEW)

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{TARGET}.sleepdurbak-{stamp}"
    open(bak, "w", encoding="utf-8").write(orig)
    open(TARGET, "w", encoding="utf-8").write(new)

    def restore(why):
        open(TARGET, "w", encoding="utf-8").write(orig)
        die(f"post-check failed ({why}) - {TARGET} restored, backup at {bak}")

    r = subprocess.run([sys.executable, "-m", "py_compile", TARGET], capture_output=True, text=True)
    if r.returncode != 0: restore("py_compile: " + r.stderr.strip()[:200])
    for m in ('_dm = sleep.get("duration_min")', 'f"{_dh}h {_dmm}m"'):
        if m not in new: restore(f"marker missing: {m}")

    post = hashlib.sha256(new.encode()).hexdigest()
    print("OK  forge_actions.py patched.")
    print("    backup :", bak)
    print("    PRE    :", PRE_SHA)
    print("    POST   :", post)
    print("\nNext: git pull --rebase ; add forge_actions.py + this installer ; commit ; push ; RUN THE WORKFLOW.")

if __name__ == "__main__":
    main()

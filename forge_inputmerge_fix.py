#!/usr/bin/env python3
"""
forge_inputmerge_fix.py  -  stop the Forge Log form from wiping auto-imported
sleep and weight.

THE BUG: input.html's submit posts the whole form to the Worker ROOT, which is a
WHOLESALE replace of data.json. Blank sleep / body_comp fields go in as null, so
submitting the form erases the sleep and weight that Health Auto Export just wrote.

THE FIX: point the submit at /brief-patch (the merge route) instead of root. The
merge overlays only non-null fields, so blank sleep/body_comp are skipped and the
auto-imported values survive. HRV/Welltory you type still saves; manual sleep entry
still works when you want it; the calendar stops being clobbered too.

One line changed in input.html (hand-maintained -> deploys on push, NO workflow run).
Anchor-based (not full-file SHA) because the exact deployed bytes weren't fetchable
this session; it asserts the target line is present exactly once and verifies the result.

SAFETY: backs up first; refuses if the anchor isn't found or is already patched;
restores on any post-check failure.
"""
import sys, os, datetime

TARGET = "input.html"
OLD = "  fetch('https://forge-input.yoseanreid.workers.dev', {"
NEW = "  fetch('https://forge-input.yoseanreid.workers.dev/brief-patch', {"

def die(m): print("ABORT:", m); sys.exit(1)

def main():
    if not os.path.exists(TARGET):
        die(f"{TARGET} not found - run from ~/Desktop/forge-daily-brief on gh-pages")
    orig = open(TARGET, encoding="utf-8").read()

    if NEW in orig:
        die("already patched (submit already points at /brief-patch) - nothing to do")
    c = orig.count(OLD)
    if c != 1:
        die(f"submit anchor found {c}x (expected exactly 1) - refusing to guess.\n"
            "The deployed input.html differs from what was expected; tell me and I'll re-check.")

    new = orig.replace(OLD, NEW)

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{TARGET}.mergefixbak-{stamp}"
    open(bak, "w", encoding="utf-8").write(orig)
    open(TARGET, "w", encoding="utf-8").write(new)

    def restore(why):
        open(TARGET, "w", encoding="utf-8").write(orig)
        die(f"post-check failed ({why}) - {TARGET} restored, backup at {bak}")

    if new.count(NEW) != 1: restore("new submit line not present exactly once")
    if new.count(OLD) != 0: restore("old root-post line still present")
    # sanity: the file should be unchanged apart from that one URL (length grows by len('/brief-patch'))
    if len(new) - len(orig) != len("/brief-patch"): restore("unexpected size delta - more than the URL changed")
    for must in ("var brief=", "showStatus('Saved!", "</html>"):
        if must not in new: restore(f"file integrity check failed: missing {must!r}")

    print("OK  input.html patched — the form now MERGES instead of overwriting.")
    print("    backup :", bak)
    print("    change : submit -> /brief-patch (was: root / wholesale replace)")
    print("    bytes  :", len(orig.encode()), "->", len(new.encode()))
    print("\nNext: git pull --rebase ; git add input.html forge_inputmerge_fix.py ; commit ; push. NO workflow run.")

if __name__ == "__main__":
    main()

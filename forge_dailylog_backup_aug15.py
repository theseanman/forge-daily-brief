#!/usr/bin/env python3
"""
forge_dailylog_backup_aug15.py  -  cloud backup + restore for forge-daily-log
(the correlation record written each night by the evening debrief).

WHAT IT DOES (patches forge-evening-debrief.html only -- hand-maintained, NO workflow run):
  1. syncPush('forge-daily-log') after each nightly log write, so every debrief backs it up.
  2. Adds forge-daily-log to the debrief PULL_KEYS, so a fresh device or a wiped jar
     restores the whole correlation history on load.
  3. A dedicated merge rule for the log in fdMergeEntry: NEWEST-WINS by each record's
     `saved` ISO timestamp. A real debrief record (has `saved`) always beats a stale
     cloud copy or a backfill stub (no `saved`). Dates are unioned, never dropped.

REQUIRES ONE CLOUDFLARE PASTE (forge-sync Worker): add 'forge-daily-log' to KEYS, or the
push returns 400 (the log still saves locally -- no data loss, just no backup until then).

SAFETY: refuses unless the PRE hash matches; backs up first; restores on any post-check
failure; a second run refuses (PRE hash no longer matches).
"""
import hashlib, sys, os, subprocess, datetime

TARGET  = "forge-evening-debrief.html"
PRE_SHA = "d310119ccbe8c6094b05ce1a25a93da7e378d747baa8c2a60f6a452f2be02df8"

# ---- 1. PULL_KEYS: add K_DAILY ----
A_OLD = "var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, K_PARKED, K_PROJ, K_REPS, K_VIDEO, K_PROTO]; /* install25 + tally_pull_key_aug14 */"
A_NEW = "var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, K_PARKED, K_PROJ, K_REPS, K_VIDEO, K_PROTO, K_DAILY]; /* install25 + tally_pull_key_aug14 + dailylog_backup */"

# ---- 2. fdMergeEntry: newest-wins-by-`saved` case for the daily log, before the generic guard ----
B_OLD = "  if (fdBlank(cloudVal) && !fdBlank(localVal)) return false;   /* the guard */"
B_NEW = (
"  if (key === K_DAILY) {                       /* dailylog_backup: newest `saved` wins, never drop a date */\n"
"    var lt = (localVal && typeof localVal.saved === 'string') ? localVal.saved : '';\n"
"    var ct = (cloudVal && typeof cloudVal.saved === 'string') ? cloudVal.saved : '';\n"
"    if (!cloudVal || typeof cloudVal !== 'object') return false;\n"
"    if (localVal === undefined) { local[dk] = cloudVal; return true; }  /* a day we don't have yet */\n"
"    if (ct > lt) { local[dk] = cloudVal; return true; }                 /* cloud is newer */\n"
"    return false;                                                       /* local same-or-newer wins */\n"
"  }\n"
"\n"
"  if (fdBlank(cloudVal) && !fdBlank(localVal)) return false;   /* the guard */"
)

# ---- 3. push after the primary log write ----
C_OLD = (
"  fdWrite(K_DAILY, log);\n"
"\n"
"  /* attach this morning's health numbers once data.json answers */"
)
C_NEW = (
"  fdWrite(K_DAILY, log);\n"
"  try { syncPush(K_DAILY); } catch (e) {}   /* dailylog_backup */\n"
"\n"
"  /* attach this morning's health numbers once data.json answers */"
)

# ---- 4. push again after the async health-attach write (so the health-enriched record is backed up) ----
D_OLD = "      if (lg[rec.d]){ lg[rec.d].health = h; fdWrite(K_DAILY, lg); }"
D_NEW = "      if (lg[rec.d]){ lg[rec.d].health = h; fdWrite(K_DAILY, lg); try { syncPush(K_DAILY); } catch (e) {} }  /* dailylog_backup */"

def die(m): print("ABORT:", m); sys.exit(1)

def main():
    if not os.path.exists(TARGET):
        die(f"{TARGET} not found - run from ~/Desktop/forge-daily-brief on gh-pages")
    orig = open(TARGET, encoding="utf-8").read()
    got = hashlib.sha256(orig.encode()).hexdigest()
    if got != PRE_SHA:
        die(f"PRE hash mismatch.\n  expected {PRE_SHA}\n  got      {got}\nTargets the current live debrief only.")
    for nm, old in [("A", A_OLD), ("B", B_OLD), ("C", C_OLD), ("D", D_OLD)]:
        c = orig.count(old)
        if c != 1: die(f"anchor {nm} found {c}x (expected 1) - refusing to guess")
    new = orig.replace(A_OLD, A_NEW).replace(B_OLD, B_NEW).replace(C_OLD, C_NEW).replace(D_OLD, D_NEW)

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = f"{TARGET}.dailylogbak-{stamp}"
    open(bak, "w", encoding="utf-8").write(orig)
    open(TARGET, "w", encoding="utf-8").write(new)

    def restore(why):
        open(TARGET, "w", encoding="utf-8").write(orig)
        die(f"post-check failed ({why}) - {TARGET} restored, backup at {bak}")

    for marker in ("K_PROTO, K_DAILY]", "if (key === K_DAILY) {", "try { syncPush(K_DAILY); } catch (e) {}"):
        if marker not in new: restore(f"marker missing: {marker}")
    if new.count("syncPush(K_DAILY)") != 2: restore("expected exactly 2 K_DAILY push sites")

    post = hashlib.sha256(new.encode()).hexdigest()
    print("OK  forge-evening-debrief.html patched.")
    print("    backup :", bak)
    print("    PRE    :", PRE_SHA)
    print("    POST   :", post)
    print("    bytes  :", len(orig.encode()), "->", len(new.encode()))
    print("\nNext: git pull --rebase ; stage the debrief + this installer ; commit ; push. NO workflow run.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# tally_pull_key_aug14.py
#
# WHAT THIS DOES (two additive edits to forge-evening-debrief.html):
#   1. Adds K_PROTO to PULL_KEYS, so opening the debrief on a DIFFERENT device
#      than the tally still pulls the day's live protocol counts from the cloud.
#      (Same device already shares localStorage — this is only for phone->Mac.)
#   2. Repaints the protocol counters after a pull lands, so a slow sync can't
#      leave step 6 showing stale zeros.
#
# It is a PATCHER, not a payload. It replaces two exact strings and refuses to
# run unless the file it finds is byte-for-byte the version this was built against.
#
# Run from ~/Desktop/forge-daily-brief on the gh-pages branch:
#     shasum -a 256 tally_pull_key_aug14.py     # compare to the value Claude stated
#     python3 tally_pull_key_aug14.py
#
import hashlib, os, sys, time

TARGET = "forge-evening-debrief.html"

PRE_SHA  = "88224bf35ddd254b5c339d89a865a905faa30d7cc387d16219597e0e53b11926"
POST_SHA = "d310119ccbe8c6094b05ce1a25a93da7e378d747baa8c2a60f6a452f2be02df8"

EDIT1_OLD = "var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, K_PARKED, K_PROJ, K_REPS, K_VIDEO]; /* install25 */"
EDIT1_NEW = "var PULL_KEYS = [K_TOP5, K_ROCKS, K_FRAME, K_MUSHIN, K_BACKLOG, K_FUN, K_PARKED, K_PROJ, K_REPS, K_VIDEO, K_PROTO]; /* install25 + tally_pull_key_aug14 */"

EDIT2_OLD = "    if (touched) { try { loadTodayTop5(); } catch (e) {} try { renderWeeklyReview(); } catch (e) {} }"
EDIT2_NEW = "    if (touched) { try { loadTodayTop5(); } catch (e) {} try { renderWeeklyReview(); } catch (e) {} try { protoLoad(); } catch (e) {} }"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def die(msg):
    print("ABORT: " + msg)
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die("%s not found. Run this from ~/Desktop/forge-daily-brief on gh-pages." % TARGET)

    raw = open(TARGET, "rb").read()
    got = sha(raw)
    if got != PRE_SHA:
        die("%s is not the expected version.\n  expected pre-SHA %s\n  found          %s\n"
            "Nothing was written. This means the live file has changed since the patch was built."
            % (TARGET, PRE_SHA, got))

    text = raw.decode("utf-8")

    for label, old in (("PULL_KEYS", EDIT1_OLD), ("pull-repaint", EDIT2_OLD)):
        n = text.count(old)
        if n != 1:
            die("anchor '%s' matched %d times, expected exactly 1. Nothing written." % (label, n))

    # already patched? refuse rather than double-apply
    if "K_PROTO]; /* install25 + tally_pull_key_aug14 */" in text:
        die("This patch is already applied. Nothing to do.")

    out = text.replace(EDIT1_OLD, EDIT1_NEW).replace(EDIT2_OLD, EDIT2_NEW)
    out_bytes = out.encode("utf-8")

    # post-conditions
    if out_bytes.decode("utf-8").count(", K_PROTO]; /* install25 + tally_pull_key_aug14 */") != 1:
        die("post-check: PULL_KEYS edit not present exactly once. Nothing written.")
    if out_bytes.decode("utf-8").count("try { protoLoad(); } catch (e) {} }") != 1:
        die("post-check: pull-repaint edit not present exactly once. Nothing written.")

    got_post = sha(out_bytes)
    if POST_SHA != "@@" + "POST_SHA@@" and got_post != POST_SHA:
        die("post-SHA mismatch.\n  expected %s\n  computed %s\nNothing written." % (POST_SHA, got_post))

    backup = TARGET + ".tallypull.bak-" + time.strftime("%Y%m%d-%H%M%S")
    open(backup, "wb").write(raw)
    open(TARGET, "wb").write(out_bytes)

    print("OK.")
    print("  backup:   " + backup)
    print("  pre-SHA:  " + got)
    print("  post-SHA: " + got_post)
    print("  bytes:    %d -> %d" % (len(raw), len(out_bytes)))
    print("")
    print("Next: git add %s && git commit -m 'debrief: pull protocol counts across devices'" % TARGET)
    print("      git pull --rebase && git push")


if __name__ == "__main__":
    main()

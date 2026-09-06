#!/usr/bin/env python3
"""
forge_drilltab_fix_20260906.py

Fixes the blank Drill tab on all eight protocol pages that have one.

THE BUG: setMode() did `el.style.display = ''` to show the drill pane. Clearing
an inline style does not override a stylesheet rule, so `#drill{ display:none; }`
kept winning and the pane stayed hidden. Every Drill tab in the Forge OS has been
blank since it shipped - charisma since August 20.

THE FIX: one character-level change per file, `''` becomes `'block'`.

  Edits    : capital, charisma, getting-paid, longevity, mental-strength,
             second-nature, selfdefense, sleep  (all .html, hand-maintained)
  Writes   : nothing new
  New keys : none. No Cloudflare paste. NO workflow run.

Every file is checked against its own pre-image SHA first. If ANY file fails its
check, nothing at all is written - the run aborts before touching disk.

Run from inside the repo, on gh-pages:
    python3 forge_drilltab_fix_20260906.py
"""

import base64
import gzip
import hashlib
import json
import os
import shutil
import sys

OLD = "document.getElementById('drill').style.display = read ? 'none' : '';"
NEW = "document.getElementById('drill').style.display = read ? 'none' : 'block';"
SUFFIX = ".bak-drillfix-20260906"

TABLE_B64 = """
H4sIAP/QnWoC/02U22okRwyGX2XxdRxKKkmlyquEvdCpbIM9a+xJIIS8ezSTgPe6u6VP/6H/fgh7
f7na66/P17fXh9++/f5QJStkyMJxiLKmyk7OUUCVCxezDs4qdOwHp3YsO2vMoTEBhj388q2HFoGS
qPQrpgN1i4QKlJ46xWB4yljTEtfoHRs2zZpVdMgBHr7fhjzbx8vnm32hTefbHh+6ELcnEW7DkAnh
symMcPLkxWY0I0al1JI5kNJLR93QJFHEce0+gRGqCeyw0VZBsbRAGeEFfs7ysAFVdagkqj/YMe9o
T3W9vlyeHt/tJb/wktlmRsVwH9FIPE+W+mFPG3h4i5qws86eRlNmadiikDAynze8Zt9VmkGTButp
vbY5atkyUCzkJb6JxI62BXCStVrbEKs5Z97xXn9cnurPl+tfP7EtIaEkx6l98GqyAUSwMFtVOM7B
gr174o66rbK5FznTuDmFNzaK1X5DZ2G09Mpr2GbteKxRVmeMvne0h+NkiEP5RFcUN13gMM6d7a0u
HbfHz+tHXZ6uz1+ENrwDJ6QjdXMLEOkY5LOjN3Zrdzorwb12JkjsnQhAuVoe7zvu6hGCG8tuAZsS
2PRmB6bCDqVMDxobm1QZi/MocfZk8w6lwcE74WfFj0s+Xuz6x0d98bHhzNonV6hnDQBQy8PiQqPO
6ew4KWjoUjq2W892h5gMFp8zbnyt/+yIGKnx3vuAhaaPuafYEFhLJ4eTl++5+sLVlbqZcISAcOz/
+V47Vqcunz/RZfNHH9VYuFq/wGO4lRMQ2lTuFce7j2cP2sytXWlXJg9Z50zgrl6mrdW16ScislqY
5D4po7302VUC1xavcJ9CGmtQ7QWzNe9Iwn/Z+3ytev/i0tV38a2xcpZ2l7Tn9h+mE43c6Z6qU0l9
ngUy9FBKY1H4yjZz37kMckhM7p9KLY5t1gccqRkwMZRlqpWwdvmPoHd/vAe0L+ZL+sWH7//8Cx3g
AhroBAAA
"""


def die(m):
    print("ABORT: " + m)
    print("Nothing was written. All files are untouched.")
    sys.exit(1)


def main():
    table = json.loads(gzip.decompress(base64.b64decode("".join(TABLE_B64.split()))).decode("utf-8"))
    planned = []
    already = []

    for name in sorted(table):
        pre_sha, post_sha = table[name]
        if not os.path.exists(name):
            die(name + " not found. Run this from inside the repo working directory.")
        src = open(name, encoding="utf-8").read()
        cur = hashlib.sha256(src.encode("utf-8")).hexdigest()
        if cur == post_sha:
            already.append(name)
            continue
        if cur != pre_sha:
            die(name + " does not match its pre-image.\n"
                "       expected " + pre_sha + "\n"
                "       found    " + cur + "\n"
                "       It has changed since this installer was built. Rebuild, do not force.")
        if src.count(OLD) != 1:
            die(name + ": the target line matched " + str(src.count(OLD)) + " times, expected 1.")
        out = src.replace(OLD, NEW, 1)
        if hashlib.sha256(out.encode("utf-8")).hexdigest() != post_sha:
            die(name + ": post-image SHA does not match after the edit.")
        if out.count(NEW) != 1 or OLD in out:
            die(name + ": the edit did not apply cleanly.")
        planned.append((name, src, out, post_sha))
        print("  ok  " + name)

    for name in already:
        print("  --  " + name + " already fixed, skipping")

    if not planned:
        print("")
        print("Nothing to do - every file is already fixed.")
        return

    print("")
    print("All " + str(len(planned)) + " checks passed. Writing.")
    written = []
    for name, src, out, post_sha in planned:
        shutil.copy2(name, name + SUFFIX)
        open(name, "w", encoding="utf-8").write(out)
        if hashlib.sha256(open(name, encoding="utf-8").read().encode("utf-8")).hexdigest() != post_sha:
            shutil.copy2(name + SUFFIX, name)
            for w in written:
                shutil.copy2(w + SUFFIX, w)
            die("bytes wrong on disk for " + name + ". All files restored from backups.")
        written.append(name)

    print("")
    print("UPDATED   : " + ", ".join(written))
    print("BACKUPS   : each file plus " + SUFFIX)
    print("")
    print("Hand-maintained pages. Commit and push - NO workflow run needed.")


if __name__ == "__main__":
    main()

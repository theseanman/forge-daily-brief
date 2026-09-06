#!/usr/bin/env python3
"""
forge_mismatch_colour_20260905.py

Recolours the MISMATCH block for the brief's LIGHT theme. The first version used
#ff6b6b, a pale pink meant for dark backgrounds; the brief's body is an orange/
amber gradient with near-black text, so it was unreadable.

  Target      : forge_actions.py   (THE GENERATOR - needs a workflow run after push)
  Pre-image   : 382c62c2aaf43ab36d284fdfdfa80fe9acbcb8132c6b10db19ef6baa66de8678
  Post-image  : 0ab950db1c9a87a2119b644656f2a01ae8d186a7eccc6d9b2c688bb35401d00b
  New keys    : none
  Cloudflare  : nothing to do
  Behaviour   : unchanged - thresholds, wording and logic are untouched

Loud lines now use the same dark-red wash the sleep alert already uses
(rgba(200,60,60,...)) with near-black text, so red is carried by the chip rather
than by the letters.

Run from inside the repo, on gh-pages:
    python3 forge_mismatch_colour_20260905.py
"""

import ast
import base64
import gzip
import hashlib
import os
import shutil
import sys

TARGET = "forge_actions.py"
PRE_SHA = "382c62c2aaf43ab36d284fdfdfa80fe9acbcb8132c6b10db19ef6baa66de8678"
POST_SHA = "0ab950db1c9a87a2119b644656f2a01ae8d186a7eccc6d9b2c688bb35401d00b"
BACKUP = "forge_actions.py.bak-mmcolour-20260905"

PAIRS_B64 = """
H4sIAHDEnGoC/61VTXPaMBD9KzvkAKS2EYSvyE167CWnTm+lB9kSRhNb8sgihGby37uSTfgIIQkT
wIO98r7Vk95b/em0i+KXXrUDaM+XKrVSK/CRTs4SkQdgH20AuV7yLjw9zRSAEXZpFMza37l8gMqu
c3HT4rIqc7am81w8xpCxkvZJiXcl41yqjA7LRyAxzLWyYSX/CdofuOFcKhEuhMwWlvajUdy6nbXh
m6viPliiKpna1CikCleS2wW99sm6ZKm0a0qiCSIJa4UJKxfDeiQiQ1E0eOCp4D8C9hziqSqOAe3H
sK22mfeqnqdH7LgVgR+YPCUEIxTvxu6uuwV20DGkOtfmMOliPh8n46RJlGohjLRHkjcUD9L7TSKJ
pj7JvdtQxe06TtSFcMMwEs/U8/MnNrx3CXeOOdiFKASFRPM1yApwzbRhKhM9ViTCQGYYl0JZHOBg
BU4EX1KCmTDJWXofNdTuHAscSZkxUnBI1sCAM3MfGnxKF7IMMOsBAXGkZLnwWBFc9hzAAzOwMqyE
Gz/HGtOtyVsKZLnMVCitKCqasEo4yW11OUFdXrvXCmYyqejVx3S6rx9IkF5m9FJxarKEdQaEBGP/
I1F/3I1xyQxHdeZibn2JSueSw0VCrvD7MuzWb1nREVactWt4ejaz4bnM4jdN7gXmF98p7FNePW7P
xhy4p50wLJZW8O6XWXYX2gkoTIwj2X1t5q3lTrn6HI91A+i0WZo6U+BMKjRdq5ZwE7xBr6zv6qKb
puDKtmsZjUbB5iLRcNSt98bl14rZz3/J6ZOJv+qcN+BQlztwmef/HhyZ1HAWbY/UDVLARTlNajof
kAHxabv7/BEqOy7aI4KBwFtr+iEKOzDHCfhtqixDJ7kAdsZ93R96pn52Y1RadGF6aKPhaPd0mo42
JgwTba0uqPNl6/an1hw73apy3ZC7RootpIq+qP4r/eeN/D8zFb8yc63RuyenRfbP4/FLFatLX+Kw
z7ij/veiPgU4aJWvoRKier/IkY5xbq3u3/98nF9J/ggAAA==
"""

PALE = ["#ff6b6b", "255,107,107", "255,255,255"]


def die(msg):
    print("ABORT: " + msg)
    print("Nothing was written. " + TARGET + " is untouched.")
    sys.exit(1)


def main():
    if not os.path.exists(TARGET):
        die(TARGET + " not found. Run this from inside the repo working directory.")

    src = open(TARGET, encoding="utf-8").read()
    pre = hashlib.sha256(src.encode("utf-8")).hexdigest()
    print("pre-image  : " + pre)

    if pre == POST_SHA:
        die("this installer has already been applied to " + TARGET + ".")
    if pre != PRE_SHA:
        die("pre-image SHA does not match. Expected " + PRE_SHA + ".\n"
            "       Rebuild against the current file - do not force it.")
    if "mmBlock" not in src:
        die("the MISMATCH block is not present. Run the card installer first.")

    pairs = ast.literal_eval(
        gzip.decompress(base64.b64decode("".join(PAIRS_B64.split()))).decode("utf-8"))

    out = src
    for name, old, new in pairs:
        if out.count(old) != 1:
            die("anchor '" + name + "' matched " + str(out.count(old)) + " times, expected 1.")
        out = out.replace(old, new, 1)
        print("  ok  recoloured " + name)

    i = out.index("/* ---------- mismatch")
    j = out.index("function paintPractice()")
    block = out[i:j]

    checks = [
        ("no pale colours left in the block", not any(p in block for p in PALE)),
        ("loud chip present", "rgba(200,60,60,0.16)" in block and "#b03030" in block),
        ("theme text variables used", "var(--text-bright)" in block and "var(--muted)" in block),
        ("statement unchanged", block.count(
            "Good news is dangerous. Bad news is the only thing that saves you.") == 1),
        ("limits footer unchanged", "a clean reading is not an all-clear" in block),
        ("thresholds unchanged", "MM_MUSHIN_DAYS = 3" in block
            and "MM_PROJ_WEEKS  = 2" in block and "MM_REPS_DAYS   = 7" in block),
        ("mmBlock still defined and called", out.count("mmBlock") == 2),
        ("paintPractice survives", out.count("function paintPractice() {{") == 1),
        ("brace balance unchanged", out.count("{") - out.count("}") == src.count("{") - src.count("}")),
    ]
    for name, passed in checks:
        if not passed:
            die("post-check failed: " + name)
        print("  ok  " + name)

    try:
        ast.parse(out)
    except SyntaxError as e:
        die("patched file is not valid Python: " + str(e))
    print("  ok  ast.parse")

    post = hashlib.sha256(out.encode("utf-8")).hexdigest()
    if post != POST_SHA:
        die("post-image SHA is " + post + ", expected " + POST_SHA + ".")
    print("  ok  post-image SHA matches")

    shutil.copy2(TARGET, BACKUP)
    open(TARGET, "w", encoding="utf-8").write(out)
    check = hashlib.sha256(open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest()
    if check != POST_SHA:
        shutil.copy2(BACKUP, TARGET)
        die("bytes on disk do not match after write. Original restored from " + BACKUP + ".")

    print("")
    print("WRITTEN   : " + TARGET)
    print("BACKUP    : " + BACKUP)
    print("post-image: " + post)
    print("")
    print("This is the GENERATOR. Commit, push, then run the workflow.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
forge_fourmoments_20260906.py

Adds The Three Moments Protocol to the Forge OS.

  Writes   : four-moments.html   (NEW hand-maintained page, live on push, NO workflow)
  Edits    : protocols.html      (one card appended to Available protocols)
  New keys : forge-img-four-moments  -- LOCAL ONLY, device-bound, never synced.
             NOTHING to add to the Cloudflare allowlist for this build.

  four-moments.html SHA : fdef081fb640387c85d8ceaeb16f6363b8599e1e9ead4168806d6598cc3bbcb1
  protocols.html  pre   : 5723f0c107a2aa086d6c603254a72ed9ae6973c07c3887a3876fd8285abac9a2
  protocols.html  post  : 96b682428841aad77b74ce86db263210d5580924aaeb32311cc10f1acd658f64

Sort mode is the default tab. It is a boundary tool: run it before entering a
situation, not once you are inside one. Every use decides a situation for good,
so the diagnostic is designed to retire itself.

Run from inside the repo, on gh-pages:
    python3 forge_fourmoments_20260906.py
"""

import base64
import gzip
import hashlib
import os
import shutil
import sys

PAGE = "four-moments.html"
PROTO = "protocols.html"
PAGE_SHA = "fdef081fb640387c85d8ceaeb16f6363b8599e1e9ead4168806d6598cc3bbcb1"
PROTO_PRE = "5723f0c107a2aa086d6c603254a72ed9ae6973c07c3887a3876fd8285abac9a2"
PROTO_POST = "96b682428841aad77b74ce86db263210d5580924aaeb32311cc10f1acd658f64"
BACKUP = "protocols.html.bak-fourmoments-20260906"

PAGE_B64 = """
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
j2sAAA==
"""
ANCHOR_B64 = """
H4sIANnBnWoC/31Pu07EQAzs+Qpri6ty3AckbEWN0IFEbWLf7Ur7iLzeIPh6nNMVpMHV2B7PjCeK
K8wJW3tyy7FgZuffA8Mbz7UQvKB2YXiVqnWuaToZ3T/AvabdMXGbnf8I31Cqhliu8GkimRvEoj1q
XBkOmbCFEdQsLsL8w8MNc7wGPUq3o4RELAOg2W8r6YkNoAKvmDpqrAUCLguXBnhRlhstm1PRAQqv
NqEuW4Coj/9GztVCO39mJIsWiaqO8Cwx7T/dNzsFFKlfzh/EwPiHN51wA/fJL/lD1tlmAQAA
"""
CARD_B64 = """
H4sIAMPUnWoC/31QS07DMBDd9xRPXnTVJgdI6hsgIajEemo7sYXtQfYElNtjWlTRCpjV0/j9PAAw
EkykWg/qrbCw4ajgi5sOqusnXso+cXJZauclRaU3OM9ow/tVtxe/pJPSY9+2vzNObNer+P4xU3JK
H73DsSU7PFwS8fhd6Mb3XmxdNUq/+GA8XkO24AniQ254BuHSHoZirJi4YJssVT80jsNM4nZY2y9R
gywkgXMFxeLIrqhcxNkdqJkSbKA5c5VgzjZfcs6uNkACKg6Zpfu3aeLWVennZttaBGtZBjy1qNu7
/X1EKoU/lN6WBoYfvLEnvfkEGrUPYMwBAAA=
"""


def unpack(b):
    return gzip.decompress(base64.b64decode("".join(b.split()))).decode("utf-8")


def die(m):
    print("ABORT: " + m)
    print("Nothing was written.")
    sys.exit(1)


def main():
    force = "--force" in sys.argv
    if not os.path.exists(PROTO):
        die(PROTO + " not found. Run this from inside the repo working directory.")
    if os.path.exists(PAGE) and not force:
        cur = hashlib.sha256(open(PAGE, encoding="utf-8").read().encode("utf-8")).hexdigest()
        if cur == PAGE_SHA:
            die(PAGE + " already exists and is identical. Nothing to do.")
        die(PAGE + " already exists and differs. Re-run with --force to overwrite.")

    page = unpack(PAGE_B64)
    anchor = unpack(ANCHOR_B64)
    card = unpack(CARD_B64)

    if hashlib.sha256(page.encode("utf-8")).hexdigest() != PAGE_SHA:
        die("carried page failed its integrity check - truncated or corrupted.")
    print("  ok  page payload intact")

    src = open(PROTO, encoding="utf-8").read()
    pre = hashlib.sha256(src.encode("utf-8")).hexdigest()
    print("protocols.html pre-image : " + pre)
    if pre == PROTO_POST:
        die("the Four Moments card is already in " + PROTO + ".")
    if pre != PROTO_PRE:
        die("protocols.html does not match its pre-image. Expected " + PROTO_PRE + ".\n"
            "       Rebuild against the current file - do not force it.")
    if "four-moments.html" in src:
        die("a four-moments link is already present in " + PROTO + ".")
    if src.count(anchor) != 1:
        die("anchor matched " + str(src.count(anchor)) + " times, expected 1.")
    print("  ok  anchor unique")

    out = src.replace(anchor, anchor.replace("</a>\n  </div>\n", "</a>\n" + card + "  </div>\n"), 1)

    checks = [
        ("card count 13 -> 14",
            src.count('<a class="protocol') == 13 and out.count('<a class="protocol') == 14),
        ("new card sits after second-nature",
            out.index("four-moments.html") > out.index("second-nature.html")),
        ("every existing protocol link survives",
            all(h in out for h in ["morning.html", "evening.html", "getting-paid.html",
                                   "charisma.html", "posture-reset.html", "capital.html",
                                   "fantasy.html", "longevity.html", "sleep.html",
                                   "selfdefense.html", "resilience.html",
                                   "mental-strength.html", "second-nature.html"])),
        ("div balance unchanged",
            out.count("<div") - out.count("</div>") == src.count("<div") - src.count("</div>")),
        ("anchor tag balance", out.count("<a class=") == out.count("</a>")),
        ("page carries no sync url", "forge-sync" not in page),
        ("sort mode is the default", "setMode('sort');" in page),
        ("two diagrams inline", page.count("<svg") == 2),
        ("tests wired into sort", "function startTests()" in page and "DISPOSAL" in page),
        ("three moments not four", "one of three kinds" in page),
        ("drill-tab display bug not present", "style.display = sort ? 'block'" in page),
        ("boundary caveat present", "at the boundary" in page),
    ]
    for name, passed in checks:
        if not passed:
            die("post-check failed: " + name)
        print("  ok  " + name)

    post = hashlib.sha256(out.encode("utf-8")).hexdigest()
    if post != PROTO_POST:
        die("protocols.html post-image is " + post + ", expected " + PROTO_POST + ".")
    print("  ok  protocols.html post-image SHA matches")

    shutil.copy2(PROTO, BACKUP)
    open(PROTO, "w", encoding="utf-8").write(out)
    if hashlib.sha256(open(PROTO, encoding="utf-8").read().encode("utf-8")).hexdigest() != PROTO_POST:
        shutil.copy2(BACKUP, PROTO)
        die("protocols.html bytes wrong after write. Original restored from " + BACKUP + ".")

    open(PAGE, "w", encoding="utf-8").write(page)
    if hashlib.sha256(open(PAGE, encoding="utf-8").read().encode("utf-8")).hexdigest() != PAGE_SHA:
        die(PAGE + " bytes wrong after write. Restore " + PROTO + " from " + BACKUP + ".")
    print("  ok  " + PAGE + " written and verified")

    print("")
    print("WRITTEN   : " + PAGE + " (new, " + str(len(page)) + " chars)")
    print("UPDATED   : " + PROTO)
    print("BACKUP    : " + BACKUP)
    print("")
    print("Both hand-maintained. Commit and push - NO workflow run, NO Cloudflare paste.")


if __name__ == "__main__":
    main()

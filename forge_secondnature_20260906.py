#!/usr/bin/env python3
"""
forge_secondnature_20260906.py

Adds The Second Nature Protocol to the Forge OS.

  Writes   : second-nature.html   (NEW hand-maintained page, live on push, NO workflow)
  Edits    : protocols.html       (one card block appended to Available protocols)
  New keys : forge-img-second-nature, forge-second-nature-drill  (both LOCAL-ONLY,
             never synced, nothing to add to the Cloudflare allowlist)

  second-nature.html SHA : 5a23de9fd7c8bde01118adf56b640effadab4818c8784fa9c561fd454a175ff0
  protocols.html  pre    : 7dffff3777d22dfa27f456c9329abf003d827a80d27cb01f0349a63e79413ba8
  protocols.html  post   : 5723f0c107a2aa086d6c603254a72ed9ae6973c07c3887a3876fd8285abac9a2

Built on the charisma.html template - the photo slot, the streak logic and the
reveal mechanic are byte-identical to it apart from the storage keys and one
hint string ("Name it" rather than "Say it aloud", because this drill is
recognition rather than recall).

Aborts without touching anything if protocols.html does not match its pre-image,
if the anchor is missing or ambiguous, or if any post-check fails. Refuses to
overwrite an existing second-nature.html unless run with --force.

Run from inside the repo, on gh-pages:
    python3 forge_secondnature_20260906.py
"""

import base64
import gzip
import hashlib
import os
import shutil
import sys

PAGE = "second-nature.html"
PROTO = "protocols.html"
PAGE_SHA = "5a23de9fd7c8bde01118adf56b640effadab4818c8784fa9c561fd454a175ff0"
PROTO_PRE = "7dffff3777d22dfa27f456c9329abf003d827a80d27cb01f0349a63e79413ba8"
PROTO_POST = "5723f0c107a2aa086d6c603254a72ed9ae6973c07c3887a3876fd8285abac9a2"
BACKUP = "protocols.html.bak-secondnature-20260906"

PAGE_B64 = """
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
bcvbpHV3AAA=
"""
ANCHOR_B64 = """
H4sIAHXPnGoC/31Pu27DMAzc+xWEh0xp8wF2NXUtULQFMhMSYamQRYeka+TvwxgZ6qWc7gjeg0Mq
vxArqr5283PDibrwnQneqRlW+DKhNlqGD2HjyHU4uSA8wWOGnTyRxi6c8xWuvMBlKQbYEmRewRj8
yqByG0ngMCXU3IN5VBRWLW08bmzOqHTcdHc6lUpq3Bzh7Bs0MKpVt4Q1l5hBy9gUUAh+Fk/YTIQj
qYIsrbnzy7+tJ/beXfgkTN6rpMTWw5uUun92T3YOKMJrFw7ioP9zN5zwDh6bGyNIG0drAQAA
"""
CARD_B64 = """
H4sIADLVnGoC/31Qu27DMAzc8xWEhkx2/AF2NHUuirRAZ9qiIwF6GBTlIv36KkYRNEERTgfyjnck
AMCAMHnM+agWTpKm5BVYpvmoDl2mKUXTRpTCdLASvNI72Gowbr0JW7EljEoPXe3+zxiTudzEj8OI
gZT+sATvmyO8bo7w9pvobu+j2FCelP60F4hJrItnGOuSQBlclOLErQT7YDDbHqRazEz0Tc2GyZ2t
tFyqyKMxxA1gtb+OuHiqAAVoRV9QXIpgcVkoZsBZiDdaqE5RGoi01o4pfA3g5PA0ckg1tNInQlOj
OWOS9PDCzt9f+uSdyJy+lN5zBf0f3tCh3v0A5b0nydcBAAA=
"""


def unpack(b):
    return gzip.decompress(base64.b64decode("".join(b.split()))).decode("utf-8")


def die(msg):
    print("ABORT: " + msg)
    print("Nothing was written.")
    sys.exit(1)


def main():
    force = "--force" in sys.argv

    if not os.path.exists(PROTO):
        die(PROTO + " not found. Run this from inside the repo working directory.")
    if os.path.exists(PAGE) and not force:
        existing = hashlib.sha256(open(PAGE, encoding="utf-8").read().encode("utf-8")).hexdigest()
        if existing == PAGE_SHA:
            die(PAGE + " already exists and is identical. Nothing to do.")
        die(PAGE + " already exists and differs. Re-run with --force to overwrite it.")

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
        die("the Second Nature card is already in " + PROTO + ".")
    if pre != PROTO_PRE:
        die("protocols.html does not match its pre-image. Expected " + PROTO_PRE + ".\n"
            "       It has changed since this installer was built - rebuild, do not force it.")
    if "second-nature.html" in src:
        die("a second-nature link is already present in " + PROTO + ".")
    if src.count(anchor) != 1:
        die("anchor matched " + str(src.count(anchor)) + " times in " + PROTO + ", expected 1.")
    print("  ok  anchor unique")

    out = src.replace(anchor, anchor.replace("</a>\n  </div>\n", "</a>\n" + card + "  </div>\n"), 1)

    checks = [
        ("card count went 12 -> 13",
            src.count('<a class="protocol') == 12 and out.count('<a class="protocol') == 13),
        ("new card sits after mental-strength",
            out.index("second-nature.html") > out.index("mental-strength.html")),
        ("every existing protocol link survives",
            all(h in out for h in ["morning.html", "evening.html", "getting-paid.html",
                                   "charisma.html", "posture-reset.html", "capital.html",
                                   "fantasy.html", "longevity.html", "sleep.html",
                                   "selfdefense.html", "resilience.html", "mental-strength.html"])),
        ("div balance unchanged by the edit",
            out.count("<div") - out.count("</div>") == src.count("<div") - src.count("</div>")),
        ("anchor link balance", out.count("<a class=") == out.count("</a>")),
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
        die(PAGE + " bytes wrong after write. protocols.html was already updated - "
                   "restore it from " + BACKUP + " before retrying.")
    print("  ok  " + PAGE + " written and verified")

    print("")
    print("WRITTEN   : " + PAGE + " (new, " + str(len(page)) + " chars)")
    print("UPDATED   : " + PROTO)
    print("BACKUP    : " + BACKUP)
    print("")
    print("Both are hand-maintained pages. Commit and push - NO workflow run needed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
forge_checklist_page_20260906.py

Writes checklist.html - the daily weighted checklist tracker.

  Writes   : checklist.html  (NEW hand-maintained page, live on push, NO workflow)
  Edits    : nothing
  New key  : forge-checklist  -- SYNCED, so the forge-sync Worker allowlist must
             already contain it BEFORE this page is deployed.
  SHA      : 2d0c5d87a5b860fee9af6012d4bbd59b37f857b098998e009a10ff1155f29c6d

Storage shape: {date: {itemId: true}}, 120-day prune, union merge on pull so a
stale cloud copy can never un-tick anything. Item ids are hand-assigned slugs,
never positions, so re-tiering or re-ordering the list later leaves history intact.
Only ticks are stored - the score is computed at render.

Run from inside the repo, on gh-pages:
    python3 forge_checklist_page_20260906.py
"""

import base64
import gzip
import hashlib
import os
import sys

TARGET = "checklist.html"
SHA = "2d0c5d87a5b860fee9af6012d4bbd59b37f857b098998e009a10ff1155f29c6d"
B64 = """
H4sIAATdnGoC/507bXObuNbf8ytUdzbYNRDbea0d0um26TZ7N22mSe/O3mzmjgyyYY3Bj5Dt+Eny
3+85kgCB7TS7nUkDh6Pz/iZBTl99/Prh5o+rcxKKaXy2c4q/SEyTsddgSQMBjAbwa8oEJX5IecaE
15iLkXPSyMEJnTKvsYjYcpZy0SB+mgiWANoyCkToBWwR+cyRNzaJkkhENHYyn8bM69okX+eMIuH5
6YJxJCwiEbOzjzSKV+RDyPxJHGXidE+Bd04zscLfhPR5mooHuCDEcYZjJ2Bs1n/dOer6B52BAk2j
ACDB/uFxDyHU90G4/usD+jZgJyXECaP+6+PRcDQaDTS9KJn0XzM6OgCQunWCaNrn4yFt9vYP7N4B
/Bwe2u7xSStH+L95xMQGlMNWTnWcxiDQ6DA4PmK4akYTFqsVxwd29/DY7u33bLfbkTTjKGHqYbfX
s7vHh4pcr1fQAw8tVibBaRoUmkgK4xD0fTsangQnuOgJft48kCnl4yjpg5lmNAiiZIyXw/TeyaL/
x7thygPGHYAAlSUbTiLhCDoDO41DSdPx0zjlfcFpks0oBxsOJG2MIXuYBivgESUgnxSg2+n8NCAj
iA1nRKfg175DZ7OYOdkqE2xq/wyaTi6pfy1vPwGe3bhm45SR7xcN+1s6TEVqf2bxgonIp/Z7DlFk
Z8DayRiPtM+G1J+MeTpPgj6nAcbZGH+DaE0Wx9EsY4QKctj5iTgnP9nkdZcdUnpCOnC9oLyZx0uL
HPRMEEZVi6AGrTofhwpB/XCKMTWK7lkwIMosajHo1FJWcZecztDq9yoV+kcnnRmYNncDoXORlr7o
wUPSPYL/IFH85gHetglLFs2MjpgD5qZAHLIRHCREOm3lbEQ6G1L+QIIom8V01R/FDLhQ8FjiRGDZ
rI/RzviA/DXPRDRaOTpf++BEyNMhE0vGkgEZ0xk4rRRRM+p3ewhDXtRFOzzUFVY5APIIdi/Adn7K
qYjSpJ+kCdMhADHGNKWYCRDHQe6ouNs9YlO9VobWKOXT/nw2Y9ynWb5+qYLquNPRamerxH8waXc3
0n6e9DZFNrIMuya/3gHyMxH3EVF7FxQlHVIYzg2oYHFF3J57iE/rEkC9aa054GiTap0D1O1pB8jv
vSEZGJ0RWVrImz1pIIQ8mBmiuEicFmY+pnsfzEayNI4CHf1Yf4qnDibTPNMS5KGq7moynhS6ilTQ
+Ll4HILtkc3LIrJXJUzcYTQ2LXnQqTuih45ABkUpqhJIRxVPHGzyw6ZIOCqCTxPysVFlFWL72526
RkrGpTRMnyNUE4ceyyCftewySswyJzvNoWoLsjV0e2v+klJgax3F6bIfRkGA5tSxiTJCcCq9S47k
DFy2KPiq8m0wRoNSXtbXt52AjW2lpOqorcod9A2sUar2obaYgJGsCxJG3P1M8x/yyabcqLjQPS6R
icvTZT3CXlzd8jCWZqgRJbAqgbrOM+h2YRQHD1ucWV01fKh496RToRsGFe06WrtaPvdeXqq0uVVr
WmOcu1nVoH1DZQd6hTaCjhcJ2FwBTPmrFjHWqgpvki8EyO/yCoVhNMt0cRqHLysQ6LW3RteUXbJD
ymIzhjhKHn7YY3ovbzGl85D2cr3HvLhprFXsE1WxkbSa4qTsJj0JReMjCsx1awgAaxU05FS2hiKh
OQ100BqGKbV0j4t2f84jCHEyQbkwq/I/6y1qoFIxFLOR6B+8qAX1Ki0Ig1tVsGofkpHhz3kGys7S
SA0+T7mKrrTvg8nd2WJ+iQ7W3o5suEIiS7tvRzfcItHRM5uwNxT4E5MPJOX9gy6rPWkUXSLVDXoK
hksYPnpGnmsjHpcgOaJscc7fHyVzeL0TriWW0hE2bL2jg1GlVHSLnJbmSROl6FqM5cUvV21TYazR
SSC2U8xCseq7h4frg6rsNCIENuOwYmpcaY4KqnSvZ3qlUx1USGTcf3kNMezRe27oK6jPRJbv7FQy
qV1FvR5u8cO6AHkpl7TKMoupX60huKttrTOS2Ekq2HpN3sayajx0T97BsNj3jC49wr2/OTZtCLvu
P9livMQdBxs9/7RzuqcPJ0739NkJboXhF0xTxI9plnkN3Ao2zrDSmlC1c2ucyZw7pSTkbOQ13L1G
joCx3zjbjSkHHX/mERud7lGNjoNKjod7oQaJAn11tpsMs9kABAMcRD/dA66KfdhdP2QBWE0yuV1R
FNXlmUHCwJN7jFyBimYwH2u4enJWERhGeEUdwrdx1tGSVpVKR42zPQ1CVNhIV7Flec/0nZavZJiT
UTN646wklEMKQumoymYNQQJYYPAwLw1mcpAGXghCYtK9CnfLChiwGpvEDoPG2c8rokJtXTlJfOWI
iBUMthOZ8VSkEOJbyUiECp3isuZ3XKAGuW0hgbmvfDtPZHgEjgSV1E1szOjG2aeUjxn5ek12p7BV
SQXmGUAcv4xRuTbneJr5PJqJsx0YK53aPyIb1RoYtYqCjFDYJYcUj3GyDCoIC0gWz8cATwIyhaZG
EgbbJjz5TMasT0JgnvIViTIyYSvAhnYiQmgrSO8bkw6ACkNiijsowMLDGuIAGqSYiCCMJEckwgIb
l+qdOqD66XQ2F0AzZJy5OBhDASIXN+eX18Qjt8DhAUTuW+Cdv5gvnGGc+hPLJiTpW1cKBiymjBQP
yn/QdPpWbtbykehbcsSxyJNd0A9gEHGWIUtyPKD/FaZGQbMJ4XNQOAWjZsTEk/SvoYGC2b5QMedM
Lt5If8LpoiId0P8XwEjGwAdpUpXckP+axSPnIxuxJFPkN9OHih4l4ISCDtC/0bBtPCT931Lw8QKG
guLpRvrpCHbRNChJIH1wpIbbZMhG6NIhK3Ek/fMFq8hVo18w0AeLh6YCn6IFw9NUCJAMC5TCKUlt
dwCMpXA541Ff8DkzFZnRecYczqgfKkIYSAjLNTAeVfjcsOksrcCf5QPDQhLUHQIGG3LYkUPCCWhr
kOoBzWDYypGh1MVxHlmIfY1oAHiWFeTkEDbgzgjKSahz41zBiIRhwtIZpFCpmeTwIaQ8yqa0khvb
+cBsyLIQRh4jRz7wFGILJKdk7fE/dVE6F1kUMKdz3D2R2JiLCkaGK9I57mt43UWXKV+PNeRjUl/S
CZLudAwtfgcYnpED6RK+lokxY7NNAWBSlxuczOnt53SA+m8SRkAt0tvfwGB7ntSpQ7UOjRRRHlj5
ceQTfATrbXKIGWOgvNwysOMRPBrORV4rdA004YT6wiwlkvovMGnivHxFo6CoUTn1gjx0lrAiGZC/
lDCbdDs1qX9YwqWhK+KHKWRxLTxR/AIui7lN8DAAWxvs0rcV8c30+cKRR0AG/c/f/l1UPigcIqwa
+Rnjr9NfpD6NIYnTlBeh82+EEQmzSW/dRtvTeJ0+7LVl3au714RD9Zutyf9C+nweM6d3EJoVr3fg
gPk5wWfQ4qu1oaBPZxGMytvsY+TWgklyhgPeE4Sij8FASQqVlMlhJEfZXn/w6KEi/zyh8wAGp3r8
FHB8xwtzUUbLDPgh+Z27gZxofj+/+OXzDYw0eLaMry4PbYKvLPdtol5VdlH8hPU75EmtuLk4//bl
/eW5scb6LPumWglhBTt/GLmsnIQqNJYmZH3Xo6eVU/zl29fvV/lYdaubsJ0TtQ71ZsK6s+VzWaAN
LtZ+DUG5yM7ZWl31PH8sLWCXYtiWD3u4CEdAGIbBmPMEjX2HJpLy/ev8D8+qDb2WEv36jy8f/vv9
22+eFQoxy/p7ewoPt3ruKs0YTTiLAneZ8gl4yA3YQq+8+vb9y/l/P77/49rr9jrAadO4jKMphRqz
9gDm0dE8UamxmgbNoPUAKQJ+Tkjgjpn4NI/jPxhsmVtty7HaTasD/8knl7BJDgHcbbXcDAo0azo9
A0nifAS7Ns3nuJUu+Ik0oKtmyRD5J2xJ9KoKLuRv8D6OARtML/jqAc+zyML79frrF3eGHzA0Yywl
10pRZH4BW4QmmLz1+Gg9PFn61Av+aXbNxe6uWM0YzF0Lz/OsdIjDtrW7++o953TlRpn83Vy0Wu8W
/YcnkMenwg+brBRZQncMOZccEgkFTaWkKKQ/F15FNfzPTdJls+WUzntzcnTQwX+tlo2d1APSO3ju
z5tIZEKihABNEo2aqRvS7Osyge3BjHGxak5aZHeXTM48YNXCxbeTOy+F/9SJijRXxTpZaR2bSBNi
A0zG0WjVhOXS9oWuSEKrC88GO3UPnifAoFmoS+PYK7xlE+YB4Fa7+m5Q0mqywvzsOfMzMD9D8wPj
zbENKdKHIoYCTRkkjY2zGuzKcPulNnowVGNThNkK92Z+nM6D51MBDHQNZJvCXlKetFS0sdgLUn+O
HwVgfJ3HDC9/Xl0ETQuFgBADHBcPoD7oj2WEhMijI1ceP3lI7531ejTyu51jq29ZlTCXWlwkIlXR
bCtZy1CSG9bAG9E4Y2Z4BDI+SmSCcfJK3teDJZi0WvJjHth2MJUTkrTvSfTbAMNGrvYfH7WDfP9V
6aHHx6qDfH+NIC6XCiC1FtHRhzcY1oUaOBerEC01iYTUxNdqaEX8uhaRWGMqUX3/NhJ3EE9y5oas
KDgj/JWCtx6qYC3IJrGe9Jc1Omg1SiUJZvO8LuVRI6MB0unPea/TO1KVZ8QwnfIy37b2rDZLfOg9
379dfEhh55Xg61YsVy3J2IVITZo5kyZXqf+KuylkOx5iLwkWlHPOwXAcj27FPIMA1IJy968MlmEi
b6RnhooRLKXH8e45p8v1IFRFZ+h2hQi5BTdUBcNfZcADRh7uQLaoowCWJBPo0s1WSXSdr/KX1lZV
r0JdU1Dc0UeJnIIxFtBCNX9m4ZZy9vccaRNl3ykTIc4zV99vgCkeH0MH7z9Yukg4N2ByqAT43VTk
y9lrD51nPdkED5n7tQKNFsGobG0IkVxJDJN3uWlwVhPyFQuMeHMcf1UYDV5irfrSis021mPlq+fr
q0jH45g1o2Bb24DSqVoGmhzDU3aRuyI+1e0zAaoQoEioC91OgZK6v42CvEq0SMBiJhgpn2DVzkyA
qglAYGtcqqipBFL+MFeReWa/HGho4JUzTwGjq8y7ta6hb9GVnFH1xc2cZerqdxYk+fVNOOf68hOP
1MU1Dut4eZcTnaYJEv2VJnPKJS4bcn15STmenFjvZzyK5T1Cf53LAffXeYx37+fjOe4NYTswg+Fh
yGCbYn31RaquvqSLHPiR+epS8t7aM+VLB6tlNkyY3VH3Wz094sjQhqCz2ij8rTl3ApxUpszBjtYz
TDOxvVGrc20LQiz0oPkaPXTsdQZkfKo2EW7MkrEIAdBu6zKJOHgS7CmM2/HdbeeubKBQkTNPnuu6
oygW4Pgin+7LgfHeFRh2kXxh3Sq7Ja7WPOt9LWx7lnmaPg7JGKZspNG2GtVXLknjzGqX8nXBSvmr
ExNtWUXrGWjy8N0aVHsyWCY6NUQcRIVVlPKR8PDxbXSHxw8eg67qlhmW1/u6JvLlptakmcJYBGtx
JIJtRAMu8dhngq+ZZK3407Lakmrb+tNqgQL5ON+GnwrZ4T2qJwnuvu7CSL0/0FS1dusr5YTmNeRr
9e5AfuCaf9JU41TjlUwlLxAMMuedVX1hJ/DF0O7rt8f7+/l7OqIkAfxkozg18rD9RvqADldb5N+m
kyYhX6eBiGqDfovGvnvXtNpW24S0+pY+q91oJ6sSF/lQhJnmRknC+Oeby9+8cKA/ApIvBvVHQBgd
IILXsfEj2St1pd694dVwdYMp9YC9bnWFb6jkNaAWcFymH1R2RBCUk1OVcDoqJ5VcvVfZCNsgmyw9
rSzkXx6i92sRqgRse8viFoWQa7ymeff42Gm1SywpHjwAHylEE2Di4uYtKRJHWaHdztNjZvAm2jKa
uXFj0iO50Qrm1XsTN3fa1soI7KvF2APIswVcvaytLVJGfHadUry2TgF/xG/j0koQPEdgSDksVdsx
9WcMTSXuu0sqQle+fWmCSnsK+gaKR6sPJrR+sor2Iuptoyf7Rm+tcfSqnaPsG72ycWDpbwqOWx4d
X5v2UrAWBh153FSpurip/QI/L207+swOdkW16MdhsjSfMbP/feobaIla2YdOodvWWX52lnefIVSq
XCto8DDoWW0tBlalYbU/Pakx7eHHfKx2ftp4K7jR7ZBfnlzwQOaLRfZw4NDprtHrnH+UTPq1PURb
WR9FEUP4tzWZ91VOru6ErbKiaEB0plyUVqb2sLRzUVmGd05xTe/I4yOhrtzRMtyBUM6aw1Y+X8gC
XIvZKYTs9FRKkftqWonWZOrJp7fTMlALjskUA6dTD9TZc+ZPpmtGL4hVrV6A18z+I4PLDxwqFp9J
i29dU/l2wVxIPKlRcbSrPzfAl/z6iFd+ShDDZCJPe9XXBOq81yVXnGWwJZSv/3H7lKW4A8R3iCIl
Q/1tQECwvUJnzV+RipAKXLHE33hM9fXq5uLy4j/nYJiLy8vzb9fnJIMdokQCR7pETxb4/RJ+gYAf
ROKf6+ArxxS2KSvX2rpHG6Yg16YdWrGh2VHHGgP88kl/hwHuUN887ak/K/sfkt4RwGc2AAA=
"""


def die(m):
    print("ABORT: " + m)
    print("Nothing was written.")
    sys.exit(1)


def main():
    force = "--force" in sys.argv
    if os.path.exists(TARGET) and not force:
        cur = hashlib.sha256(open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest()
        if cur == SHA:
            die(TARGET + " already exists and is identical. Nothing to do.")
        die(TARGET + " already exists and differs. Re-run with --force to overwrite.")

    page = gzip.decompress(base64.b64decode("".join(B64.split()))).decode("utf-8")
    if hashlib.sha256(page.encode("utf-8")).hexdigest() != SHA:
        die("carried page failed its integrity check - truncated or corrupted.")
    print("  ok  payload intact")

    for marker in ["forge-checklist", "unionInto", "id:'live-hour'", "PRUNE_DAYS"]:
        if marker not in page:
            die("payload missing expected marker: " + marker)
    print("  ok  markers present")

    open(TARGET, "w", encoding="utf-8").write(page)
    if hashlib.sha256(open(TARGET, encoding="utf-8").read().encode("utf-8")).hexdigest() != SHA:
        die("bytes on disk do not match after write.")
    print("  ok  written and verified")
    print("")
    print("WRITTEN   : " + TARGET + " (" + str(len(page)) + " chars)")
    print("")
    print("Hand-maintained page. Commit and push - NO workflow run needed.")
    print("The forge-sync Worker must already accept 'forge-checklist' or nothing backs up.")


if __name__ == "__main__":
    main()
